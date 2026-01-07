# -*- coding: utf-8 -*-
{
    'name': 'Chilean Payroll & Human Resources',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'author': 'Konos',
    'website': 'http://konos.cl',
    'license': 'OEEL-1',
    'summary': 'Localización de Nómina y RRHH para Chile (Enterprise)',
    'contributors': [
        "Nelson Ramirez <info@konos.cl>",
        "Daniel Blanco Martin <daniel@blancomartin.com>",
        "Carlos Lopez Mite <celm1990@hotmail.com>",
        "Daniel Santibáñez Polanco <dsantibanez@globalresponse.cl>",
    ],
    'depends': [
        'hr',
        'hr_payroll',         # Trae hr_contract automáticamente
        'hr_payroll_account', # Contabilidad
        'l10n_cl',            # Localización base
    ],
    'external_dependencies': {
        'python': [
            'num2words',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/hr_salary_rule_category.xml',
        # 'data/hr_centros_costos.xml', # REVISAR: Comentado por seguridad (verificar si existe el archivo)
        'data/l10n_cl_hr_indicadores.xml',
        'data/l10n_cl_hr_isapre.xml',
        'data/l10n_cl_hr_afp.xml',
        'data/l10n_cl_hr_mutual.xml',
        'data/l10n_cl_hr_apv.xml',
        'data/hr_type_employee.xml',
        'data/resource_calendar_attendance.xml',
        'data/hr_holidays_status.xml',
        'data/hr_contract_type.xml',
        'data/l10n_cl_hr_ccaf.xml',
        'data/account_journal.xml',
        'data/partner.xml',
        'data/l10n_cl_hr_payroll_data.xml',
        'views/menu_root.xml',
        'views/hr_indicadores_previsionales_view.xml',
        'views/hr_salary_rule_view.xml',
        # 'views/hr_contract_view.xml',
        'views/hr_employee.xml',
        'views/hr_payslip_view.xml',
        'views/hr_afp_view.xml',
        # 'views/hr_payslip_run_view.xml', # COMENTADO: Wizard antiguo eliminado
        'views/report_payslip.xml',
        'views/report_hrsalarybymonth.xml',
        'views/hr_salary_books.xml',
        # 'views/hr_holiday_views.xml',    # COMENTADO: Riesgo de incompatibilidad hr.holidays vs hr.leave
        'views/wizard_export_csv_previred_view.xml',
    ],
    'demo': [
        'demo/l10n_cl_hr_payroll_demo.xml'
    ],
    'description': """
Chilean Payroll & Human Resources (Odoo 19 Enterprise)
======================================================
Payroll configuration for Chile localization compatible with Odoo 19 Enterprise.
    """,
    'installable': True,
    'application': True,
    'auto_install': False,
    'icon': '/l10n_cl_hr/static/description/icon.png',
}
