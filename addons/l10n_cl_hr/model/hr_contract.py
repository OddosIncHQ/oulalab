from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    afp_id = fields.Many2one('hr.afp', string='AFP')
    isapre_id = fields.Many2one('hr.isapre', string='ISAPRE')
    seguro_complementario_id = fields.Many2one('hr.seguro.complementario', string='Seguro Complementario')
    apv_id = fields.Many2one('hr.apv', string='APV')

    anticipo_sueldo = fields.Float(string='Anticipo de Sueldo', help="Anticipo realizado contablemente")
    carga_familiar = fields.Integer(string='Carga Simple', help="Asignación familiar simple")
    carga_familiar_maternal = fields.Integer(string='Carga Maternal', help="Asignación familiar maternal")
    carga_familiar_invalida = fields.Integer(string='Carga Inválida', help="Asignación familiar inválida")

    colacion = fields.Float(string='Asig. Colación', help="Monto asignado por colación")
    movilizacion = fields.Float(string='Asig. Movilización', help="Monto asignado por movilización")
    viatico_santiago = fields.Float(string='Asig. Viático', help="Monto asignado por viático en Santiago")
    otro_no_imp = fields.Float(string='Otros No Imponible', help="Otros haberes no imponibles")
    otros_imp = fields.Float(string='Otros Imponible', help="Otros haberes imponibles")

    seguro_complementario = fields.Float(string='Cotización', help="Monto cotizado por seguro complementario")
    isapre_cotizacion_uf = fields.Float(string='Cotización Isapre', digits=(6, 4), help="Monto pactado en UF")
    isapre_fun = fields.Char(string='Número de FUN', help="Número de contrato de salud con Isapre")
    isapre_cuenta_propia = fields.Boolean(string='Isapre Cuenta Propia')
    mutual_seguridad = fields.Boolean(string='Mutual Seguridad', default=True)
    pension = fields.Boolean(string='Pensionado')
    sin_afp = fields.Boolean(string='No Calcula AFP')
    sin_afp_sis = fields.Boolean(string='No Calcula AFP SIS')
    gratificacion_legal = fields.Boolean(string='Gratificación L. Manual')

    isapre_moneda = fields.Selection(
        [('uf', 'UF'), ('clp', 'Pesos')],
        string='Moneda Isapre',
        default='uf'
    )
    aporte_voluntario = fields.Float(
        string='Ahorro Previsional Voluntario (APV)',
        help="Monto mensual pactado como APV"
    )
    aporte_voluntario_moneda = fields.Selection(
        [('uf', 'UF'), ('clp', 'Pesos')],
        string='Moneda APV',
        default='uf'
    )
    forma_pago_apv = fields.Selection(
        [('1', 'Directa'), ('2', 'Indirecta')],
        string='Forma de Pago APV',
        default='1'
    )
    seguro_complementario_moneda = fields.Selection(
        [('uf', 'UF'), ('clp', 'Pesos')],
        string='Moneda Seguro Complementario',
        default='uf'
    )

    complete_name = fields.Char(related='employee_id.firstname', readonly=True, store=True)
    last_name = fields.Char(related='employee_id.last_name', readonly=True, store=True)
