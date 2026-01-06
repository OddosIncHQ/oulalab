from odoo import api, fields, models, _


class HrMutual(models.Model):
    _name = 'hr.mutual'
    _description = 'Mutualidad'

    codigo = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
