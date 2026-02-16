# -*- coding: utf-8 -*-
from odoo import models, fields # type: ignore

class StylehubServicio(models.Model):
    _name = "stylehub.servicio"
    _description = "Servicio de StyleHub"

    name = fields.Char(string="Nombre del Servicio", required=True)
    price = fields.Float(string="Precio", required=True)
    duration = fields.Float(string="Duración (horas)", required=True, default=0.5)