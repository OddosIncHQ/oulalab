from odoo import api, fields, models, _

class HrSeguroComplementario(models.Model):
    _name = 'hr.seguro.complementario'
    _description = 'Seguro Complementario'

    codigo = fields.Char('Código', required=True)
    name = fields.Char('Nombre', required=True)
