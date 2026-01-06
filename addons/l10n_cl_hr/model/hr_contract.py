# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Contrato del Empleado (Chile)'

    # ---------------------------------------------------------
    # Entidades Previsionales y Salud
    # ---------------------------------------------------------
    afp_id = fields.Many2one('hr.afp', string='AFP')
    isapre_id = fields.Many2one('hr.isapre', string='ISAPRE')
    seguro_complementario_id = fields.Many2one('hr.seguro.complementario', string='Seguro Complementario')
    apv_id = fields.Many2one('hr.apv', string='APV / Institución Ahorro')
    mutual_seguridad = fields.Boolean(string='Cotiza Mutual Seguridad', default=True)

    # ---------------------------------------------------------
    # Asignaciones Familiares y Cargas
    # ---------------------------------------------------------
    carga_familiar = fields.Integer(string='Cargas Simples', help="Cantidad de cargas familiares normales")
    carga_familiar_maternal = fields.Integer(string='Cargas Maternales', help="Cantidad de cargas por maternidad")
    carga_familiar_invalida = fields.Integer(string='Cargas Inválidas', help="Cantidad de cargas por invalidez")

    # ---------------------------------------------------------
    # Haberes No Imponibles (Asignaciones)
    # ---------------------------------------------------------
    colacion = fields.Float(string='Asig. Colación', digits='Payroll', help="Monto fijo mensual por colación")
    movilizacion = fields.Float(string='Asig. Movilización', digits='Payroll', help="Monto fijo mensual por movilización")
    viatico_santiago = fields.Float(string='Asig. Viático', digits='Payroll', help="Monto por viático (Opcional)")
    otro_no_imp = fields.Float(string='Otros No Imponibles', digits='Payroll', help="Otros haberes fijos no imponibles")
    
    # ---------------------------------------------------------
    # Otros Haberes e Inputs
    # ---------------------------------------------------------
    otros_imp = fields.Float(string='Otros Imponibles', digits='Payroll', help="Otros haberes fijos imponibles")
    anticipo_sueldo = fields.Float(string='Anticipo de Sueldo Fijo', digits='Payroll', help="Monto fijo de anticipo (si aplica recurrentemente)")
    gratificacion_legal = fields.Boolean(string='Gratificación Legal Manual', 
                                         help="Si está marcado, se usa lógica manual o tope del 25% según reglas salariales.")

    # ---------------------------------------------------------
    # Definiciones de Salud (Isapre/Fonasa)
    # ---------------------------------------------------------
    isapre_moneda = fields.Selection([
        ('uf', 'UF'), 
        ('clp', 'Pesos (CLP)')
    ], string='Moneda Plan Salud', default='uf')
    
    isapre_cotizacion_uf = fields.Float(string='Cotización Pactada', digits=(16, 4), 
                                        help="Valor del plan en UF o Pesos según la moneda seleccionada")
    
    isapre_fun = fields.Char(string='Número de FUN', help="Folio Único de Notificación (Isapre)")
    isapre_cuenta_propia = fields.Boolean(string='Cotización Adicional Voluntaria (Cuenta Propia)')

    # ---------------------------------------------------------
    # Ahorro Previsional Voluntario (APV)
    # ---------------------------------------------------------
    aporte_voluntario = fields.Float(string='Monto APV', digits=(16, 4), help="Monto mensual pactado")
    
    aporte_voluntario_moneda = fields.Selection([
        ('uf', 'UF'), 
        ('clp', 'Pesos (CLP)')
    ], string='Moneda APV', default='uf')
    
    forma_pago_apv = fields.Selection([
        ('1', 'Descuento Directo (Empleador)'), 
        ('2', 'Pago Indirecto')
    ], string='Forma de Pago APV', default='1')

    # ---------------------------------------------------------
    # Seguro Complementario
    # ---------------------------------------------------------
    seguro_complementario = fields.Float(string='Costo Seguro Comp.', digits='Payroll', help="Monto a descontar al empleado")
    
    seguro_complementario_moneda = fields.Selection([
        ('uf', 'UF'), 
        ('clp', 'Pesos (CLP)')
    ], string='Moneda Seguro Comp.', default='clp')

    # ---------------------------------------------------------
    # Flags de Excepción
    # ---------------------------------------------------------
    pension = fields.Boolean(string='Es Pensionado', help="Indica si el empleado ya está pensionado (afecta cálculo SIS)")
    sin_afp = fields.Boolean(string='Exento de AFP', help="No calcular cotización obligatoria AFP")
    sin_afp_sis = fields.Boolean(string='Exento de SIS', help="No calcular Seguro de Invalidez y Sobrevivencia")

    # ---------------------------------------------------------
    # Campos Relacionados (Legacy)
    # ATENCION: Odoo 19 nativo NO tiene firstname/lastname separados.
    # Se comentan para evitar errores de instalacion. 
    # Descomentar solo si tienes instalado el modulo 'partner_firstname' de OCA.
    # ---------------------------------------------------------
    # complete_name = fields.Char(related='employee_id.firstname', readonly=True)
    # last_name = fields.Char(related='employee_id.last_name', readonly=True)
