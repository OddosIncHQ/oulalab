from odoo import models, fields

class HrIsapre(models.Model):
    _name = 'hr.isapre'
    _description = 'Isapre'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')
