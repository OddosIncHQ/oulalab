# -*- coding: utf-8 -*-
from odoo import models, fields

class HrContractType(models.Model):
    _inherit = 'hr.contract.type'
    _description = 'Tipo de Contrato Laboral (Chile)'

    # Campo utilizado para mapear con los códigos de Previred
    # (Ej: 1=Indefinido, 7=Plazo Fijo, 1=Sueldo Empresarial)
    l10n_cl_code = fields.Char(
        string='Código Previred', 
        help="Código numérico para archivos de Previred (ej: 1, 7, etc.)"
    )
