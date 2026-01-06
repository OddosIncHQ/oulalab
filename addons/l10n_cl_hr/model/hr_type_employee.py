from odoo import api, fields, models, _


class HrTypeEmployee(models.Model):
    _name = 'hr.type.employee'
    _description = 'Tipo de Empleado'

    id_type = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
