# -*- coding: utf-8 -*-
import io
import csv
import base64
import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WizardExportCsvPrevired(models.TransientModel):
    _name = 'wizard.export.csv.previred'
    _description = 'Asistente Exportación Previred'

    # Mapeos de configuración
    DELIMITER_MAP = {
        'comma': ',',
        'dot_coma': ';',
        'tab': '\t',
    }
    QUOTE_MAP = {
        'colon': '"',
        'semicolon': "'",
        'none': '',
    }

    # Campos del Wizard
    date_from = fields.Date(string='Fecha Inicial', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Fecha Final', required=True, 
                          default=lambda self: fields.Date.context_today(self) + relativedelta(day=31))
    
    file_data = fields.Binary(string='Archivo Generado', readonly=True)
    file_name = fields.Char(string='Nombre de archivo')
    
    delimiter_option = fields.Selection([
        ('colon', 'Comillas Dobles (")'),
        ('semicolon', "Comillas Simples (')"),
        ('none', "Ninguno"),
    ], string='Encapsulado de Texto', default='none', required=True)
    
    delimiter_field_option = fields.Selection([
        ('comma', 'Coma (,)'),
        ('dot_coma', "Punto y coma (;)"),
        ('tab', "Tabulador"),
    ], string='Separador de Campos', default='dot_coma', required=True)

    def show_view(self, name):
        """ Retorna la acción para abrir el wizard nuevamente con el archivo generado """
        return {
            'name': name,
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'wizard.export.csv.previred',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # -------------------------------------------------------------------------
    # HELPERS DE LÓGICA DE NEGOCIO
    # -------------------------------------------------------------------------

    def get_nacionalidad(self, employee):
        # 0 chileno (CL), 1 extranjero
        if not employee.country_id:
            return 0
        return 0 if employee.country_id.code == 'CL' else 1

    def get_tipo_pago(self, employee):
        # 01: Remuneraciones, 02: Gratificaciones, etc.
        # Por defecto Previred usa 1 para sueldos normales
        return 1

    def get_regimen_provisional(self, contract):
        # SIP (Ex-INP) o AFP
        return 'SIP' if contract.pension else 'AFP'

    def get_tipo_trabajador(self, employee):
        # Retorna el código Previred almacenado en hr.type.employee
        if not employee.type_id:
            return 0 # Por defecto Activo
        return employee.type_id.id_type

    def get_dias_trabajados(self, payslip):
        """ Obtiene días trabajados (WORK100) """
        for line in payslip.worked_days_line_ids:
            if line.code == 'WORK100':
                return int(line.number_of_days)
        return 0

    def get_cost_center(self, contract):
        if contract.analytic_account_id:
            return contract.analytic_account_id.code or "0"
        return "0"

    def get_tipo_linea(self, payslip):
        # 00: Principal
        return '00'

    def get_tramo_asignacion_familiar(self, payslip, total_imponible):
        """ Calcula el tramo A, B, C, D basado en los indicadores del mes """
        indicadores = payslip.l10n_cl_indicadores_id
        if not indicadores:
            return 'D'

        if payslip.contract_id.carga_familiar > 0 and not payslip.contract_id.pension:
            if total_imponible <= indicadores.asignacion_familiar_primer:
                return 'A'
            elif total_imponible <= indicadores.asignacion_familiar_segundo:
                return 'B'
            elif total_imponible <= indicadores.asignacion_familiar_tercer:
                return 'C'
        
        return 'D'

    def get_rule_value(self, payslip, code):
        """ Obtiene el valor de una regla salarial (Optimizado en memoria) """
        line = payslip.line_ids.filtered(lambda l: l.code == code)
        return int(round(sum(line.mapped('total')))) if line else 0

    # -------------------------------------------------------------------------
    # CALCULOS DE TOPES (IMPONIBLES)
    # -------------------------------------------------------------------------

    def get_tope_afp(self, payslip, imponible):
        indicadores = payslip.l10n_cl_indicadores_id
        if not indicadores: 
            return int(imponible)

        tope_pesos = round(indicadores.tope_imponible_afp * indicadores.uf)
        
        if payslip.contract_id.pension:
            return 0
        
        if imponible >= tope_pesos:
            return int(tope_pesos)
        return int(imponible)

    def get_tope_seguro_cesantia(self, payslip, imponible):
        indicadores = payslip.l10n_cl_indicadores_id
        if not indicadores: 
            return int(imponible)
            
        tope_pesos = round(indicadores.tope_imponible_seguro_cesantia * indicadores.uf)

        if payslip.contract_id.pension or payslip.contract_id.contract_type_id.name == 'Sueldo Empresarial':
            return 0
            
        if imponible >= tope_pesos:
            return int(tope_pesos)
        return int(imponible)

    def get_tope_salud(self, payslip, imponible):
        # El tope de salud es el mismo que el de AFP (7% sobre tope imponible)
        indicadores = payslip.l10n_cl_indicadores_id
        if not indicadores: 
            return int(imponible)
            
        tope_pesos = round(indicadores.tope_imponible_afp * indicadores.uf)
        
        if imponible >= tope_pesos:
            return int(tope_pesos)
        return int(imponible)

    # -------------------------------------------------------------------------
    # UTILIDADES STRING
    # -------------------------------------------------------------------------
    def _clean_str(self, text, size=None):
        """ Limpia caracteres especiales y acorta """
        if not text:
            return ""
        
        replacements = (
            ('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ñ', 'n'),
            ('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ó', 'O'), ('Ú', 'U'), ('Ñ', 'N')
        )
        for a, b in replacements:
            text = text.replace(a, b)
        
        text = text.upper().strip()
        if size:
            return text[:size]
        return text

    def _clean_rut(self, rut_text):
        """ Retorna tupla (Cuerpo, DV) """
        if not rut_text:
            return "0", "0"
        
        clean = rut_text.replace('.', '').replace(',', '')
        if '-' in clean:
            parts = clean.split('-')
            return parts[0], parts[1]
        return clean, ""

    # -------------------------------------------------------------------------
    # GENERACION PRINCIPAL
    # -------------------------------------------------------------------------
    def action_generate_csv(self):
        self.ensure_one()
        payslip_obj = self.env['hr.payslip']
        
        # Buscar nóminas confirmadas en el rango
        domain = [
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('state', '=', 'done'),
            ('company_id', '=', self.env.company.id)
        ]
        payslips = payslip_obj.search(domain)

        if not payslips:
            raise UserError(_("No se encontraron nóminas confirmadas ('Hecho') para el periodo seleccionado."))

        # Configuración del CSV
        output = io.StringIO()
        delimiter = self.DELIMITER_MAP.get(self.delimiter_field_option, ';')
        quotechar = self.QUOTE_MAP.get(self.delimiter_option, '')
        quoting = csv.QUOTE_MINIMAL if quotechar else csv.QUOTE_NONE
        
        writer = csv.writer(output, delimiter=delimiter, quotechar=quotechar, quoting=quoting)

        # Datos Empresa
        company_rut, company_dv = self._clean_rut(self.env.company.vat)
        
        # Formatos de fecha para Previred
        # Se usa el mes de la fecha final para determinar el periodo (mmaaaa)
        periodo_remuneracion = self.date_to.strftime("%m%Y")
        
        sexo_map = {'male': "M", 'female': "F"}

        for slip in payslips:
            employee = slip.employee_id
            contract = slip.contract_id
            indicadores = slip.l10n_cl_indicadores_id
            
            # Si no tiene indicadores asociados, alerta o saltar (aquí continuamos con 0)
            if not indicadores:
                _logger.warning("Nomina %s no tiene indicadores asociados", slip.name)

            rut_emp, rut_dv = self._clean_rut(employee.identification_id)

            # Valores calculados
            total_imponible = self.get_rule_value(slip, 'TOTIM')
            total_haberes = self.get_rule_value(slip, 'HAB')
            
            # Topes
            imponible_afp = self.get_tope_afp(slip, total_imponible)
            imponible_salud = self.get_tope_salud(slip, total_imponible)
            imponible_sc = self.get_tope_seguro_cesantia(slip, total_imponible)
            imponible_mutual = imponible_afp # Generalmente usa el mismo tope que AFP

            # Fechas Movimiento
            fecha_inicio_mp = "00/00/0000"
            fecha_fin_mp = "00/00/0000"
            if slip.movimientos_personal != '0':
                if slip.date_start_mp:
                    fecha_inicio_mp = slip.date_start_mp.strftime("%d/%m/%Y")
                if slip.date_end_mp:
                    fecha_fin_mp = slip.date_end_mp.strftime("%d/%m/%Y")
            
            # Lógica Asignación Familiar
            tramo_asig = self.get_tramo_asignacion_familiar(slip, total_imponible)
            monto_asig_fam = self.get_rule_value(slip, 'ASIGFAM')

            # --- CONSTRUCCIÓN DE LA FILA (105 CAMPOS) ---
            row = []
            
            # 1. RUT Trabajador
            row.append(self._clean_str(rut_emp, 11))
            # 2. DV Trabajador
            row.append(self._clean_str(rut_dv, 1))
            # 3. Apellido Paterno
            row.append(self._clean_str(employee.last_name, 30))
            # 4. Apellido Materno
            row.append(self._clean_str(employee.mothers_name, 30))
            # 5. Nombres
            row.append("%s %s" % (self._clean_str(employee.firstname, 15), self._clean_str(employee.middle_name, 15)))
            # 6. Sexo
            row.append(sexo_map.get(employee.gender, ""))
            # 7. Nacionalidad
            row.append(self.get_nacionalidad(employee))
            # 8. Tipo Pago
            row.append(self.get_tipo_pago(employee))
            # 9. Periodo Desde (mmaaaa)
            row.append(self.date_from.strftime("%m%Y"))
            # 10. Periodo Hasta (mmaaaa)
            row.append(periodo_remuneracion)
            # 11. Regimen Previsional (AFP/SIP)
            row.append(self.get_regimen_provisional(contract))
            # 12. Tipo Trabajador (Pensionado, Activo, etc)
            row.append(self.get_tipo_trabajador(employee))
            # 13. Dias Trabajados
            row.append(self.get_dias_trabajados(slip))
            # 14. Tipo de Linea
            row.append(self.get_tipo_linea(slip))
            # 15. Código Movimiento Personal
            row.append(slip.movimientos_personal)
            # 16. Fecha Desde Movimiento
            row.append(fecha_inicio_mp)
            # 17. Fecha Hasta Movimiento
            row.append(fecha_fin_mp)
            # 18. Tramo Asig Familiar
            row.append(tramo_asig)
            # 19. Cargas Simples
            row.append(contract.carga_familiar)
            # 20. Cargas Maternales
            row.append(contract.carga_familiar_maternal)
            # 21. Cargas Invalidas
            row.append(contract.carga_familiar_invalida)
            # 22. Asignacion Familiar Monto
            row.append(monto_asig_fam)
            # 23. Asig Fam Retroactiva
            row.append("0")
            # 24. Reintegro Cargas
            row.append("0")
            # 25. Solicitud Trabajador Joven
            row.append("N") # Por defecto N
            
            # --- AFP ---
            # 26. Código AFP
            row.append(contract.afp_id.code or "0")
            # 27. Renta Imponible AFP
            row.append(imponible_afp)
            # 28. Cotización Obligatoria AFP
            row.append(self.get_rule_value(slip, 'PREV')) # REGLA 'PREV' = Cotizacion AFP
            # 29. Cotización SIS
            row.append(self.get_rule_value(slip, 'SIS'))
            # 30. Cuenta Ahorro AFP
            row.append("0")
            # 31. Renta Imp. Sust.
            row.append("0")
            # 32. Tasa Pactada Sust.
            row.append("0")
            # 33. Aporte Indemn Sust.
            row.append("0")
            # 34. N Periodos Sust.
            row.append("0")
            # 35. Desde Sust.
            row.append("0")
            # 36. Hasta Sust.
            row.append("0")
            # 37. Puesto Pesado
            row.append("")
            # 38. % Pesado
            row.append("0")
            # 39. Cotiz Pesado
            row.append("0")
            
            # --- APV ---
            monto_apv = self.get_rule_value(slip, 'APV')
            has_apv = monto_apv > 0
            
            # 40. Cod Inst APV
            row.append(contract.apv_id.codigo if has_apv else "0")
            # 41. Numero Contrato APV
            row.append("0")
            # 42. Forma Pago APV
            row.append(contract.forma_pago_apv if has_apv else "0")
            # 43. Monto APV
            row.append(monto_apv)
            # 44. Cotiz Depositos
            row.append("0")
            
            # --- APVC (Colectivo) - Relleno 0 ---
            row.append("0") # 45
            row.append("")  # 46
            row.append("0") # 47
            row.append("0") # 48
            row.append("0") # 49
            
            # --- Afiliado Voluntario (Relleno) ---
            row.append("0") # 50
            row.append("")  # 51
            row.append("")  # 52
            row.append("")  # 53
            row.append("")  # 54
            row.append("0") # 55
            row.append("00") # 56
            row.append("0") # 57
            row.append("0") # 58
            row.append("0") # 59
            row.append("0") # 60
            row.append("0") # 61
            row.append("0") # 62
            
            # --- EX-CAJAS (IPS) ---
            # Si es Fonasa (cod 07) asumimos IPS en este ejemplo simplificado, 
            # o si el regimen es SIP. Ajustar segun logica real.
            is_ips = contract.isapre_id.code == '07'
            
            # 63. Codigo Ex-Caja
            row.append("0") 
            # 64. Tasa Ex-Caja
            row.append("0")
            # 65. Renta Imponible IPS
            row.append(total_imponible if is_ips else "0")
            # 66. Cotizacion IPS
            row.append("0") # Calcular si aplica
            # 67. Renta Imp Desahucio
            row.append("0")
            # 68. Codigo Desahucio
            row.append("0")
            # 69. Tasa Desahucio
            row.append("0")
            # 70. Cotiz Desahucio
            row.append("0")
            
            # 71. Cotizacion Fonasa
            # Si es IPS/Fonasa, el valor va aquí
            row.append(self.get_rule_value(slip, 'FONASA') if is_ips else "0")
            
            # 72. Cotizacion Acc Trabajo (ISL)
            # Si no tiene mutual, paga ISL
            monto_isl = self.get_rule_value(slip, 'ISL')
            row.append(monto_isl)
            
            # 73. Bonif Ley 15386
            row.append("0")
            # 74. Desc Cargas ISL
            row.append("0")
            # 75. Bonos Gobierno
            row.append("0")
            
            # --- SALUD (ISAPRE) ---
            # 76. Codigo Isapre
            row.append(contract.isapre_id.code or "00")
            # 77. FUN
            row.append(contract.isapre_fun or "")
            # 78. Renta Imponible Isapre
            row.append(imponible_salud if not is_ips else "0")
            # 79. Moneda Plan (1=Peso, 2=UF)
            row.append("2" if not is_ips else "1")
            # 80. Cotizacion Pactada
            row.append(contract.isapre_cotizacion_uf if not is_ips else "0")
            # 81. Cotizacion Obligatoria (7%)
            row.append(self.get_rule_value(slip, 'SALUD') if not is_ips else "0")
            # 82. Cotizacion Adicional Voluntaria
            row.append(self.get_rule_value(slip, 'ADISA') if not is_ips else "0")
            # 83. Monto GES
            row.append("0")
            
            # --- CCAF ---
            # 84. Codigo CCAF
            row.append(indicadores.ccaf_id.code or "00")
            # 85. Renta Imp CCAF
            row.append(imponible_afp if self.get_dias_trabajados(slip) > 0 else "0")
            # 86. Creditos Personales CCAF
            row.append(self.get_rule_value(slip, 'PCCAF'))
            # 87. Desc Dental
            row.append("0")
            # 88. Leasing
            row.append("0")
            # 89. Seguro Vida
            row.append("0")
            # 90. Otros CCAF
            row.append("0")
            # 91. Cotiz CCAF (No afiliados Isapre)
            row.append(self.get_rule_value(slip, 'CAJACOMP'))
            # 92. Desc Cargas CCAF
            row.append("0")
            # 93. Otros 1
            row.append("0")
            # 94. Otros 2
            row.append("0")
            # 95. Bonos Gob
            row.append("0")
            
            # --- MUTUAL ---
            # 96. Cod Sucursal
            row.append("")
            # 97. Codigo Mutual
            row.append(indicadores.mutualidad_id.code or "00")
            # 98. Renta Imp Mutual
            row.append(imponible_mutual)
            # 99. Cotiz Accidente Trabajo
            row.append(self.get_rule_value(slip, 'MUT'))
            # 100. Cod Sucursal
            row.append("0")
            
            # --- SEGURO CESANTIA ---
            # 101. Renta Imp SC
            row.append(imponible_sc)
            # 102. Aporte Trabajador
            row.append(self.get_rule_value(slip, 'SECE'))
            # 103. Aporte Empleador
            row.append(self.get_rule_value(slip, 'SECEEMP'))
            
            # --- OTROS ---
            # 104. Rut Pagadora Subsidio (Relleno)
            row.append("0")
            # 105. DV Pagadora
            row.append("")
            # 106. Centro de Costo
            row.append(self.get_cost_center(contract))
            
            # Convertir todo a string y escribir
            writer.writerow([str(x) for x in row])

        # Finalizar y guardar
        csv_content = output.getvalue()
        self.write({
            'file_data': base64.encodebytes(csv_content.encode('utf-8')),
            'file_name': 'Previred_%s.txt' % self.date_to.strftime('%Y%m')
        })
        
        output.close()
        return self.show_view(_('Archivo Previred Generado'))
