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
            # Solo aplicar la validación a albaranes de salida que tienen una suscripción asociada.
            if picking.picking_type_id.code != 'outgoing' or not picking.x_suscripcion_id:
                continue

            suscripcion = picking.x_suscripcion_id

            # Calcular el total de prendas salientes en este picking que son arrendables.
            # Usamos `move_line_ids_without_package` para las cantidades reales procesadas (`qty_done`)
            # o `move_ids_without_package` para las cantidades planificadas (`product_uom_qty`).
            # Si esta validación se ejecuta *antes* de que el picking esté 'done',
            # `product_uom_qty` es más apropiado para la planificación.
            # Si se ejecuta *después* de la validación, `qty_done` de `move_line_ids_without_package` es lo correcto.
            # Asumiendo que esta es una validación PRE-VALIDACIÓN del picking:
            prendas_salientes = sum(
                move.product_uom_qty # Usar product_uom_qty para la cantidad planificada en el movimiento.
                for move in picking.move_ids_without_package
                if move.product_id.x_es_prenda_arrendable
            )

            # Para una validación más precisa al momento de la confirmación (done),
            # podrías usar `move_line_ids_without_package` y `qty_done`.
            # Sin embargo, `@api.constrains` se dispara en CREATE/WRITE, no necesariamente al 'done'.
            # La lógica actual con `product_uom_qty` es válida para una validación en borrador/confirmación.

            # `x_cantidad_prendas_en_posesion` debe ser un campo computado en la suscripción
            # que refleje el número actual de prendas activas arrendadas.
            total_post_envio = suscripcion.x_cantidad_prendas_en_posesion + prendas_salientes

            if total_post_envio > suscripcion.x_max_prendas_permitidas:
                raise ValidationError(_(
                    'Supera el máximo de prendas permitidas (%s) para esta suscripción (%s). Con este envío, el cliente tendría %s prendas.'
                ) % (suscripcion.x_max_prendas_permitidas, suscripcion.display_name, total_post_envio))

            if picking.x_es_cambio_prenda and \
               suscripcion.x_cambios_usados_mes >= suscripcion.x_cambios_permitidos_mes:
                raise ValidationError(_(
                    'Se ha alcanzado el límite de cambios permitidos este mes para la suscripción %s.'
                ) % suscripcion.display_name)

    def _action_done(self):
        # Llama al método original de Odoo para que el picking se valide correctamente.
        res = super()._action_done()

        for picking in self:
            # Lógica para albaranes de salida (el cliente se lleva la prenda)
            if picking.picking_type_id.code == 'outgoing' and picking.x_suscripcion_id:
                suscripcion = picking.x_suscripcion_id
                for ml in picking.move_line_ids_without_package:
                    # Asegurarse de que la prenda es arrendable y tiene un número de serie asignado
                    if ml.product_id.x_es_prenda_arrendable and ml.lot_id:
                        # Crea una nueva línea de arriendo para la prenda que sale
                        self.env['arriendo.prenda.linea'].create({
                            'suscripcion_id': suscripcion.id,
                            'prenda_id': ml.product_id.id,
                            'numero_serie_id': ml.lot_id.id,
                            'fecha_arriendo': fields.Datetime.now(),
                            'estado': 'arrendada',
                            'active': True,
                        })
                # Incrementa el contador de cambios si es un picking de cambio
                if picking.x_es_cambio_prenda:
                    suscripcion.x_cambios_usados_mes += 1

            # Lógica para albaranes de entrada (el cliente devuelve la prenda)
            elif picking.picking_type_id.code == 'incoming' and picking.x_suscripcion_id:
                suscripcion = picking.x_suscripcion_id
                for ml in picking.move_line_ids_without_package:
                    # Asegurarse de que la prenda es arrendable y tiene un número de serie asignado
                    if ml.product_id.x_es_prenda_arrendable and ml.lot_id:
                        # Busca la línea de arriendo activa para esta prenda y suscripción
                        linea = self.env['arriendo.prenda.linea'].search([
                            ('suscripcion_id', '=', suscripcion.id),
                            ('numero_serie_id', '=', ml.lot_id.id),
                            ('estado', '=', 'arrendada'), # Solo busca las que están actualmente arrendadas
                            ('active', '=', True), # Solo busca las líneas activas
                        ], limit=1) # Solo necesitamos una, la más reciente si hubiera varias por algún error.
                        if linea:
                            # Actualiza el estado y la fecha de devolución, y la inactiva
                            linea.write({
                                'estado': 'devuelta',
                                'fecha_devolucion': fields.Datetime.now(),
                                'active': False, # Marca como inactiva para que no cuente en 'x_cantidad_prendas_en_posesion'
                            })

        return res

