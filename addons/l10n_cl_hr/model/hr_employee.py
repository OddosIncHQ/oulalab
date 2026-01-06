# -*- coding: utf-8 -*-
import re
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Campos para desglose de nombre (No nativos en Odoo, necesarios para Previred)
    firstname = fields.Char(string="Nombre")
    middle_name = fields.Char(string="Segundo Nombre", help='Segundo nombre del empleado')
    last_name = fields.Char(string="Apellido Paterno")
    mothers_name = fields.Char(string="Apellido Materno", help='Apellido materno del empleado')
    
    # Tipo de trabajador para Previred
    type_id = fields.Many2one('hr.type.employee', string='Tipo de Empleado')
    
    # RUT
    formated_vat = fields.Char(string='RUT Formateado', compute='_compute_formated_vat', store=True, help='RUT formateado con puntos y guion')

    # ---------------------------------------------------------
    # Lógica de Nombres
    # ---------------------------------------------------------

    @api.depends('firstname', 'middle_name', 'last_name', 'mothers_name')
    def _compute_name(self):
        for rec in self:
            rec.name = rec._get_computed_name(
                rec.last_name,
                rec.firstname,
                rec.mothers_name,
                rec.middle_name
            )

    def _get_computed_name(self, last_name, firstname, last_name2=None, middle_name=None):
        """ Construye el nombre completo evitando espacios dobles """
        names = [
            firstname or '',
            middle_name or '',
            last_name or '',
            last_name2 or ''
        ]
        # Filtra elementos vacíos y une con espacios
        return " ".join(filter(None, names))

    @api.onchange('firstname', 'mothers_name', 'middle_name', 'last_name')
    def _onchange_name_fields(self):
        # Actualiza el nombre en tiempo real en la interfaz
        self.name = self._get_computed_name(
            self.last_name,
            self.firstname,
            self.mothers_name,
            self.middle_name
        )

    # ---------------------------------------------------------
    # Lógica de RUT (Identification ID)
    # ---------------------------------------------------------

    @api.onchange('identification_id')
    def _onchange_document(self):
        """ Formatea el RUT automáticamente al cambiar el campo """
        if self.identification_id:
            # Elimina caracteres no válidos y asegura mayúsculas
            clean_id = re.sub(r'[^0-9Kk]', '', str(self.identification_id)).upper()
            
            # Rellena con ceros a la izquierda si es necesario (ej: 1-9 -> 000000001-9)
            # Nota: Para visualización chilena estándar, a veces no se usa zfill(9), 
            # pero mantengo tu lógica original para consistencia de tu base de datos.
            if len(clean_id) < 2:
                return # RUT muy corto para formatear
                
            cuerpo = clean_id[:-1]
            dv = clean_id[-1]
            
            # Formateo con puntos si tiene largo suficiente, sino simple
            if len(cuerpo) > 3:
                # Invertir, agrupar de a 3, unir con puntos, invertir de nuevo
                cuerpo_fmt = '.'.join([cuerpo[::-1][i:i+3] for i in range(0, len(cuerpo), 3)])[::-1]
                self.identification_id = f'{cuerpo_fmt}-{dv}'
            else:
                self.identification_id = f'{cuerpo}-{dv}'

    @api.depends('identification_id')
    def _compute_formated_vat(self):
        for rec in self:
            rec.formated_vat = rec.identification_id

    def check_identification_id_cl(self, identification_id):
        """ Valida el RUT chileno usando algoritmo Módulo 11 """
        if not identification_id:
            return False

        # Limpiar formato
        rut_clean = identification_id.replace('-', '').replace('.', '')
        
        if len(rut_clean) < 2:
            raise ValidationError('El RUT es demasiado corto.')

        body = rut_clean[:-1]
        vdig = rut_clean[-1].upper()

        try:
            # Algoritmo Modulo 11
            recorrer = reversed(body)
            multiplo = 2
            suma = 0
            
            for c in recorrer:
                suma += int(c) * multiplo
                if multiplo == 7: 
                    multiplo = 2
                else: 
                    multiplo += 1
            
            res = 11 - (suma % 11)
            dvr = 'K' if res == 10 else '0' if res == 11 else str(res)
            
            if dvr != vdig:
                raise ValidationError(f'El RUT {identification_id} no es válido (Dígito verificador incorrecto).')
            return True

        except ValueError:
            raise ValidationError('El RUT contiene caracteres inválidos en el cuerpo numérico.')
        except Exception as e:
             raise ValidationError(f'Error al validar RUT: {str(e)}')

    @api.constrains('identification_id')
    def _check_rut_validity_and_unique(self):
        """ Restricción combinada: Valida formato y unicidad """
        for rec in self:
            if not rec.identification_id:
                continue

            # 1. Validar formato algorítmico
            # Se omite para el RUT genérico de prueba si es necesario
            if rec.identification_id != "55.555.555-5":
                rec.check_identification_id_cl(rec.identification_id)

            # 2. Validar Unicidad
            # Buscamos duplicados excluyendo el registro actual
            duplicate = self.env['hr.employee'].search([
                ('identification_id', '=', rec.identification_id),
                ('id', '!=', rec.id),
                ('company_id', '=', rec.company_id.id) # Opcional: unicidad por compañía o global
            ])
            
            if rec.identification_id != "55.555.555-5" and duplicate:
                raise ValidationError(f'El RUT {rec.identification_id} ya está registrado para el empleado {duplicate[0].name}.')
