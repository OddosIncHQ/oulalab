# -*- coding: utf-8 -*-
{
    'name': 'Chilean Payroll (L10n CL)',
    'version': '19.0.1.0.0', # Ajustado a la versión 19
    'category': 'Localization/Payroll',
    'author': 'Blanco Martin & Asociados, Daniel Blanco',
    'website': 'https://blancomartin.cl',
    'license': 'AGPL-3',
    'summary': 'Nómina Chilena y Localización de Recursos Humanos',
    'description': """
Chilean Payroll Salary Rules.
========================================
* Configuración de hr_payroll para Chile.
* Reglas de contribución (Previred).
* Reportes de liquidación y Libro de Remuneraciones.
* Indicadores previsionales actualizados.
    """,
    'depends': [
        'hr_payroll', # NOTA: En Odoo 13+ hr_payroll es Enterprise. 
                      # Si usas Community, debes usar 'om_hr_payroll'.
        'hr_payroll_account', 
    ],
    'data': [
        'security/ir.model.access.csv', # Asegúrate de tener este archivo
        'views/report_hrsalarybymonth.xml',
        'views/report_payslip.xml',
        'views/hr_indicadores_previsionales_view.xml',
        'views/hr_salary_rule_view.xml',
        'views/hr_employee.xml',
        'data/l10n_cl_hr_payroll_data.xml',
    ],
    'demo': [
        'demo/l10n_cl_hr_payroll_demo.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
