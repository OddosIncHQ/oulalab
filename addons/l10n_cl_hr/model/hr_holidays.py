import math
from odoo import api, fields, models


class HRHolidaysStatus(models.Model):
    _inherit = 'hr.leave.type'

    is_continued = fields.Boolean(string='Descontar Fines de Semana')


class HRHolidays(models.Model):
    _inherit = 'hr.leave'

    def _get_duration(self, date_from, date_to, employee_id):
        """Cálculo personalizado de duración de licencia."""
        self.ensure_one()
        if self.holiday_status_id.is_continued:
            time_delta = date_to - date_from
            return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)
        return super()._get_duration(date_from, date_to, employee_id)
