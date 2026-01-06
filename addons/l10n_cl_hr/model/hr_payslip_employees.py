# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generación de Nóminas Masivas (Chile)'

    # Estandarizamos el nombre para coincidir con hr_payslip
    l10n_cl_indicadores_id = fields.Many2one('hr.indicadores', string='Indicadores Previsionales')
    
    movimientos_personal = fields.Selection([
        ('0', 'Sin Movimiento en el Mes'),
        ('1', 'Contratación a plazo indefinido'),
        ('2', 'Retiro'),
        ('3', 'Subsidios (Licencias Médicas)'),
        ('4', 'Permiso Sin Goce de Sueldos'),
        ('5', 'Incorporación en el Lugar de Trabajo'),
        ('6', 'Accidentes del Trabajo'),
        ('7', 'Contratación a plazo fijo'),
        ('8', 'Cambio Contrato plazo fijo a indefinido'),
        ('11', 'Otros Movimientos (Ausentismos)'),
        ('12', 'Reliquidación, Premio, Bono')
    ], string='Movimiento Personal', default='0')

    @api.model
    def default_get(self, fields_list):
        res = super(HrPayslipEmployees, self).default_get(fields_list)
        # Intentamos obtener el último indicador disponible
        indicadores = self.env['hr.indicadores'].search([], order='date desc', limit=1)
        
        # Si estamos en el contexto de un lote (Run), intentamos buscar por la fecha del lote
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'hr.payslip.run':
            run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
            if run.date_end:
                indicador_mes = self.env['hr.indicadores'].search([
                    ('date', '<=', run.date_end)
                ], order='date desc', limit=1)
                if indicador_mes:
                    indicadores = indicador_mes

        if indicadores:
            res.update({
                'l10n_cl_indicadores_id': indicadores.id,
                'movimientos_personal': '0'
            })
        return res

    def compute_sheet(self):
        """
        Genera las nóminas para los empleados seleccionados, inyectando
        los datos chilenos (Indicadores y Movimientos).
        """
        self.ensure_one()
        
        # Obtenemos el Lote (Run) activo
        if not self.env.context.get('active_id'):
            return {'type': 'ir.actions.act_window_close'}
            
        payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        
        if not self.employee_ids:
            raise UserError(_("Debe seleccionar al menos un empleado."))

        payslips = self.env['hr.payslip']
        
        for employee in self.employee_ids:
            # Obtenemos los datos base para la nómina usando el método nativo de Odoo
            # Esto calcula entradas, días trabajados, etc.
            slip_data = self.env['hr.payslip'].onchange_employee_id(
                payslip_run.date_start, 
                payslip_run.date_end, 
                employee.id, 
                contract_id=False
            )
            
            # Preparamos el diccionario de valores
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name', 'Nómina'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'company_id': self.env.company.id,
                
                # Campos específicos de Chile
                'l10n_cl_indicadores_id': self.l10n_cl_indicadores_id.id,
                'movimientos_personal': self.movimientos_personal,
                
                # Líneas One2many (Entradas y Días Trabajados)
                # Nota: En Odoo 19 es más seguro recrear las líneas
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', [])],
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', [])],
            }
            
            # Creamos la nómina
            payslips += self.env['hr.payslip'].create(res)
        
        # Calculamos las reglas salariales
        payslips.compute_sheet()
        
        return {'type': 'ir.actions.act_window_close'}
