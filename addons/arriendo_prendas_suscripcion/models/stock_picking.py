# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_suscripcion_id = fields.Many2one(
        'sale.subscription',
        string='Suscripción'
    )

    x_es_cambio_prenda = fields.Boolean(
        string='Es Cambio de Prenda',
        default=False
    )

    @api.constrains('move_ids_without_package', 'x_suscripcion_id', 'x_es_cambio_prenda')
    def _check_subscription_limits(self):
        for picking in self:
            if picking.picking_type_id.code != 'outgoing' or not picking.x_suscripcion_id:
                continue

            suscripcion = picking.x_suscripcion_id

            # Total de prendas salientes en este picking
            prendas_salientes = sum(
                move.product_uom_qty
                for move in picking.move_ids_without_package
                if move.product_id.x_es_prenda_arrendable
            )

            total_post_envio = suscripcion.x_cantidad_prendas_en_posesion + prendas_salientes

            if total_post_envio > suscripcion.x_max_prendas_permitidas:
                raise ValidationError(_(
                    'Supera el máximo de prendas permitidas (%s) para esta suscripción.'
                ) % suscripcion.x_max_prendas_permitidas)

            if picking.x_es_cambio_prenda and \
               suscripcion.x_cambios_usados_mes >= suscripcion.x_cambios_permitidos_mes:
                raise ValidationError(_(
                    'Se ha alcanzado el límite de cambios permitidos este mes para esta suscripción.'
                ))

    def _action_done(self):
        res = super()._action_done()

        for picking in self:
            if picking.picking_type_id.code == 'outgoing' and picking.x_suscripcion_id:
                suscripcion = picking.x_suscripcion_id
                for ml in picking.move_line_ids_without_package:
                    if ml.product_id.x_es_prenda_arrendable and ml.lot_id:
                        self.env['arriendo.prenda.linea'].create({
                            'suscripcion_id': suscripcion.id,
                            'prenda_id': ml.product_id.id,
                            'numero_serie_id': ml.lot_id.id,
                            'fecha_arriendo': fields.Datetime.now(),
                            'estado': 'arrendada',
                            'active': True,
                        })
                if picking.x_es_cambio_prenda:
                    suscripcion.x_cambios_usados_mes += 1

            elif picking.picking_type_id.code == 'incoming' and picking.x_suscripcion_id:
                suscripcion = picking.x_suscripcion_id
                for ml in picking.move_line_ids_without_package:
                    if ml.product_id.x_es_prenda_arrendable and ml.lot_id:
                        linea = self.env['arriendo.prenda.linea'].search([
                            ('suscripcion_id', '=', suscripcion.id),
                            ('numero_serie_id', '=', ml.lot_id.id),
                            ('estado', '=', 'arrendada'),
                            ('active', '=', True),
                        ], limit=1)
                        if linea:
                            linea.write({
                                'estado': 'devuelta',
                                'fecha_devolucion': fields.Datetime.now(),
                                'active': False,
                            })

        return res
