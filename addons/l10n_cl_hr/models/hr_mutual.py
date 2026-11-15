# -*- coding: utf-8 -*-
from odoo import models, fields

class HrMutual(models.Model):
    _name = 'hr.mutual'
    _description = 'Mutual de Seguridad'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    
    # Coincide con <field name="code"> en el XML de datos
    code = fields.Char(
        string='Código Previred', 
        required=True, 
        help="Código oficial para archivo de Previred (ej: 01, 02)"
    )
    
    rut = fields.Char(string='RUT', help="RUT de la institución")
    
    active = fields.Boolean(default=True, string="Activo")
