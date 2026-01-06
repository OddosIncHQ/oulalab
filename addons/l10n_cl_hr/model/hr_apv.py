from odoo import api, fields, models, _


class HrAPV(models.Model):
    _name = 'hr.apv'
    _description = 'Institución Autorizada APV - APVC : Compañías de Seguros de Vida'

    codigo = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
