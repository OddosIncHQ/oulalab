# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import date_utils
from datetime import date # Importar date para operaciones de fecha si se usa directamente.


class SaleSubscription(models.Model):
    _inherit = 'sale.order'

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
        # El dominio ya filtra por 'arrendada', lo cual es bueno.
        # Sin embargo, para la cuenta, es mejor ser explícito con 'active=True'.
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
            # Asegurarse de contar solo las líneas activas que están 'arrendada'.
            # Aunque el dominio del One2many ya filtra por 'arrendada',
            # es una buena práctica ser explícito aquí para la robustez.
            rec.x_cantidad_prendas_en_posesion = len(rec.x_prendas_en_posesion_ids.filtered(lambda l: l.active))

    def action_reset_monthly_changes(self):
        """Resetea el contador de cambios mensuales para suscripciones activas ('open')"""
        # Usar self.env.cr.execute() para un commit explícito no es necesario
        # si la función se llama como un método de modelo normal o desde un cron.
        # Odoo maneja las transacciones.
        
        # Obtener la fecha actual del contexto para consistencia.
        hoy = fields.Date.context_today(self) 
        
        # Calcular el primer día del próximo mes para la próxima fecha de reseteo.
        # Esto asegura que el reseteo siempre sea al inicio del mes siguiente.
        proximo_mes_inicio = date_utils.start_of(hoy, 'month') + date_utils.relativedelta(months=1)

        # Iterar sobre las suscripciones en estado 'open' (activas)
        for rec in self.search([('state', '=', 'open')]):
            # Solo resetear si la próxima fecha de reseteo es hoy o ya pasó,
            # o si nunca se ha establecido (primera vez).
            if not rec.x_proxima_fecha_reseteo_cambios or rec.x_proxima_fecha_reseteo_cambios <= hoy:
                rec.write({
                    'x_cambios_usados_mes': 0,
                    'x_proxima_fecha_reseteo_cambios': proximo_mes_inicio
                })
