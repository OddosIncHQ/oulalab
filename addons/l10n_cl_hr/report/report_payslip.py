# -*- coding: utf-8 -*-
from odoo import api, models
from .amount_to_text_es import amount_to_text

class PayslipReport(models.AbstractModel):
    # Este nombre vincula la clase con el ID del template XML 'hr_payroll.report_payslip'
    _name = 'report.hr_payroll.report_payslip'
    _description = 'Reporte de Liquidación de Sueldo'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Sobrescribe la generación de valores para el reporte.
        Aquí inyectamos funciones personalizadas para usar en el QWeb.
        """
        # Obtenemos los objetos de nómina seleccionados
        payslips = self.env['hr.payslip'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'data': data,
            'company_id': self.env.company,
            
            # Inyectamos la función personalizada de conversión a texto
            # En el XML se usa como: <span t-esc="convert(o.net_wage, o.currency_id)"/>
            'convert': self._convert_to_text,
        }

    def _convert_to_text(self, amount, currency):
        """
        Función helper para convertir montos a palabras usando 
        la librería personalizada 'amount_to_text_es.py'
        """
        if not amount:
            return ""
            
        currency_name = currency.name if currency else 'CLP'
        return amount_to_text(amount, 'es', currency_name)
