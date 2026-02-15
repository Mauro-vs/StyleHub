# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Cliente(models.Model):
    # Usamos _inherit en lugar de _name
    _inherit = 'res.partner'

    # Añadimos un campo para contar las citas completadas
    cita_count = fields.Integer(string="Citas Realizadas", compute="_compute_citas_vip")
    
    # Campo booleano que nos dirá si es VIP o no
    is_vip = fields.Boolean(string="Es VIP", compute="_compute_citas_vip")

    def _compute_citas_vip(self):
        for partner in self:
            # self.env nos permite hacer consultas a OTROS modelos de la base de datos
            # Buscamos cuántas citas tienen a este cliente y están en estado "realizada"
            citas_completadas = self.env['stylehub.cita'].search_count([
                ('cliente_id', '=', partner.id),
                ('state', '=', 'realizada')
            ])
            
            partner.cita_count = citas_completadas
            # Es VIP si tiene 5 o más citas completadas
            partner.is_vip = (citas_completadas >= 5)