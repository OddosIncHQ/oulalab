from odoo import api, fields, models, _


class HrIsapre(models.Model):
    _name = 'hr.isapre'
    _description = 'Isapres'

    codigo = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
    rut = fields.Char(string='RUT', required=True)
