# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Nómina de Sueldo (Chile)'

    # ---------------------------------------------------------
    # Indicadores Previsionales (UF, UTM, Topes)
    # ---------------------------------------------------------
    l10n_cl_indicadores_id = fields.Many2one(
        'hr.indicadores', 
        string='Indicadores Previsionales',
        compute='_compute_indicadores',
        store=True,
        readonly=False,
        help='Indicadores económicos del mes (UF, UTM, Topes) para cálculo de leyes sociales.'
    )
    
    # Guardamos valores clave en la nómina para histórico y reportes
    l10n_cl_uf = fields.Float(string='Valor UF', digits=(16, 2), readonly=True)
    l10n_cl_utm = fields.Float(string='Valor UTM', digits=(16, 2), readonly=True)

    # ---------------------------------------------------------
    # Campos Previred (Movimientos de Personal)
    # ---------------------------------------------------------
    movimientos_personal = fields.Selection([
        ('0', 'Sin Movimiento en el Mes'),
        ('1', 'Contratación a plazo indefinido'),
        ('2', 'Retiro Total'),
        ('3', 'Subsidios (Licencias Médicas)'),
        ('4', 'Permiso Sin Goce de Sueldos'),
        ('5', 'Incorporación en el Lugar de Trabajo'),
        ('6', 'Accidentes del Trabajo'),
        ('7', 'Contratación a plazo fijo'),
        ('8', 'Cambio Contrato plazo fijo a indefinido'),
        ('11', 'Otros Movimientos (Ausentismos)'),
        ('12', 'Reliquidación, Premio, Bono')
    ], string='Código Movimiento Previred', default="0")

    date_start_mp = fields.Date(string='Inicio Movimiento', help="Fecha de inicio del movimiento (ej: inicio licencia)")
    date_end_mp = fields.Date(string='Fin Movimiento', help="Fecha de término del movimiento")

    # ---------------------------------------------------------
    # Lógica de Negocio
    # ---------------------------------------------------------

    @api.depends('date_to', 'date_from')
    def _compute_indicadores(self):
        """ Busca automáticamente los indicadores del mes de la nómina """
        for slip in self:
            if slip.date_to:
                # Busca el indicador donde el mes/año coincida con la fecha fin de la nómina
                indicador = self.env['hr.indicadores'].search([
                    ('month', '=', str(slip.date_to.month)),
                    ('year', '=', slip.date_to.year)
                ], limit=1)
                
                # Si no encuentra exacto, busca el más reciente anterior
                if not indicador:
                    indicador = self.env['hr.indicadores'].search([
                        ('date', '<=', slip.date_to)
                    ], limit=1, order='year desc, month desc')

                slip.l10n_cl_indicadores_id = indicador
                if indicador:
                    slip.l10n_cl_uf = indicador.uf
                    slip.l10n_cl_utm = indicador.utm

    def _get_base_local_dict(self):
        """ 
        Inyecta variables globales en el motor de cálculo de reglas salariales.
        Permite usar 'indicadores', 'uf', 'utm' en las fórmulas Python.
        """
        res = super(HrPayslip, self)._get_base_local_dict()
        if self.l10n_cl_indicadores_id:
            res.update({
                'indicadores': self.l10n_cl_indicadores_id,
                'uf': self.l10n_cl_uf,
                'utm': self.l10n_cl_utm,
                'sueldo_minimo': self.l10n_cl_indicadores_id.sueldo_minimo,
                'tope_afp': self.l10n_cl_indicadores_id.tope_imponible_afp,
                'tope_cesantia': self.l10n_cl_indicadores_id.tope_imponible_seguro_cesantia,
            })
        return res

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        """
        Sobrescribe la generación de días trabajados para aplicar lógica chilena:
        1. Mes Comercial (30 días).
        2. Días Trabajados = 30 - Licencias.
        3. Agrega línea EFF100 (Días efectivos) para cálculo de semana corrida.
        """
        # 1. Obtener cálculo estándar de Odoo (calendario real)
        res = super(HrPayslip, self)._get_worked_day_lines(domain=domain, check_out_of_contract=check_out_of_contract)
        
        # Si no hay resultados, retornar
        if not res:
            return res

        # 2. Separar asistencia (WORK100) de ausencias
        work_line = next((line for line in res if line['code'] == 'WORK100'), None)
        leaves_days = sum(line['number_of_days'] for line in res if line['code'] != 'WORK100')
        
        if work_line:
            real_days = work_line['number_of_days']
            
            # 3. Crear línea de Días Efectivos (EFF100) - Útil para gratificación/semana corrida
            # Usamos una copia para no alterar la referencia original aún
            effective_line = work_line.copy()
            effective_line.update({
                'name': _("Días de trabajo efectivos (Reales)"),
                'code': 'EFF100',
                'sequence': 2, # Aparece después de WORK100
                'number_of_days': real_days,
                # number_of_hours se mantiene igual
            })
            res.append(effective_line)

            # 4. Ajustar WORK100 a base 30 días (Lógica Chile)
            # Si trabajó menos de 30 días reales (ej: entró el día 15), se usa proporcional?
            # La lógica estándar chilena es: 30 - Ausencias.
            # Pero si el contrato empezó a mitad de mes, Odoo ya calcula menos días.
            
            # Si el contrato cubre todo el mes (30 o 31 días), forzamos base 30
            # Si hay ausencias, restamos de 30.
            
            # Ajuste simple: Si días reales > 0, normalizamos a 30 menos licencias
            if real_days > 0:
                # Días comerciales teóricos
                commercial_days = 30 - leaves_days
                
                # Caso febrero o meses de 31 días: Odoo calcula días reales.
                # Si es un mes completo sin ausencias, queremos 30.
                if leaves_days == 0 and real_days >= 28:
                     work_line['number_of_days'] = 30
                
                # Si hay licencias, aseguramos que la suma no exceda 30
                elif leaves_days > 0:
                     # Si la licencia es de 31 días (mes completo), WORK100 debe ser 0.
                     # Odoo ya debería traer 0 en real_days si estuvo ausente todo el mes.
                     if work_line['number_of_days'] > 0:
                         work_line['number_of_days'] = max(0, 30 - leaves_days)

        return res
