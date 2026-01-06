# -*- coding: utf-8 -*-
from odoo import models, fields

class HrContractType(models.Model):
    _inherit = 'hr.contract.type'
    _description = 'Tipo de Contrato Laboral'

    # Campo utilizado para mapear con los códigos de Previred / Dirección del Trabajo
    codigo = fields.Char(
        string='Código Oficial', 
        help="Código numérico para archivos de Previred (ej: 1 para Indefinido)"
    )
