# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError


class CrossoveredBudget(models.Model):
    _inherit = 'budget.analytic'

    @api.model
    def _custom_get_default_currency(self):
        return self.env.company.currency_id

    custom_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=_custom_get_default_currency,
        store=True,
        readonly=True,
        tracking=True,
    )

    custom_budget_currency_option = fields.Selection(
        selection=[
            ('company_currency', 'Budget in Company Currency'),
            ('other_currency', 'Budget in Other Currency'),
        ],
        string="Budget Currency Option",
        default='company_currency',
        readonly=True,
    )

    @api.onchange('custom_budget_currency_option')
    def onchange_custom_budget_currency_option(self):
        if self.custom_budget_currency_option == 'company_currency':
            self.custom_currency_id = self.company_id.currency_id

    @api.constrains('custom_currency_id')
    def _custom_currency_validation(self):
        for record in self:
            if record.custom_budget_currency_option == 'company_currency' and \
                    record.custom_currency_id != record.company_id.currency_id:
                raise ValidationError(_('Currency does not match with company currency!'))


class CrossoveredBudgetLines(models.Model):
    _inherit = 'budget.line'

    custom_currency_id = fields.Many2one(
        'res.currency',
        related="budget_analytic_id.custom_currency_id",
        readonly=True,
    )
    custom_planned_amount = fields.Monetary(
        compute='_compute_custom_planned_amount',
        string='Budgeted (Other Currency)',
        store=True,
        currency_field='custom_currency_id',
        inverse="_inverse_custom_planned_amount",
    )
    custom_practical_amount = fields.Monetary(
        compute='_compute_custom_all',
        string='Committed (Other Currency)',
        currency_field='custom_currency_id',
        help="Already billed amount + confirmed purchase orders.",
    )
    custom_achieved_amount = fields.Monetary(
        compute='_compute_custom_all',
        string='Achieved (Other Currency)',
        help="Amount billed/invoiced."
    )
    custom_theoretical_amount = fields.Monetary(
        compute='_compute_custom_theoretical_amount',
        string='Theoretical (Other Currency)',
        currency_field='custom_currency_id',
        help="Amount supposed to be billed/invoiced, calculated as "
             "(Budget Amount / Budget Days) x Budget Days Completed.",
    )

    def _compute_custom_all(self):
        grouped = {
            line: (committed, achieved)
            for line, committed, achieved in self.env['budget.report']._read_group(
                domain=[('budget_line_id', 'in', self.ids)],
                groupby=['budget_line_id'],
                aggregates=['committed:sum', 'achieved:sum'],
            )
        }
        for line in self:
            committed, achieved = grouped.get(line, (0, 0))
            line.custom_practical_amount = line.company_id.currency_id._convert(
                committed, line.custom_currency_id, line.company_id, fields.Date.today()
            )
            line.custom_achieved_amount = line.company_id.currency_id._convert(
                achieved, line.custom_currency_id, line.company_id, fields.Date.today()
            )

    @api.model
    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        fields_list = {'custom_practical_amount', 'custom_theoretical_amount'}

        def truncate_aggr(field):
            return field.split(':', 1)[0] if ':' in field else field

        fields = {truncate_aggr(field) for field in aggregates}

        result = super(CrossoveredBudgetLines, self)._read_group(domain, groupby, aggregates, having, offset, limit, order)

        if fields & fields_list:
            for group_line in result:
                if 'custom_practical_amount' in fields:
                    group_line['custom_practical_amount'] = sum(
                        line.custom_practical_amount for line in self.search(group_line.get('__domain', []))
                    )
                if 'custom_theoretical_amount' in fields:
                    group_line['custom_theoretical_amount'] = sum(
                        line.custom_theoretical_amount for line in self.search(group_line.get('__domain', []))
                    )

        return result

    @api.depends('budget_amount', 'custom_currency_id')
    def _compute_custom_planned_amount(self):
        for line in self:
            if line.budget_amount and line.currency_id != line.custom_currency_id:
                line.custom_planned_amount = line.currency_id._convert(
                    line.budget_amount, line.custom_currency_id, line.company_id, line.date_from or fields.Date.today()
                )
            else:
                line.custom_planned_amount = line.budget_amount

    def _inverse_custom_planned_amount(self):
        for line in self:
            if line.custom_planned_amount and line.currency_id != line.custom_currency_id:
                line.budget_amount = line.custom_currency_id._convert(
                    line.custom_planned_amount, line.currency_id, line.company_id, line.date_from or fields.Date.today()
                )
            else:
                line.budget_amount = line.custom_planned_amount

    @api.depends('date_from', 'date_to')
    def _compute_custom_theoretical_amount(self):
        today = fields.Date.today()
        for line in self:
            if not line.date_from or not line.date_to:
                line.custom_theoretical_amount = line.custom_planned_amount
            else:
                total_days = (line.date_to - line.date_from).days + 1
                elapsed_days = (today - line.date_from).days + 1
                if elapsed_days < 0:
                    line.custom_theoretical_amount = 0.0
                elif elapsed_days <= total_days:
                    line.custom_theoretical_amount = (elapsed_days / total_days) * line.custom_planned_amount
                else:
                    line.custom_theoretical_amount = line.custom_planned_amount
