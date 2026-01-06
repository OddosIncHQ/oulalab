from odoo import models, fields, api


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    indicadores_id = fields.Many2one(
        'hr.indicadores',
        string='Indicadores Previsionales',
        help='Valores de UF, UTM y otros usados en la nómina'
    )

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'indicadores_id' not in vals:
                indicadores = self.env['hr.indicadores'].search([], order='id desc', limit=1)
                vals['indicadores_id'] = indicadores.id if indicadores else False
        return super().create(vals_list)

    def compute_sheet_all(self):
        for rec in self:
            slips = rec.slip_ids.filtered(lambda s: s.state in ['draft', 'verify'])
            slips.compute_sheet()
