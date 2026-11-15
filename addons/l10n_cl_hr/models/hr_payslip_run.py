# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Lote de Nóminas (Chile)'
    _order = 'id desc'

    # Indicadores Previsionales del Lote
    l10n_cl_indicadores_id = fields.Many2one(
        'hr.indicadores',
        string='Indicadores Previsionales',
        readonly=True,
        # Usamos 'readonly=False' si el estado es 'draft' mediante XML o attrs en Odoo 18/19
        help='Valores de UF, UTM y topes usados para todas las nóminas de este lote.'
    )

    # Movimientos de Personal (Previred)
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
    ], string='Movimiento Personal (Lote)', default='0')

    # Campo auxiliar para mostrar el periodo (Mes-Año)
    l10n_cl_period = fields.Char(string='Periodo', compute='_compute_period', store=True)

    @api.depends('date_start')
    def _compute_period(self):
        for rec in self:
            if rec.date_start:
                rec.l10n_cl_period = rec.date_start.strftime('%m-%Y')
            else:
                rec.l10n_cl_period = ''

    @api.onchange('date_end')
    def _onchange_date_end(self):
        """ Auto-selecciona los indicadores basados en la fecha de fin """
        if self.date_end:
            indicador = self.env['hr.indicadores'].search([
                ('date', '<=', self.date_end)
            ], limit=1, order='date desc')
            if indicador:
                self.l10n_cl_indicadores_id = indicador.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Si no vienen indicadores, buscamos el último disponible
            if not vals.get('l10n_cl_indicadores_id'):
                date_ref = vals.get('date_end') or fields.Date.today()
                indicador = self.env['hr.indicadores'].search([
                    ('date', '<=', date_ref)
                ], limit=1, order='date desc')
                if indicador:
                    vals['l10n_cl_indicadores_id'] = indicador.id
        return super(HrPayslipRun, self).create(vals_list)

    def compute_sheet_all(self):
        """ Recalcula todas las nóminas del lote """
        for rec in self:
            # Filtramos solo las que no están canceladas o hechas
            slips = rec.slip_ids.filtered(lambda s: s.state in ['draft', 'verify'])
            
            # Propagamos los indicadores del lote a las nóminas individuales antes de calcular
            if rec.l10n_cl_indicadores_id:
                slips.write({
                    'l10n_cl_indicadores_id': rec.l10n_cl_indicadores_id.id,
                    'movimientos_personal': rec.movimientos_personal
                })
            
            slips.compute_sheet()
