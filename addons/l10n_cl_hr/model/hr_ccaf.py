from odoo import models, fields

class HrCCAF(models.Model):
    _name = 'hr.ccaf'
    _description = 'Caja de Compensación'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')
