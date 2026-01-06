from odoo import models, fields

class HrAPV(models.Model):
    _name = 'hr.apv'
    _description = 'Institución APV'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')
