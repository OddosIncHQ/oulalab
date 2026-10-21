# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HrIndicadores(models.Model):
    _name = 'hr.indicadores'
    _description = 'Indicadores Previsionales'

    name = fields.Char('Nombre', required=True)
    
    # Asignación Familiar
    asignacion_familiar_primer = fields.Float('Asignación Familiar Tramo 1')
    asignacion_familiar_segundo = fields.Float('Asignación Familiar Tramo 2')
    asignacion_familiar_tercer = fields.Float('Asignación Familiar Tramo 3')
    asignacion_familiar_monto_a = fields.Float('Monto Tramo Uno')
    asignacion_familiar_monto_b = fields.Float('Monto Tramo Dos')
    asignacion_familiar_monto_c = fields.Float('Monto Tramo Tres')
    
    # Seguro de Cesantía
    contrato_plazo_fijo_empleador = fields.Float('Contrato Plazo Fijo Empleador')
    contrato_plazo_fijo_trabajador = fields.Float('Contrato Plazo Fijo Trabajador')    
    contrato_plazo_indefinido_empleador = fields.Float('Contrato Plazo Indefinido Empleador')
    contrato_plazo_indefinido_empleador_otro = fields.Float('Contrato Plazo Indefinido 11 años o más')
    
    caja_compensacion = fields.Float('Caja Compensación')
    deposito_convenido = fields.Float('Deposito Convenido')
    fonasa = fields.Float('Fonasa')
    mutual_seguridad = fields.Float('Mutualidad')
    pensiones_ips = fields.Float('Pensiones IPS')
    sueldo_minimo = fields.Float('Sueldo Mínimo')
    sueldo_minimo_otro = fields.Float('Sueldo Mínimo (Menores 18 y Mayores 65)')
    
    # Tasas AFP
    tasa_afp_cuprum = fields.Float('Cuprum')
    tasa_afp_capital = fields.Float('Capital')
    tasa_afp_provida = fields.Float('ProVida')
    tasa_afp_modelo = fields.Float('Modelo')
    tasa_afp_planvital = fields.Float('PlanVital')
    tasa_afp_habitat = fields.Float('Habitat')
    
    # Tasas SIS
    tasa_sis_cuprum = fields.Float('SIS Cuprum')
    tasa_sis_capital = fields.Float('SIS Capital')
    tasa_sis_provida = fields.Float('SIS Provida')
    tasa_sis_planvital = fields.Float('SIS PlanVital')
    tasa_sis_habitat = fields.Float('SIS Habitat')
    tasa_sis_modelo = fields.Float('SIS Modelo')
    
    # Topes Imponibles
    tope_anual_apv = fields.Float('Tope Anual APV')
    tope_mensual_apv = fields.Float('Tope Mensual APV')
    tope_imponible_afp = fields.Float('Tope imponible AFP')
    tope_imponible_ips = fields.Float('Tope Imponible IPS')
    tope_imponible_salud = fields.Float('Tope Imponible Salud')
    tope_imponible_seguro_cesantia = fields.Float('Tope Imponible Seguro Cesantía')
    
    # Índices económicos
    uf = fields.Float('UF', required=True)
    utm = fields.Float('UTM', required=True)
    uta = fields.Float('UTA')
    uf_otros = fields.Float('UF Otros (Seguro Comp.)')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # En Odoo 19 'states' en Python está obsoleto, se maneja en el XML
    indicadores_id = fields.Many2one('hr.indicadores', 'Indicadores', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        # Si vienen indicadores en el contexto, se asignan automáticamente
        for vals in vals_list:
            if self.env.context.get('indicadores_id') and 'indicadores_id' not in vals:
                vals['indicadores_id'] = self.env.context.get('indicadores_id')
        return super(HrPayslip, self).create(vals_list)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    indicadores_id = fields.Many2one('hr.indicadores', 'Indicadores', required=True)


class HrIsapre(models.Model):
    _name = 'hr.isapre'
    _description = 'Isapres'

    name = fields.Char('Nombre', required=True)
    rut = fields.Char('RUT', required=True)


class HrAfp(models.Model):
    _name = 'hr.afp'
    _description = 'Administradoras de Fondos de Pensión'

    codigo = fields.Char('Código', required=True)
    name = fields.Char('Nombre', required=True)
    rut = fields.Char('RUT', required=True)
    rate = fields.Float('Tasa', required=True)
    sis = fields.Float('Aporte Empresa (SIS)', required=True)
    independiente = fields.Float('Independientes', required=True)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    afp_id = fields.Many2one('hr.afp', string='AFP')
    aporte_voluntario = fields.Float('APV')
    anticipo_sueldo = fields.Float('Anticipo de Sueldo')
    carga_familiar = fields.Integer('Cargas Familiares')
    colacion = fields.Float('Asig. Colación')
    isapre_id = fields.Many2one('hr.isapre', string='ISAPRE')
    isapre_cotizacion_uf = fields.Float('Cotización Isapre (UF)')
    movilizacion = fields.Float('Asig. Movilización')
    mutual_seguridad = fields.Boolean('Cotiza en Mutual')
    otro_no_imp = fields.Float('Otros No Imponibles')
    otros_imp = fields.Float('Otros Imponibles')
    pension = fields.Boolean('Es Pensionado')
    seguro_complementario = fields.Float('Seguro Complementario (UF)')
    viatico_santiago = fields.Float('Viático Santiago')
    
    # Campos relacionados actualizados a API moderna
    complete_name = fields.Char(related='employee_id.name', string='Nombre Completo', store=True)
    gratificacion_legal = fields.Boolean('Gratificación Legal Anual', default=True)
    
    aporte_voluntario_moneda = fields.Selection([
        ('uf', 'UF'), 
        ('clp', 'Pesos')
    ], string='Moneda APV', default="uf")
    
    seguro_complementario_moneda = fields.Selection([
        ('uf', 'UF'), 
        ('clp', 'Pesos')
    ], string='Moneda Seguro', default="uf")

    # Reemplazo de _defaults por el nuevo estándar 'default'
    type_id = fields.Many2one(
        'hr.contract.type', 
        string='Tipo de Contrato', 
        default=lambda self: self.env['hr.contract.type'].search([('name', '=', 'Plazo Indefinido')], limit=1)
    )


class HrTypeEmployee(models.Model):
    _name = 'hr.type.employee'
    _description = 'Tipo de Empleado'
    
    id_type = fields.Char('Código', required=True)
    name = fields.Char('Nombre', required=True)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    date_start = fields.Date('Fecha Inicio')
    date_end = fields.Date('Fecha Fin')


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        # Actualización de lógica de Wizard para Odoo 19
        active_id = self.env.context.get('active_id')
        if active_id:
            run = self.env['hr.payslip.run'].browse(active_id)
            if run.indicadores_id:
                # Inyectamos el indicador en el contexto para que las nóminas lo tomen
                self = self.with_context(indicadores_id=run.indicadores_id.id)
        return super(HrPayslipEmployees, self).compute_sheet()
