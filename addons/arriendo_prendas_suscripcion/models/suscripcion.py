# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import date_utils
from datetime import date


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    x_max_prendas_permitidas = fields.Integer(
        string='Máx. Prendas Permitidas',
        default=0
    )

    x_cambios_permitidos_mes = fields.Integer(
        string='Cambios Permitidos por Mes',
        default=0
    )

    x_cambios_usados_mes = fields.Integer(
        string='Cambios Usados este Mes',
        default=0,
        readonly=True
    )

    x_proxima_fecha_reseteo_cambios = fields.Date(
        string='Próxima Fecha de Reseteo',
        readonly=True
    )

    x_prendas_en_posesion_ids = fields.One2many(
        'arriendo.prenda.linea',
        'suscripcion_id',
        string='Prendas en Posesión',
        domain=[('estado', '=', 'arrendada')]
    )

    x_cantidad_prendas_en_posesion = fields.Integer(
        string='Cantidad de Prendas en Posesión',
        compute='_compute_cantidad_prendas',
        store=True
    )

    @api.depends('x_prendas_en_posesion_ids')
    def _compute_cantidad_prendas(self):
        for rec in self:
            rec.x_cantidad_prendas_en_posesion = len(rec.x_prendas_en_posesion_ids)

    def action_reset_monthly_changes(self):
        """Resetea el contador de cambios mensuales para suscripciones activas ('open')"""
        hoy = fields.Date.context_today(self)
        for rec in self.search([('state', '=', 'open')]):
            rec.write({
                'x_cambios_usados_mes': 0,
                'x_proxima_fecha_reseteo_cambios': date_utils.add(hoy, months=1)
            })
