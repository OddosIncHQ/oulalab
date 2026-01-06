from odoo import models, fields

class HrAFP(models.Model):
    _name = 'hr.afp'
    _description = 'AFP'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')
    rate = fields.Float(string='Tasa (%)', digits=(16, 2))
    sis = fields.Float(string='SIS (%)', digits=(16, 2), help='Seguro de Invalidez y Sobrevivencia')
