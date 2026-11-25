from datetime import timedelta
from odoo import api, fields, models
from .res_partner import parse_bo_iso_datetime


class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    x_bo_showroom_uuid = fields.Char(
        string='UUID Showroom BackOffice',
        index=True,
        help='Identificador UUID del Showroom exportado en el CSV de citas de OulaLab.',
    )


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    x_bo_appointment_key = fields.Char(
        string='Clave Única Cita BO',
        index=True,
        copy=False,
        readonly=True,
    )
    x_bo_status = fields.Selection(
        [
            ('confirmed', 'Confirmada'),
            ('cancelled', 'Cancelada'),
            ('completed', 'Realizada'),
            ('no_show', 'No Asistió'),
        ],
        string='Estado Cita BO',
        copy=False,
    )
    x_bo_created_at = fields.Datetime(string='Fecha Alta Cita BO', readonly=True, copy=False)

    @api.model
    def upsert_from_bo_appointment(self, row, dry_run=False):
        start_str = (row.get('Inicio') or '').strip()
        status_raw = (row.get('Estado') or 'confirmed').strip().lower()
        client_name = (row.get('Cliente') or '').strip()
        email = (row.get('Email') or '').strip().lower()
        showroom_uuid = (row.get('Showroom') or '').strip()
        created_at_str = (row.get('Fecha de alta') or '').strip()

        start_dt, _ = parse_bo_iso_datetime(start_str)
        if not start_dt:
            return 'skipped', self.browse(), f"Fecha de inicio inválida: {start_str}"

        created_dt, _ = parse_bo_iso_datetime(created_at_str)
        appt_key = f"{email or client_name}|{start_dt.strftime('%Y-%m-%d %H:%M:%S')}|{showroom_uuid}"

        showroom_info = self.env['oulalab.bo.showroom.map'].resolve_showroom(showroom_uuid)
        appt_type = showroom_info['appointment_type']
        responsible_user = showroom_info['user']
        duration_hours = showroom_info['duration']
        stop_dt = start_dt + timedelta(hours=duration_hours)

        Partner = self.env['res.partner']
        partner = Partner._find_bo_partner(email=email, name=client_name)
        if not partner and (email or client_name) and not dry_run:
            chile = self.env.ref('base.cl', raise_if_not_found=False)
            partner = Partner.create({
                'name': client_name or email,
                'email': email or False,
                'company_type': 'person',
                'country_id': chile.id if chile else False,
                'lang': 'es_CL',
                'tz': 'America/Santiago',
            })

        lead = self.env['crm.lead'].browse()
        if email:
            lead = self.env['crm.lead'].search(
                ['|', ('email_normalized', '=', email), ('email_from', '=ilike', email)],
                order='id desc',
                limit=1,
            )

        existing = self.with_context(active_test=False).search(
            [('x_bo_appointment_key', '=', appt_key)], limit=1
        )

        is_cancelled = status_raw in ('cancelled', 'canceled', 'cancelada')
        bo_status = 'cancelled' if is_cancelled else (
            status_raw if status_raw in ('confirmed', 'completed', 'no_show') else 'confirmed'
        )
        base_title = appt_type.name if appt_type else 'Visita Showroom OulaLab'
        event_name = f"{base_title} - {client_name or email}"

        partner_ids = []
        if partner:
            partner_ids.append(partner.id)
        if responsible_user and responsible_user.partner_id:
            partner_ids.append(responsible_user.partner_id.id)

        vals = {
            'name': event_name,
            'start': start_dt,
            'stop': stop_dt,
            'x_bo_status': bo_status,
            'active': not is_cancelled,
            'user_id': responsible_user.id if responsible_user else self.env.user.id,
        }
        if appt_type:
            vals['appointment_type_id'] = appt_type.id
            if appt_type.location_id:
                vals['location'] = appt_type.location_id.name
        if created_dt:
            vals['x_bo_created_at'] = created_dt
        if lead:
            vals['opportunity_id'] = lead.id
        if partner_ids:
            vals['partner_ids'] = [(6, 0, list(set(partner_ids)))]

        if existing:
            if not dry_run:
                existing.with_context(active_test=False).write(vals)
                if is_cancelled and partner:
                    existing.attendee_ids.filtered(lambda a: a.partner_id == partner).write({'state': 'declined'})
            return 'updated', existing, f"Cita actualizada ({event_name} [{bo_status}])"

        vals['x_bo_appointment_key'] = appt_key
        if not dry_run:
            existing = self.create(vals)
            if not is_cancelled and partner:
                existing.attendee_ids.filtered(lambda a: a.partner_id == partner).write({'state': 'accepted'})
            elif is_cancelled and partner:
                existing.attendee_ids.filtered(lambda a: a.partner_id == partner).write({'state': 'declined'})
        return 'created', existing, f"Cita creada ({event_name} [{bo_status}])"
