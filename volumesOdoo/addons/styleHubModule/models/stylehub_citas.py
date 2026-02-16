# -*- coding: utf-8 -*-
from odoo import models, fields, api # type: ignore
from datetime import timedelta
from odoo.exceptions import ValidationError # type: ignore
import pytz # type: ignore

class StylehubCita(models.Model):
    _name = "stylehub.cita"
    _description = "Cita de Peluquería"
    _order = "fecha_inicio desc"
    _rec_name = "name"

    # CAMPOS DEL MODELO
    
    # Campo autogenerado para mostrar como título de la cita
    name = fields.Char(
        string="Referencia", 
        compute="_compute_name", 
        store=True, 
        readonly=True
    )
    
    cliente_id = fields.Many2one('res.partner', string="Cliente", required=True)
    estilista_id = fields.Many2one('stylehub.estilista', string="Estilista", required=True)
    
    fecha_inicio = fields.Datetime(string="Fecha Inicio", default=fields.Datetime.now, required=True)
    
    # Se calcula sumando la duración de los servicios a la fecha de inicio
    fecha_fin = fields.Datetime(
        string="Fecha Fin (Estimada)", 
        compute="_compute_fecha_fin", 
        store=True
    )

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
    ], string="Estado", default='borrador')

    # Relación One2many para almacenar los múltiples servicios de una misma cita
    lineas_ids = fields.One2many(
        comodel_name='stylehub.cita.line', 
        inverse_name='cita_id', 
        string="Servicios"
    )

    amount_total = fields.Float(string="Total a Pagar", compute="_compute_total", store=True)

    # MÉTODOS COMPUTADOS

    # Aqui se cree el nombre/referencia de la cita, 
    # con el servicio q se va a realizar y el cliente de esa cita
    @api.depends('cliente_id.name', 'lineas_ids.servicio_id.name')
    def _compute_name(self):
        """
        Genera el nombre de la cita dinámicamente uniendo los servicios y el cliente.
        Ejemplo: 'Corte, Lavado - Juan Pérez'
        """
        for cita in self:
            if cita.cliente_id:
                # Obtenemos una lista con los nombres de todos los servicios de esta cita
                nombres_servicios = cita.lineas_ids.mapped('servicio_id.name') # Utilizo el .mapped para no tener q acceder a la base de datos en cada acceso y obtener una lista directa de nombres
                servicios_str = ", ".join(nombres_servicios) if nombres_servicios else "Sin servicios"
                cita.name = f"{servicios_str} - {cita.cliente_id.name}"
            else:
                cita.name = "Nueva Cita"

    @api.depends('lineas_ids.precio')
    def _compute_total(self):
        """Suma el precio de todas las líneas de servicio para obtener el total."""
        for record in self:
            record.amount_total = sum(line.precio for line in record.lineas_ids)

    @api.depends('fecha_inicio', 'lineas_ids.servicio_id.duration')
    def _compute_fecha_fin(self):
        """
        Calcula la hora de finalización sumando las horas de duración 
        de cada servicio a la fecha de inicio mediante timedelta.
        """
        for record in self:
            if not record.fecha_inicio:
                record.fecha_fin = False
                continue
            horas_totales = sum(line.servicio_id.duration for line in record.lineas_ids)
            record.fecha_fin = record.fecha_inicio + timedelta(hours=horas_totales)

    # RESTRICCIONES Y VALIDACIONES
    
    @api.constrains('estilista_id', 'fecha_inicio', 'fecha_fin')
    def _check_solapamiento(self):
        """
        Evita que un mismo estilista tenga dos citas en el mismo rango de tiempo.
        Ignora las citas que han sido canceladas.
        """
        for cita in self:
            if not cita.fecha_inicio or not cita.fecha_fin:
                continue

            # Dominio para buscar citas que se crucen en el tiempo con la actual
            domain = [
                ('id', '!=', cita.id),
                ('estilista_id', '=', cita.estilista_id.id),
                ('state', '!=', 'cancelada'), 
                ('fecha_inicio', '<', cita.fecha_fin), 
                ('fecha_fin', '>', cita.fecha_inicio)
            ]

            if self.search_count(domain) > 0:
                raise ValidationError(f"¡CONFLICTO! El estilista {cita.estilista_id.name} ya tiene una cita en ese horario.")
    
    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_horario_comercial(self):
        """
        Valida que la cita se cree dentro del horario comercial (08:00 a 20:00).
        Fijado permanentemente a la hora de España peninsular.
        """
        for cita in self:
            if not cita.fecha_inicio or not cita.fecha_fin:
                continue

            # 1. Fijamos la zona horaria directamente a España
            tz_espana = pytz.timezone('Europe/Madrid')

            # 2. Convertimos las fechas UTC de la base de datos a la hora real de España
            inicio_local = pytz.utc.localize(cita.fecha_inicio).astimezone(tz_espana)
            fin_local = pytz.utc.localize(cita.fecha_fin).astimezone(tz_espana)

            # 3. Extraemos la hora (de 0 a 23)
            hora_inicio = inicio_local.hour
            hora_fin = fin_local.hour
            minuto_fin = fin_local.minute

            # LÓGICA: No antes de las 8:00, y no después de las 20:00 exactas
            if hora_inicio < 8 or hora_fin > 20 or (hora_fin == 20 and minuto_fin > 0):
                raise ValidationError(
                    f"¡Horario no válido!\n"
                    f"El horario comercial es de 08:00 a 20:00 (Hora de España).\n"
                    f"Estás intentando guardar una cita de {inicio_local.strftime('%H:%M')} a {fin_local.strftime('%H:%M')}."
                )
            
    # FLUJO DE ESTADOS (WORKFLOW)
    
    def action_confirmar(self):
        for rec in self:
            if not rec.lineas_ids:
                raise ValidationError("No puedes confirmar una cita vacía. Añade servicios primero.")
            rec.state = 'confirmada'

    def action_realizada(self):
        for rec in self:
            rec.state = 'realizada'

    def action_cancelar(self):
        for rec in self:
            rec.state = 'cancelada'

    def action_borrador(self):
        for rec in self:
            rec.state = 'borrador'


# MODELO DE LÍNEAS DE SERVICIO (DETALLE)

class StylehubCitaLine(models.Model):
    _name = 'stylehub.cita.line'
    _description = 'Línea de Servicio en Cita'

    cita_id = fields.Many2one('stylehub.cita', string="Cita", required=True, ondelete='cascade')
    servicio_id = fields.Many2one('stylehub.servicio', string="Servicio", required=True)
    precio = fields.Float(string="Precio")

    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        """
        Al seleccionar un servicio, trae automáticamente su precio base 
        desde el catálogo para que el usuario pueda editarlo si lo necesita.
        """
        if self.servicio_id:
            self.precio = self.servicio_id.price