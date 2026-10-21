# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_suscripcion_id = fields.Many2one(
        'sale.order',
        string='Suscripción Asociada',
        domain="[('partner_id', '=', partner_id), ('is_subscription', '=', True), ('stage_category', '=', 'progress')]",
        help="Vincular este albarán a una suscripción activa del cliente para automatizar el registro del arriendo."
    )
    x_es_cambio_prenda = fields.Boolean(
        string='Es un Cambio de Prenda',
        default=False,
        help="Marcar si este envío cuenta como uno de los cambios mensuales permitidos por la suscripción."
    )

    @api.constrains('move_ids_without_package', 'x_suscripcion_id', 'state')
    def _check_subscription_limits(self):
        for picking in self:
            if picking.state == 'cancel' or picking.picking_type_code != 'outgoing' or not picking.x_suscripcion_id:
                continue

            suscripcion = picking.x_suscripcion_id

            if picking.x_es_cambio_prenda:
                if suscripcion.x_cambios_usados_mes >= suscripcion.x_cambios_permitidos_mes:
                    raise ValidationError(_("Límite de cambios alcanzado para la suscripción %s.") % suscripcion.name)

            prendas_en_este_envio = sum(
                move.product_uom_qty for move in picking.move_ids_without_package
                if move.product_id.x_es_prenda_arrendable
            )

            # Recalcular cantidad real para evitar dependencias inconsistentes
            current_count = self.env['arriendo.prenda.linea'].search_count([
                ('suscripcion_id', '=', suscripcion.id),
                ('estado', '=', 'arrendada'),
                ('active', '=', True),
            ])

            total_post_envio = current_count + prendas_en_este_envio
            if total_post_envio > suscripcion.x_max_prendas_permitidas:
                raise ValidationError(_("Límite de prendas excedido para la suscripción %s.") % suscripcion.name)

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            if not picking.x_suscripcion_id:
                continue

            suscripcion = picking.x_suscripcion_id
            ArriendoLinea = self.env['arriendo.prenda.linea']

            if picking.picking_type_code == 'outgoing':
                if picking.x_es_cambio_prenda:
                    suscripcion.write({'x_cambios_usados_mes': suscripcion.x_cambios_usados_mes + 1})

                for move_line in picking.move_line_ids.filtered(lambda ml: ml.product_id.x_es_prenda_arrendable and ml.lot_id):
                    # Evitar duplicados
                    existing = ArriendoLinea.search_count([
                        ('suscripcion_id', '=', suscripcion.id),
                        ('numero_serie_id', '=', move_line.lot_id.id),
                        ('estado', '=', 'arrendada'),
                        ('active', '=', True),
                    ])
                    if not existing:
                        ArriendoLinea.create({
                            'suscripcion_id': suscripcion.id,
                            'prenda_id': move_line.product_id.id,
                            'numero_serie_id': move_line.lot_id.id,
                            'fecha_arriendo': picking.date_done,
                            'estado': 'arrendada',
                            'active': True,
                        })

            elif picking.picking_type_code == 'incoming':
                for move_line in picking.move_line_ids.filtered(lambda ml: ml.product_id.x_es_prenda_arrendable and ml.lot_id):
                    linea = ArriendoLinea.search([
                        ('suscripcion_id', '=', suscripcion.id),
                        ('numero_serie_id', '=', move_line.lot_id.id),
                        ('estado', '=', 'arrendada'),
                        ('active', '=', True),
                    ], limit=1)
                    if linea:
                        linea.write({
                            'estado': 'devuelta',
                            'fecha_devolucion': picking.date_done,
                            'active': False,
                        })
        return res
