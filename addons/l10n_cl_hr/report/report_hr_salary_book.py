# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError

class ReportHrSalaryByMonth(models.AbstractModel):
    _name = 'report.l10n_cl_hr.report_hrsalarybymonth'
    _description = 'Reporte Libro de Remuneraciones'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prepara los datos para el reporte QWeb.
        En Odoo moderno, 'docids' son los IDs del wizard que lanzó el reporte.
        """
        # Obtenemos el registro del wizard
        model = 'hr.salary.employee.month'
        docs = self.env[model].browse(docids)
        
        if not docs:
            raise UserError(_("No se encontró el asistente de impresión."))

        # Como es un wizard, generalmente hay un solo registro (docids[0])
        wizard = docs[0]

        # Pasamos el objeto wizard a las funciones helper
        get_employee2 = self.get_employee_haberes(wizard)
        get_employee = self.get_employee_descuentos(wizard)
        
        # Analytic (opcional, mantuve la lógica si la usas)
        # get_analytic = self.get_analytic(wizard) 

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'get_employee': get_employee,     # Tabla Descuentos
            'get_employee2': get_employee2,   # Tabla Haberes
            'res_company': self.env.company,
        }

    # -------------------------------------------------------------------------
    # HELPER FUNCTIONS (SQL)
    # -------------------------------------------------------------------------

    def get_centro_costo(self, analytic_id):
        if not analytic_id:
            return "00"
        
        # Optimizacion: Usar ORM cacheado o SQL directo si es lento
        account = self.env['account.analytic.account'].browse(analytic_id)
        return account.code or account.name or "00"

    def get_worked_days(self, emp_id, emp_salary, month, year):
        """ Obtiene días trabajados (WORK100) """
        query = """
            SELECT sum(number_of_days) 
            FROM hr_payslip_worked_days as p
            LEFT JOIN hr_payslip as r on r.id = p.payslip_id
            WHERE r.employee_id = %s 
              AND EXTRACT(MONTH FROM r.date_to) = %s
              AND EXTRACT(YEAR FROM r.date_to) = %s
              AND p.code = 'WORK100'
              AND r.state = 'done'
        """
        self.env.cr.execute(query, (emp_id, month, year))
        result = self.env.cr.fetchone()
        
        days = result[0] if result and result[0] is not None else 0.0
        emp_salary.append(days)
        return emp_salary

    def get_salary_rule_value(self, emp_id, emp_salary, rule_code_pattern, month, year):
        """ 
        Obtiene la suma de una regla salarial (o patrón de reglas)
        Ej: rule_code_pattern = 'SUELDO' o 'HEX%'
        """
        query = """
            SELECT sum(pl.total) 
            FROM hr_payslip_line as pl
            LEFT JOIN hr_payslip as p on pl.slip_id = p.id
            WHERE p.state = 'done' 
              AND p.employee_id = %s 
              AND pl.code LIKE %s
              AND EXTRACT(MONTH FROM p.date_to) = %s
              AND EXTRACT(YEAR FROM p.date_to) = %s
        """
        self.env.cr.execute(query, (emp_id, rule_code_pattern, month, year))
        result = self.env.cr.fetchone()

        amount = result[0] if result and result[0] is not None else 0.0
        emp_salary.append(amount)
        return emp_salary

    # -------------------------------------------------------------------------
    # CONSTRUCCION DE TABLAS
    # -------------------------------------------------------------------------

    def get_employee_haberes(self, wizard):
        """ Genera la Tabla 1: HABERES """
        emp_salary_list = []
        
        # Fechas desde el objeto wizard (Date object)
        last_year = wizard.end_date.year
        last_month = wizard.end_date.month

        # Buscamos empleados con nóminas en ese mes
        query = """
            SELECT emp.id, emp.identification_id, emp.name, 
                   r.analytic_account_id
            FROM hr_payslip as p 
            LEFT JOIN hr_employee as emp on emp.id = p.employee_id
            LEFT JOIN hr_contract as r on r.id = p.contract_id
            WHERE p.state = 'done' 
              AND EXTRACT(MONTH FROM p.date_to) = %s
              AND EXTRACT(YEAR FROM p.date_to) = %s
            GROUP BY emp.id, emp.name, emp.identification_id, r.analytic_account_id
            ORDER BY emp.name
        """
        self.env.cr.execute(query, (last_month, last_year))
        employees_data = self.env.cr.fetchall()

        if not employees_data:
            return []

        for emp in employees_data:
            # Estructura de la fila (List)
            # Índices correspondientes al XML <tr t-foreach="get_employee2">
            
            emp_id = emp[0]
            emp_rut = emp[1] or ''
            emp_name = emp[2] or ''
            analytic_id = emp[3]
            
            row = []
            row.append(self.get_centro_costo(analytic_id)) # 0: CC
            row.append(emp_rut)                            # 1: RUT
            row.append(emp_name)                           # 2: Nombre
            row.append("") # 3: (Espacio reservado legacy)
            row.append("") # 4: (Espacio reservado legacy)
            row.append("") # 5: (Espacio reservado legacy)
            
            # 6: Días Trabajados
            row = self.get_worked_days(emp_id, row, last_month, last_year)

            # --- COLUMNAS DE HABERES (Ajustar códigos según tus reglas salariales) ---
            # 7: Sueldo Base
            row = self.get_salary_rule_value(emp_id, row, 'SUELDO', last_month, last_year)
            # 8: Horas Extras
            row = self.get_salary_rule_value(emp_id, row, 'HEX%', last_month, last_year)
            # 9: Gratificación
            row = self.get_salary_rule_value(emp_id, row, 'GRAT', last_month, last_year)
            # 10: Otros Imponibles (BONO)
            row = self.get_salary_rule_value(emp_id, row, 'BONO', last_month, last_year)
            # 11: Total Imponible
            row = self.get_salary_rule_value(emp_id, row, 'TOTIM', last_month, last_year)
            # 12: Asignación Familiar
            row = self.get_salary_rule_value(emp_id, row, 'ASIGFAM', last_month, last_year)
            # 13: Otros No Imponibles (Colación/Movilización)
            row = self.get_salary_rule_value(emp_id, row, 'TOTNOI', last_month, last_year)
            # 14: Total No Imponible (Repetido en tu lógica original, ajusta si necesario)
            row = self.get_salary_rule_value(emp_id, row, 'TOTNOI', last_month, last_year) 
            # 15: Total Haberes
            row = self.get_salary_rule_value(emp_id, row, 'HAB', last_month, last_year)

            emp_salary_list.append(row)

        return emp_salary_list

    def get_employee_descuentos(self, wizard):
        """ Genera la Tabla 2: DESCUENTOS """
        emp_salary_list = []
        
        last_year = wizard.end_date.year
        last_month = wizard.end_date.month

        # Misma Query de empleados
        query = """
            SELECT emp.id, emp.identification_id, emp.name, 
                   r.analytic_account_id
            FROM hr_payslip as p 
            LEFT JOIN hr_employee as emp on emp.id = p.employee_id
            LEFT JOIN hr_contract as r on r.id = p.contract_id
            WHERE p.state = 'done' 
              AND EXTRACT(MONTH FROM p.date_to) = %s
              AND EXTRACT(YEAR FROM p.date_to) = %s
            GROUP BY emp.id, emp.name, emp.identification_id, r.analytic_account_id
            ORDER BY emp.name
        """
        self.env.cr.execute(query, (last_month, last_year))
        employees_data = self.env.cr.fetchall()

        if not employees_data:
            return []

        for emp in employees_data:
            emp_id = emp[0]
            emp_rut = emp[1] or ''
            emp_name = emp[2] or ''
            analytic_id = emp[3]
            
            row = []
            row.append(self.get_centro_costo(analytic_id)) # 0
            row.append(emp_rut)                            # 1
            row.append(emp_name)                           # 2
            row.append("") # 3
            row.append("") # 4
            row.append("") # 5
            
            # 6: Días Trabajados
            row = self.get_worked_days(emp_id, row, last_month, last_year)

            # --- COLUMNAS DE DESCUENTOS ---
            # 7: Previsión (AFP)
            row = self.get_salary_rule_value(emp_id, row, 'PREV', last_month, last_year)
            # 8: Salud (Isapre/Fonasa)
            row = self.get_salary_rule_value(emp_id, row, 'SALUD', last_month, last_year)
            # 9: Impuesto Único
            row = self.get_salary_rule_value(emp_id, row, 'IMPUNI', last_month, last_year)
            # 10: Seguro Cesantía
            row = self.get_salary_rule_value(emp_id, row, 'SECE', last_month, last_year)
            # 11: Otros Descuentos Legales (Adicional Salud)
            row = self.get_salary_rule_value(emp_id, row, 'ADISA', last_month, last_year)
            # 12: Total Descuentos Legales
            row = self.get_salary_rule_value(emp_id, row, 'TODELE', last_month, last_year)
            # 13: Descuentos Varios (Prestamos, etc)
            row = self.get_salary_rule_value(emp_id, row, 'SMT', last_month, last_year) 
            # 14: Total Descuentos
            row = self.get_salary_rule_value(emp_id, row, 'TDE', last_month, last_year)
            # 15: Líquido a Pagar
            row = self.get_salary_rule_value(emp_id, row, 'LIQ', last_month, last_year)

            emp_salary_list.append(row)

        return emp_salary_list
