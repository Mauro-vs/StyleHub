# -*- coding: utf-8 -*-
from odoo import models, fields


class StylehubEstilista(models.Model):
    _name = "stylehub.estilista"
    _description = "Estilista de StyleHub"

    image = fields.Image(string="Imagen", max_width=512, max_height=512)

    name = fields.Char(string="Nombre", required=True)
    especialidad = fields.Char(string="Especialidad")
    active = fields.Boolean(string="Activo", default=True)

    cita_ids = fields.One2many(
        comodel_name='stylehub.cita', 
        inverse_name='estilista_id', 
        string='Historial de Citas'
    )