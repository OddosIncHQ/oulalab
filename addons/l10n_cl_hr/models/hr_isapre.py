# -*- coding: utf-8 -*-
from odoo import models, fields

class HrIsapre(models.Model):
    _name = 'hr.isapre'
    _description = 'Instituciones de Salud Previsional (Isapre)'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    
    code = fields.Char(
        string='Código Previred', 
        required=True,
        help="Código oficial para archivo de Previred (ej: 07, 01)"
    )
    
    # Campo obligatorio para que cargue el XML de datos
    rut = fields.Char(
        string='RUT', 
        help="RUT de la Isapre"
    )
    
    # Campo estándar para archivar registros sin borrarlos
    active = fields.Boolean(default=True, string="Activo")
