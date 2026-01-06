# -*- coding: utf-8 -*-
from odoo import models, fields

class HrSeguroComplementario(models.Model):
    _name = 'hr.seguro.complementario'
    _description = 'Seguro Complementario de Salud'
    _order = 'name asc'

    name = fields.Char(string='Nombre Aseguradora', required=True)
    code = fields.Char(string='Código Interno', required=True)
    
    # Útil para reportes o identificación oficial
    rut = fields.Char(string='RUT Aseguradora', help="RUT de la compañía de seguros")
    
    # Campo estándar para archivar
    active = fields.Boolean(default=True, string="Activo")
