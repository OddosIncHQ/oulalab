# -*- coding: utf-8 -*-
{
    'name': 'Chilean Payroll with Accounting',
    'version': '19.0.1.0.0',
    'category': 'Payroll/Localization',
    'author': 'Konos',
    'license': 'AGPL-3',
    'description': """
    Enlace Contable para Remuneraciones Chile (Odoo 19).
    Define las cuentas contables (Debe/Haber) para las reglas salariales.
    """,
    'depends': [
        'hr_payroll_account', # Módulo base de Odoo Enterprise para conta de nómina
        'l10n_cl',            # Localización chilena oficial (Plan de Cuentas)
        'l10n_cl_hr',         # Tu módulo de nómina migrado
    ],
    'data': [
        'data/l10n_cl_hr_payroll_account_data.xml',
    ],
    'auto_install': True, # Se instala automático si tienes l10n_cl_hr y contabilidad
    'installable': True,
}
