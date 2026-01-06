# -*- coding: utf-8 -*-
from odoo import models, fields

class HrIsapre(models.Model):
    _name = 'hr.isapre'
    _description = 'Instituciones de Salud Previsional (Isapre)'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', help="Código oficial para archivo de Previred")
    
    # Campo estándar para archivar registros sin borrarlos (Best Practice Odoo)
    active = fields.Boolean(default=True, string="Activo")
