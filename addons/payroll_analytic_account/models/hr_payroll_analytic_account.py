# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    # Campo para activar la analítica desde el contrato
    account_analytic_true = fields.Boolean(
        string='Usar Cuenta Analítica del Contrato',
        help="Si se marca, el gasto generado por esta regla se imputará a la cuenta analítica definida en el contrato del empleado."
    )

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        """
        Extendemos el método estándar que prepara el diccionario para el asiento contable.
        """
        # Llamamos al método original para obtener los valores base (cuenta, debito, credito, etc)
        vals = super(HrPayslip, self)._prepare_line_values(line, account_id, date, debit, credit)

        # Verificamos si la regla salarial tiene activado el check "Usar Cuenta Analítica del Contrato"
        if line.salary_rule_id.account_analytic_true and self.contract_id.analytic_account_id:
            # En Odoo 17/18/19, la analítica se maneja con 'analytic_distribution'
            # Es un diccionario {id_cuenta_analitica: porcentaje}
            vals['analytic_distribution'] = {
                self.contract_id.analytic_account_id.id: 100
            }
        
        # Opcional: Si la regla tiene una cuenta analítica fija asignada directamente (comportamiento estándar)
        elif line.salary_rule_id.analytic_account_id:
             vals['analytic_distribution'] = {
                line.salary_rule_id.analytic_account_id.id: 100
            }

        return vals
