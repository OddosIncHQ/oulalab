from odoo import api, fields, models, _


class HrContractType(models.Model):
    _inherit = 'hr.contract.type'
    _description = 'Tipo de Contrato'

    codigo = fields.Char(string='Código')
