# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrSalaryEmployeeByMonth(models.TransientModel):
    _name = 'hr.salary.employee.month'
    _description = 'Asistente Libro de Remuneraciones'

    # Odoo maneja automáticamente el formato YYYY-MM-DD
    end_date = fields.Date(
        string='Fecha de Cierre', 
        required=True, 
        default=fields.Date.context_today,
        help="Seleccione una fecha dentro del mes que desea imprimir (generalmente fin de mes)."
    )

    def print_report(self):
        """
        Imprime el reporte PDF.
        Llama a la acción de reporte definida en hr_salary_books_view.xml
        """
        self.ensure_one()
        
        # En Odoo 19, simplemente pasamos el recordset del wizard (self).
        # El AbstractModel (report_hr_salary_book.py) leerá 'end_date' desde aquí.
        return self.env.ref('l10n_cl_hr.hr_salary_books').report_action(self)
