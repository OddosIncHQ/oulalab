# -*- coding: utf-8 -*-
from odoo import models, fields

class HrAPV(models.Model):
    _name = 'hr.apv'
    _description = 'Instituciones de Ahorro Previsional Voluntario (APV)'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', help="Código oficial para archivo de Previred")
    
    # Permite archivar la institución sin eliminarla de la base de datos
    active = fields.Boolean(default=True, string="Activo")
