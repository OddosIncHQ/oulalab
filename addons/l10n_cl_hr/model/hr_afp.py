# -*- coding: utf-8 -*-
from odoo import models, fields

class HrAFP(models.Model):
    _name = 'hr.afp'
    _description = 'Administradoras de Fondos de Pensiones (AFP)'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', help="Código oficial para Previred")
    
    # En Odoo 19, digits=(16, 2) sigue siendo válido para precisión fija
    rate = fields.Float(string='Tasa (%)', digits=(16, 2))
    
    sis = fields.Float(
        string='SIS (%)', 
        digits=(16, 2), 
        help='Seguro de Invalidez y Sobrevivencia (A cargo del empleador)'
    )
    
    # Campo estándar en Odoo moderno para archivar registros sin borrarlos
    active = fields.Boolean(default=True, string="Activo")
