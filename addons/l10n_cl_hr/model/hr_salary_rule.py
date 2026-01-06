# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    _description = 'Regla Salarial Chile'

    # Vigencia de la regla (Opcional, para reglas temporales)
    date_start = fields.Date(string='Fecha Inicio', help="Fecha a partir de la cual aplica esta regla.")
    date_end = fields.Date(string='Fecha Fin', help="Fecha hasta la cual aplica esta regla.")

    # Campo CLAVE para la integración con Previred
    l10n_cl_previred_code = fields.Char(
        string='Código Previred',
        help="Código interno para asignar esta regla a una columna del archivo Previred (ej: P1, P2, HaberImponible, etc)."
    )

    # Opcional: Si usas contabilidad detallada por regla
    # account_debit = fields.Many2one('account.account', 'Cuenta de Débito', company_dependent=True)
    # account_credit = fields.Many2one('account.account', 'Cuenta de Crédito', company_dependent=True)
