from odoo import api, fields, models, _


class HrAFP(models.Model):
    _name = 'hr.afp'
    _description = 'Fondos de Pensiones'

    codigo = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
    rut = fields.Char(string='RUT', required=True)
    rate = fields.Float(string='Tasa', required=True, help="Tasa de cotización obligatoria")
    sis = fields.Float(string='Aporte Empresa', required=True, help="Seguro de Invalidez y Sobrevivencia")
    independiente = fields.Float(string='Independientes', required=True, help="Tasa para trabajadores independientes")
