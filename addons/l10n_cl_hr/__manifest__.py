{
    'name': 'Chilean Payroll & Human Resources',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'author': 'Konos',
    'website': 'http://konos.cl',
    'license': 'AGPL-3',
    'summary': 'Localización de Nómina y RRHH para Chile',
    'contributors': [
        "Nelson Ramirez <info@konos.cl>",
        "Daniel Blanco Martin <daniel@blancomartin.com>",
        "Carlos Lopez Mite <celm1990@hotmail.com>",
        "Daniel Santibáñez Polanco <dsantibanez@globalresponse.cl>",
    ],
    'depends': [
        'hr',
        'hr_contract',
        'hr_payroll',         # Odoo Enterprise. Si usas Community, cambia por 'om_hr_payroll'
        'hr_payroll_account', # Para contabilizar la nómina
        'l10n_cl',            # REQUERIDO en Odoo 18 para datos chilenos (RUT, Comunas)
    ],
    'external_dependencies': {
        'python': [
            'num2words',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/hr_salary_rule_category.xml',
        'data/hr_centros_costos.xml',
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
        'views/hr_contract_view.xml',
        'views/hr_employee.xml',
        'views/hr_payslip_view.xml',
        'views/hr_afp_view.xml',
        'views/hr_payslip_run_view.xml',
        'views/report_payslip.xml',
        'views/report_hrsalarybymonth.xml',
        'views/hr_salary_books.xml',
        'views/hr_holiday_views.xml',
        'views/wizard_export_csv_previred_view.xml',
    ],
    'demo': [
        'demo/l10n_cl_hr_payroll_demo.xml'
    ],
    'description': """
Chilean Payroll & Human Resources (Odoo 18 Migration)
=====================================================
Payroll configuration for Chile localization.
Includes rules for:
* Employee Basic Info & Contracts (RUT, AFP, Isapre)
* Attendance, Holidays and Sick License
* Employee PaySlip & Salary Rules
* Allowances / Deductions / Company Inputs
* Chilean Indicators (UF, UTM)
* Payroll Books (Libro de Remuneraciones)
* Previred Plain Text Generation
    """,
    'installable': True,
    'application': True,
    'auto_install': False,
    'icon': '/l10n_cl_hr/static/description/icon.png',
}
