# -*- coding: utf-8 -*-
import math
from odoo import api, fields, models

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_continued = fields.Boolean(
        string='Días Corridos (Incluye Fines de Semana)',
        help="Si se marca, el cálculo de días incluirá sábados, domingos y festivos (ignora el calendario laboral)."
    )

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """
        Sobrescribe el cálculo de días de Odoo 19.
        Si el tipo de licencia es 'is_continued', calcula días calendario (corridos).
        De lo contrario, usa el cálculo estándar (días hábiles según calendario).
        """
        # 1. Obtenemos el cálculo estándar de Odoo (Días hábiles)
        # Devuelve un dict: {'days': float, 'hours': float}
        result = super(HrLeave, self)._get_number_of_days(date_from, date_to, employee_id)

        # 2. Verificamos si debemos aplicar la lógica de días corridos
        # Intentamos obtener el tipo de ausencia del registro actual o del contexto
        leave_type = self.holiday_status_id
        if not leave_type and self.env.context.get('default_holiday_status_id'):
            leave_type = self.env['hr.leave.type'].browse(self.env.context.get('default_holiday_status_id'))

        # 3. Aplicamos la lógica personalizada si corresponde
        if leave_type and leave_type.is_continued and date_from and date_to:
            # Cálculo de diferencia matemática pura (Días calendario)
            time_delta = date_to - date_from
            days = math.ceil(time_delta.days + float(time_delta.seconds) / 86400)
            
            # Sobrescribimos la clave 'days' en el resultado
            result['days'] = days
        
        return result
