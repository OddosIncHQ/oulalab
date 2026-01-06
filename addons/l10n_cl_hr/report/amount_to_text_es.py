# -*- coding: utf-8 -*-
import logging
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

#-------------------------------------------------------------
# SPANISH CONVERSION LOGIC
#-------------------------------------------------------------

units_29 = (
    'CERO', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS',
    'SIETE', 'OCHO', 'NUEVE', 'DIEZ', 'ONCE', 'DOCE',
    'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO',
    'DIECINUEVE', 'VEINTE', 'VEINTIÚN', 'VEINTIDÓS', 'VEINTITRÉS', 'VEINTICUATRO',
    'VEINTICINCO', 'VEINTISÉIS', 'VEINTISIETE', 'VEINTIOCHO', 'VEINTINUEVE'
)

tens = (
    'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA', 'CIEN'
)

denom = (
    '',
    'MIL', 'MILLÓN', 'MIL MILLONES', 'BILLÓN', 'MIL BILLONES', 'TRILLÓN', 'MIL TRILLONES',
    'CUATRILLÓN', 'MIL CUATRILLONES', 'QUINTILLÓN', 'MIL QUINTILLONES', 'SEXTILLÓN', 'MIL SEXTILLONES', 'SEPTILLÓN',
    'MIL SEPTILLONES', 'OCTILLÓN', 'MIL OCTILLONES', 'NONILLÓN', 'MIL NONILLONES', 'DECILLÓN', 'MIL DECILLONES'
)

denom_plural = (
    '',
    'MIL', 'MILLONES', 'MIL MILLONES', 'BILLONES', 'MIL BILLONES', 'TRILLONES', 'MIL TRILLONES',
    'CUATRILLONES', 'MIL CUATRILLONES', 'QUINTILLONES', 'MIL QUINTILLONES', 'SEXTILLONES', 'MIL SEXTILLONES', 'SEPTILLONES',
    'MIL SEPTILLONES', 'OCTILLONES', 'MIL OCTILLONES', 'NONILLONES', 'MIL NONILLONES', 'DECILLONES', 'MIL DECILLONES'
)

def _convert_nn(val):
    """ Convierte valores menores a 100 a texto """
    if val < 30:
        return units_29[val]
    for (dcap, dval) in ((k, 30 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + ' Y ' + units_29[val % 10]
            return dcap

def _convert_nnn(val):
    """ Convierte valores menores a 1000 a texto """
    word = ''
    (mod, quotient) = (val % 100, val // 100)
    if quotient > 0:
        if quotient == 1:
            if mod == 0:
                word = 'CIEN'
            else:
                word = 'CIENTO'
        elif quotient == 5:
            word = 'QUINIENTOS'
        elif quotient == 9:
            word = 'NOVECIENTOS'
        else:
            word = units_29[quotient] + 'CIENTOS'
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn(mod)
    return word

def spanish_number(val):
    """ Función principal recursiva para conversión de números enteros """
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    
    # Valores a partir de mil
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)

            # Casos especiales del idioma español
            if l == 1:
                if didx == 1:
                    ret = denom[didx]
                else:
                    ret = _convert_nnn(l) + ' ' + denom[didx]
            else:
                ret = _convert_nnn(l) + ' ' + denom_plural[didx]

            if r > 0:
                ret = ret + ' ' + spanish_number(r)
            return ret

def amount_to_text_es(number, currency):
    """
    Convierte un número a texto incluyendo moneda.
    Soporta decimales (Céntimos/Centavos).
    """
    number = '%.2f' % number
    
    # Normalización básica de moneda
    units_name = currency.upper() if currency else ''
    # Si viene 'CLP', lo pasamos a 'PESO' para que la lógica de plural funcione
    if units_name == 'CLP':
        units_name = 'PESO'
        
    int_part, dec_part = str(number).split('.')
    
    start_word = spanish_number(int(int_part))
    
    # Lógica de Pluralización de la moneda
    # Si termina en vocal (PESO) se agrega S (PESOS)
    # Si termina en consonante (DOLAR) se agrega ES (DOLARES) - Aproximación simple
    final_currency = units_name
    if int(int_part) != 1:
        if not units_name.endswith('S'):
            final_currency += 'S'
    
    final_result = start_word + ' ' + final_currency

    # Manejo de Decimales
    if int(dec_part) > 0:
        end_word = spanish_number(int(dec_part))
        cents_number = int(dec_part)
        cents_name = 'CÉNTIMOS' if cents_number > 1 else 'CÉNTIMO'
        
        # En Chile no se usan centimos habitualmente, pero el reporte podría requerirlo
        final_result += ' CON ' + end_word + ' ' + cents_name
        
    return final_result

#-------------------------------------------------------------
# Generic functions interface
#-------------------------------------------------------------

_translate_funcs = {'es': amount_to_text_es}

def amount_to_text(nbr, lang='es', currency='euros'):
    """
    Converts an integer to its textual representation, using the language set in the context if any.
    Example:
        1654: thousands six cent cinquante-quatre.
    """
    if lang not in _translate_funcs:
        _logger.warning("No translation function found for lang: '%s', defaulting to 'es'", lang)
        lang = 'es'
    
    return _translate_funcs[lang](abs(nbr), currency)
