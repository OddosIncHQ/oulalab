from odoo import models, fields, api, _
from odoo.tools import date_utils
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_max_prendas_permitidas = fields.Integer(string='Máx. Prendas Permitidas')
    x_cambios_permitidos_mes = fields.Integer(string='Cambios Permitidos por Mes')
    x_cambios_usados_mes = fields.Integer(string='Cambios Usados este Mes', readonly=True, copy=False)
    x_proxima_fecha_reseteo_cambios = fields.Date(string='Próxima Fecha de Reseteo', readonly=True, copy=False)

    x_prendas_en_posesion_ids = fields.One2many(
        comodel_name='arriendo.prenda.linea',
        inverse_name='suscripcion_id',
        string='Prendas en Posesión del Cliente',
        domain=[('estado', '=', 'arrendada'), ('active', '=', True)],
        readonly=True,
        copy=False
    )
    x_cantidad_prendas_en_posesion = fields.Integer(
        string='Prendas en Posesión',
        compute='_compute_cantidad_prendas',
        store=True,
        help="Cantidad actual de prendas que el cliente tiene arrendadas y activas."
    )

    @api.depends('x_prendas_en_posesion_ids', 'x_prendas_en_posesion_ids.active')
    def _compute_cantidad_prendas(self):
        for suscripcion in self:
            suscripcion.x_cantidad_prendas_en_posesion = len(suscripcion.x_prendas_en_posesion_ids)

    @api.model
    def action_reset_monthly_changes(self):
        _logger.info("Iniciando cron 'action_reset_monthly_changes'...")
        hoy = fields.Date.context_today(self)
        suscripciones_a_resetear = self.search([
            ('is_subscription', '=', True),
            ('stage_category', '=', 'progress'),
            '|',
            ('x_proxima_fecha_reseteo_cambios', '=', False),
            ('x_proxima_fecha_reseteo_cambios', '<=', hoy)
        ])
        for rec in suscripciones_a_resetear:
            nueva_fecha = date_utils.start_of(hoy, 'month') + relativedelta(months=1)
            rec.write({
                'x_cambios_usados_mes': 0,
                'x_proxima_fecha_reseteo_cambios': nueva_fecha
            })
            _logger.info(f"Reset mensual aplicado a la suscripción {rec.name}.")
            rec.message_post(
                body=_(
                    "✔️ El contador de cambios mensuales ha sido reiniciado automáticamente. Próximo reseteo: %s"
                ) % nueva_fecha.strftime('%d/%m/%Y'),
                subtype_xmlid="mail.mt_note"
            )
        _logger.info("Cron 'action_reset_monthly_changes' finalizado.")
