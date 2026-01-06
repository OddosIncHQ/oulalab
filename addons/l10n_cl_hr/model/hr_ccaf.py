from odoo import api, fields, models, _


class HrCCAF(models.Model):
    _name = 'hr.ccaf'
    _description = 'Caja de Compensación (CCAF)'

    codigo = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
