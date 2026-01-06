# -*- coding: utf-8 -*-
from odoo import models, fields

class HrMutual(models.Model):
    _name = 'hr.mutual'
    _description = 'Mutual de Seguridad'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    
    # Se estandariza a 'code' para consistencia con el resto de modelos (AFP, Isapre)
    code = fields.Char(string='Código Previred', required=True, help="Código oficial para archivo de Previred (ej: 1)")
    
    rut = fields.Char(string='RUT', help="RUT de la institución")
    
    # Campo estándar para archivar
    active = fields.Boolean(default=True, string="Activo")
