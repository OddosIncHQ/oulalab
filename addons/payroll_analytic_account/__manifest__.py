# -*- coding: utf-8 -*-
{
    'name': 'Payroll Analytic Account',
    'version': '19.0.1.0.0',
    'category': 'Payroll/Accounting',
    'author': 'Konos',
    'website': 'http://konos.cl',
    'license': 'AGPL-3',
    'summary': 'Imputación automática de Cuentas Analíticas desde el Contrato en la Nómina',
    'description': """
Payroll Analytic Account (Odoo 19)
==================================

Este módulo permite distribuir los gastos de nómina a Centros de Costo (Cuentas Analíticas).

Características:
----------------
* Agrega un campo "Cuenta Analítica" obligatorio en el Contrato del empleado.
* Agrega una opción en las Reglas Salariales: "Usar Cuenta Analítica del Contrato".
* Al confirmar la nómina, el asiento contable hereda la cuenta analítica del contrato para las líneas correspondientes.
    """,
    'depends': [
        'hr_payroll_account', # Módulo base de contabilidad de nómina
        'hr_contract',        # Modificamos la vista del contrato
        'account',            # Necesario para el modelo de cuentas analíticas
    ],
    'data': [
        'views/hr_payroll_analytic_account_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
