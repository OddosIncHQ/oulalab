# -*- coding: utf-8 -*-
from odoo import models, fields

class HrCCAF(models.Model):
    _name = 'hr.ccaf'
    _description = 'Cajas de Compensación de Asignación Familiar (CCAF)'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', help="Código oficial para archivo de Previred")
    
    # Campo estándar para archivar registros
    active = fields.Boolean(default=True, string="Activo")
