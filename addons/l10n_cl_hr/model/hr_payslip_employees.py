from odoo import models, fields, api

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    indicadores_id = fields.Many2one('hr.indicadores', string='Indicadores Previsionales')
    movimientos_personal = fields.Selection([
        ('0', 'Sin Movimiento en el Mes'),
        ('1', 'Contratación a plazo indefinido'),
        ('2', 'Retiro'),
        ('3', 'Subsidios (L Médicas)'),
        ('4', 'Permiso Sin Goce de Sueldos'),
        ('5', 'Incorporación en el Lugar de Trabajo'),
        ('6', 'Accidentes del Trabajo'),
        ('7', 'Contratación a plazo fijo'),
        ('8', 'Cambio Contrato plazo fijo a indefinido'),
        ('11', 'Otros Movimientos (Ausentismos)'),
        ('12', 'Reliquidación, Premio, Bono')
    ], string='Movimiento Personal', default='0')

    @api.model
    def default_get(self, fields_list):
        res = super(HrPayslipEmployees, self).default_get(fields_list)
        indicadores = self.env['hr.indicadores'].search([], order='id desc', limit=1)
        res.update({
            'indicadores_id': indicadores.id if indicadores else False,
            'movimientos_personal': '0'
        })
        return res

    def compute_sheet(self):
        self.ensure_one()
        slips = self.env['hr.payslip'].browse(self.env.context.get('active_ids', []))
        slips.write({
            'indicadores_id': self.indicadores_id.id,
            'movimientos_personal': self.movimientos_personal
        })
        slips.compute_sheet()
