# -*- coding: utf-8 -*-
from odoo import models, fields

class HrAFP(models.Model):
    _name = 'hr.afp'
    _description = 'Administradoras de Fondos de Pensiones (AFP)'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    
    code = fields.Char(
        string='Código Previred', 
        required=True,
        help="Código oficial para archivo Previred (ej: 33, 03, etc)"
    )
    
    rut = fields.Char(
        string='RUT', 
        help="RUT de la Institución (Formato XX.XXX.XXX-X)"
    )

    # Tasa Cotización Obligatoria (10% + Comisión)
    rate = fields.Float(
        string='Tasa (%)', 
        digits=(16, 2),
        help="Porcentaje total a descontar al trabajador (10% fondo + comisión AFP)"
    )
    
    # Seguro de Invalidez y Sobrevivencia (Costo Empleador)
    sis = fields.Float(
        string='SIS (%)', 
        digits=(16, 2), 
        default=1.49,
        help='Seguro de Invalidez y Sobrevivencia (A cargo del empleador, excepto jubilados)'
    )
    
    # Tasa para trabajadores independientes (usualmente igual a rate)
    independiente = fields.Float(
        string='Tasa Independiente (%)', 
        digits=(16, 2)
    )

    # Campo estándar para ocultar registros antiguos (ej: AFP Masvida)
    active = fields.Boolean(default=True, string="Activo")
