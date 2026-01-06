# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from urllib.request import urlopen
from bs4 import BeautifulSoup

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MONTH_LIST = [
    ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'),
    ('4', 'Abril'), ('5', 'Mayo'), ('6', 'Junio'),
    ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Septiembre'),
    ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
]

class HrIndicadoresPrevisionales(models.Model):
    _name = 'hr.indicadores'
    _description = 'Indicadores Previsionales Chile'
    _order = 'year desc, month desc'

    name = fields.Char(string='Nombre', compute='_compute_name', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Validado'),
    ], string='Estado', readonly=True, default='draft')

    # Asignación Familiar
    asignacion_familiar_primer = fields.Float(string='Asignación Familiar Tramo 1', readonly=True)
    asignacion_familiar_segundo = fields.Float(string='Asignación Familiar Tramo 2', readonly=True)
    asignacion_familiar_tercer = fields.Float(string='Asignación Familiar Tramo 3', readonly=True)
    
    asignacion_familiar_monto_a = fields.Float(string='Monto Tramo A', readonly=True)
    asignacion_familiar_monto_b = fields.Float(string='Monto Tramo B', readonly=True)
    asignacion_familiar_monto_c = fields.Float(string='Monto Tramo C', readonly=True)

    # Seguro de Cesantía
    contrato_plazo_fijo_empleador = fields.Float(string='Contrato Plazo Fijo Empleador', readonly=True)
    contrato_plazo_fijo_trabajador = fields.Float(string='Contrato Plazo Fijo Trabajador', readonly=True)
    contrato_plazo_indefinido_empleador = fields.Float(string='Contrato Plazo Indefinido Empleador', readonly=True)
    contrato_plazo_indefinido_empleador_otro = fields.Float(string='Contrato Plazo Indefinido 11 años+', readonly=True)
    contrato_plazo_indefinido_trabajador = fields.Float(string='Contrato Plazo Indefinido Trabajador', readonly=True)
    contrato_plazo_indefinido_trabajador_otro = fields.Float(string='Contrato Plazo Indefinido 11 años+ Trabajador', readonly=True)

    # Otros Indicadores
    caja_compensacion = fields.Float(string='Caja Compensación', readonly=True)
    deposito_convenido = fields.Float(string='Depósito Convenido (UF)', readonly=True)
    fonasa = fields.Float(string='Fonasa (%)', readonly=True)
    mutual_seguridad = fields.Float(string='Mutualidad (%)', readonly=True)
    isl = fields.Float(string='ISL (%)', readonly=True)
    pensiones_ips = fields.Float(string='Pensiones IPS (%)', readonly=True)
    
    sueldo_minimo = fields.Float(string='Sueldo Mínimo', readonly=True)
    sueldo_minimo_otro = fields.Float(string='Sueldo Mínimo (<18 y >65)', readonly=True)

    # Tasas AFP
    tasa_afp_cuprum = fields.Float(string='Tasa Cuprum', readonly=True)
    tasa_afp_capital = fields.Float(string='Tasa Capital', readonly=True)
    tasa_afp_provida = fields.Float(string='Tasa ProVida', readonly=True)
    tasa_afp_modelo = fields.Float(string='Tasa Modelo', readonly=True)
    tasa_afp_planvital = fields.Float(string='Tasa PlanVital', readonly=True)
    tasa_afp_habitat = fields.Float(string='Tasa Habitat', readonly=True)
    tasa_afp_uno = fields.Float(string='Tasa Uno', readonly=True, help="AFP Uno")

    # Tasas SIS
    tasa_sis_cuprum = fields.Float(string='SIS Cuprum', readonly=True)
    tasa_sis_capital = fields.Float(string='SIS Capital', readonly=True)
    tasa_sis_provida = fields.Float(string='SIS Provida', readonly=True)
    tasa_sis_planvital = fields.Float(string='SIS PlanVital', readonly=True)
    tasa_sis_habitat = fields.Float(string='SIS Habitat', readonly=True)
    tasa_sis_modelo = fields.Float(string='SIS Modelo', readonly=True)
    tasa_sis_uno = fields.Float(string='SIS Uno', readonly=True)

    # Tasas Independientes
    tasa_independiente_cuprum = fields.Float(string='Independientes Cuprum', readonly=True)
    tasa_independiente_capital = fields.Float(string='Independientes Capital', readonly=True)
    tasa_independiente_provida = fields.Float(string='Independientes Provida', readonly=True)
    tasa_independiente_planvital = fields.Float(string='Independientes PlanVital', readonly=True)
    tasa_independiente_habitat = fields.Float(string='Independientes Habitat', readonly=True)
    tasa_independiente_modelo = fields.Float(string='Independientes Modelo', readonly=True)
    tasa_independiente_uno = fields.Float(string='Independientes Uno', readonly=True)

    # Topes
    tope_anual_apv = fields.Float(string='Tope Anual APV (UF)', readonly=True)
    tope_mensual_apv = fields.Float(string='Tope Mensual APV (UF)', readonly=True)
    tope_imponible_afp = fields.Float(string='Tope Imponible AFP (UF)', readonly=True)
    tope_imponible_ips = fields.Float(string='Tope Imponible IPS (UF)', readonly=True)
    tope_imponible_salud = fields.Float(string='Tope Imponible Salud (UF)', readonly=True)
    tope_imponible_seguro_cesantia = fields.Float(string='Tope Seguro Cesantía (UF)', readonly=True)

    # Valores Moneda
    uf = fields.Float(string='UF', required=True, readonly=True)
    utm = fields.Float(string='UTM', required=True, readonly=True)
    uta = fields.Float(string='UTA', readonly=True)
    uf_otros = fields.Float(string='UF (Día Pago)', readonly=True)
    
    # Configuración
    mutualidad_id = fields.Many2one('hr.mutual', string='Mutual', readonly=True)
    ccaf_id = fields.Many2one('hr.ccaf', string='CCAF', readonly=True)
    
    month = fields.Selection(MONTH_LIST, string='Mes', required=True, default=str(datetime.now().month))
    year = fields.Integer(string='Año', required=True, default=datetime.now().year)
    
    gratificacion_legal = fields.Boolean(string='Gratificación Legal Manual', readonly=True)
    mutual_seguridad_bool = fields.Boolean(string='Cotiza Mutual', default=True, readonly=True)
    ipc = fields.Float(string='IPC (%)', readonly=True)

    @api.depends('month', 'year')
    def _compute_name(self):
        for rec in self:
            if rec.month and rec.year:
                month_name = dict(MONTH_LIST).get(rec.month, '')
                rec.name = f"{month_name} {rec.year}"
            else:
                rec.name = "Nuevo Indicador"

    def action_done(self):
        self.write({'state': 'done'})
        return True

    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    def update_document(self):
        """
        Conecta a Previred y extrae los indicadores.
        """
        for rec in self:
            try:
                # Helper functions internas
                def clear_string(cad):
                    if not cad: return "0"
                    cad = cad.replace(".", '').replace("$", '').replace(" ", '')
                    cad = cad.replace("Renta", '').replace("<", '').replace(">", '')
                    cad = cad.replace("=", '').replace("R", '').replace("I", '').replace("%", '')
                    cad = cad.replace(",", '.')
                    cad = cad.replace("1ff8", '')
                    return cad

                def string_divide(cad, cad2, rounded):
                    if not cad or not cad2: return 0.0
                    return round(float(cad) / float(cad2), rounded)

                # Request a Previred
                # Nota: Previred cambia su HTML a menudo. Si falla, verificar los selectores.
                url = 'https://www.previred.com/web/previred/indicadores-previsionales'
                with urlopen(url) as response:
                    html_doc = response.read()
                
                soup = BeautifulSoup(html_doc, 'html.parser')
                tables = soup.find_all("table")

                if not tables:
                    raise UserError("No se encontraron tablas en Previred. La estructura web puede haber cambiado.")

                # 1. UF - UTM - UTA
                # Tabla 0 = UF, Tabla 1 = UTM/UTA
                rec.uf = float(clear_string(tables[0].select("strong")[1].get_text()))
                rec.utm = float(clear_string(tables[1].select("strong")[3].get_text()))
                rec.uta = float(clear_string(tables[1].select("strong")[4].get_text()))

                # 2. Rentas Topes (Tabla 2)
                rec.tope_imponible_afp = string_divide(clear_string(tables[2].select("strong")[1].get_text()), rec.uf, 2)
                rec.tope_imponible_ips = string_divide(clear_string(tables[2].select("strong")[2].get_text()), rec.uf, 2)
                rec.tope_imponible_seguro_cesantia = string_divide(clear_string(tables[2].select("strong")[3].get_text()), rec.uf, 2)
                rec.tope_imponible_salud = rec.tope_imponible_afp # Usualmente el mismo

                # 3. Sueldo Mínimo (Tabla 3)
                rec.sueldo_minimo = float(clear_string(tables[3].select("strong")[1].get_text()))
                rec.sueldo_minimo_otro = float(clear_string(tables[3].select("strong")[2].get_text()))

                # 4. APV (Tabla 4)
                rec.tope_mensual_apv = string_divide(clear_string(tables[4].select("strong")[2].get_text()), rec.uf, 2)
                rec.tope_anual_apv = string_divide(clear_string(tables[4].select("strong")[1].get_text()), rec.uf, 2)

                # 5. Depósito Convenido (Tabla 5)
                rec.deposito_convenido = string_divide(clear_string(tables[5].select("strong")[1].get_text()), rec.uf, 2)

                # 6. Seguro Cesantía Tasas (Tabla 6)
                rec.contrato_plazo_indefinido_empleador = float(clear_string(tables[6].select("strong")[5].get_text()))
                rec.contrato_plazo_indefinido_trabajador = float(clear_string(tables[6].select("strong")[6].get_text()))
                rec.contrato_plazo_fijo_empleador = float(clear_string(tables[6].select("strong")[7].get_text()))
                # rec.contrato_plazo_fijo_trabajador = 0.0 # Siempre es 0

                # 7. Tasas AFP (Tabla 7)
                # OJO: Los índices de las tablas pueden variar si Previred agrega una AFP (ej: AFP Uno)
                # Se recomienda validar los índices manualmente si esto falla.
                
                # Ejemplo genérico (Capital)
                rec.tasa_afp_capital = float(clear_string(tables[7].select("strong")[8].get_text()))
                rec.tasa_sis_capital = float(clear_string(tables[7].select("strong")[9].get_text()))
                
                # Cuprum
                rec.tasa_afp_cuprum = float(clear_string(tables[7].select("strong")[11].get_text()))
                rec.tasa_sis_cuprum = float(clear_string(tables[7].select("strong")[12].get_text()))
                
                # Habitat
                rec.tasa_afp_habitat = float(clear_string(tables[7].select("strong")[14].get_text()))
                rec.tasa_sis_habitat = float(clear_string(tables[7].select("strong")[15].get_text()))
                
                # PlanVital
                rec.tasa_afp_planvital = float(clear_string(tables[7].select("strong")[17].get_text()))
                rec.tasa_sis_planvital = float(clear_string(tables[7].select("strong")[18].get_text()))
                
                # ProVida
                rec.tasa_afp_provida = float(clear_string(tables[7].select("strong")[20].get_text()))
                rec.tasa_sis_provida = float(clear_string(tables[7].select("strong")[21].get_text()))
                
                # Modelo
                rec.tasa_afp_modelo = float(clear_string(tables[7].select("strong")[23].get_text()))
                rec.tasa_sis_modelo = float(clear_string(tables[7].select("strong")[24].get_text()))
                
                # AFP Uno (Agregar si la tabla lo permite, usualmente indices 26 y 27)
                # rec.tasa_afp_uno = float(clear_string(tables[7].select("strong")[26].get_text()))

                # 8. Asignación Familiar (Tabla 8)
                rec.asignacion_familiar_monto_a = float(clear_string(tables[8].select("strong")[4].get_text()))
                rec.asignacion_familiar_primer = float(clear_string(tables[8].select("strong")[5].get_text())[1:]) # Quitamos el simbolo <
                
                rec.asignacion_familiar_monto_b = float(clear_string(tables[8].select("strong")[6].get_text()))
                rec.asignacion_familiar_segundo = float(clear_string(tables[8].select("strong")[7].get_text())[6:]) # Quitamos el simbolo >
                
                rec.asignacion_familiar_monto_c = float(clear_string(tables[8].select("strong")[8].get_text()))
                rec.asignacion_familiar_tercer = float(clear_string(tables[8].select("strong")[9].get_text())[6:])

            except Exception as e:
                _logger.error(f"Error al actualizar indicadores desde Previred: {str(e)}")
                raise UserError(f"No se pudieron obtener los datos de Previred. La estructura de la página podría haber cambiado.\nError técnico: {e}")
