import re
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    firstname = fields.Char(string="Nombre")
    last_name = fields.Char(string="Apellido Paterno")
    middle_name = fields.Char(string="Segundo Nombre", help='Segundo nombre del empleado')
    mothers_name = fields.Char(string="Apellido Materno", help='Apellido materno del empleado')
    type_id = fields.Many2one('hr.type.employee', string='Tipo de Empleado')
    formated_vat = fields.Char(string='RUT Formateado', store=True, help='RUT formateado con puntos y guion')

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
        names = []
        if firstname:
            names.append(firstname)
        if middle_name:
            names.append(middle_name)
        if last_name:
            names.append(last_name)
        if last_name2:
            names.append(last_name2)
        return " ".join(names)

    @api.onchange('firstname', 'mothers_name', 'middle_name', 'last_name')
    def _onchange_name_fields(self):
        if self.firstname and self.last_name:
            self.name = self._get_computed_name(
                self.last_name,
                self.firstname,
                self.mothers_name,
                self.middle_name
            )

    @api.onchange('identification_id')
    def _onchange_document(self):
        if self.identification_id:
            clean_id = re.sub('[^1234567890Kk]', '', str(self.identification_id)).zfill(9).upper()
            self.identification_id = '%s.%s.%s-%s' % (
                clean_id[0:2], clean_id[2:5], clean_id[5:8], clean_id[-1]
            )

    def check_identification_id_cl(self, identification_id):
        body, vdig = '', ''
        if len(identification_id) > 9:
            identification_id = identification_id.replace('-', '', 1).replace('.', '', 2)
        if len(identification_id) != 9:
            raise UserError('El RUT no tiene formato válido')
        else:
            body, vdig = identification_id[:-1], identification_id[-1].upper()
        try:
            vali = list(range(2, 8)) + [2, 3]  # ✅ Fix para Python 3
            operar = '0123456789K0'[11 - (
                sum([int(d) * f for d, f in zip(body[::-1], vali)]) % 11)]
            if operar == vdig:
                return True
            else:
                raise UserError('El RUT no tiene formato válido')
        except IndexError:
            raise UserError('El RUT no tiene formato válido')

    @api.constrains('identification_id')
    def _rut_unique(self):
        for rec in self:
            if not rec.identification_id:
                continue
            duplicate = self.env['hr.employee'].search([
                ('identification_id', '=', rec.identification_id),
                ('id', '!=', rec.id)
            ])
            if rec.identification_id != "55.555.555-5" and duplicate:
                raise UserError('El RUT debe ser único')

