# -*- coding: utf-8 -*-
from odoo import models, fields

class HrTypeEmployee(models.Model):
    _name = 'hr.type.employee'
    _description = 'Tipo de Trabajador (Código Previred)'
    _order = 'id_type asc'

    # Código oficial para el archivo de Previred (ej: 0=Activo, 1=Pensionado, etc.)
    id_type = fields.Char(string='Código Previred', required=True)
    
    name = fields.Char(string='Descripción', required=True)
    
    # Campo estándar para archivar en Odoo 19
    active = fields.Boolean(default=True, string="Activo")
