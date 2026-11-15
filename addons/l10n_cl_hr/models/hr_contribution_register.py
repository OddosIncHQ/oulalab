# models/hr_contribution_register.py
from odoo import models, fields

class HrContributionRegister(models.Model):
    _name = 'hr.contribution.register'
    _description = 'Registro de Contribución'

    name = fields.Char(required=True, string='Nombre')
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    note = fields.Text(string='Descripción')
