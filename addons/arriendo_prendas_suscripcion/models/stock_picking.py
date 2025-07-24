# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    """
    Hereda de 'stock.picking' (Albaranes) para integrar la lógica de arriendo
    directamente en las operaciones de inventario (envíos y devoluciones).
    """
    _inherit = 'stock.picking'

    x_suscripcion_id = fields.Many2one(
        'sale.order',
        string='Suscripción Asociada',
        # El dominio asegura que solo se muestren suscripciones activas del cliente seleccionado.
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
        """
        Valida antes de confirmar un movimiento que no se excedan los límites de la suscripción.
        Se dispara al añadir/modificar líneas o al asignar una suscripción.
        """
        for picking in self:
            # Aplicar solo a albaranes de SALIDA, que no estén cancelados y tengan una suscripción.
            if picking.state == 'cancel' or picking.picking_type_code != 'outgoing' or not picking.x_suscripcion_id:
                continue

            suscripcion = picking.x_suscripcion_id
            
            # 1. Validar límite de cambios mensuales.
            if picking.x_es_cambio_prenda:
                if suscripcion.x_cambios_usados_mes >= suscripcion.x_cambios_permitidos_mes:
                    raise ValidationError(_(
                        "Límite de cambios alcanzado: La suscripción %s ya ha usado sus %s cambios este mes."
                    ) % (suscripcion.name, suscripcion.x_cambios_permitidos_mes))

            # 2. Validar límite de prendas en posesión.
            # Se calcula sobre la cantidad demandada (product_uom_qty) ya que la validación es antes de procesar.
            prendas_en_este_envio = sum(
                move.product_uom_qty
                for move in picking.move_ids_without_package
                if move.product_id.x_es_prenda_arrendable
            )
            
            total_prendas_post_envio = suscripcion.x_cantidad_prendas_en_posesion + prendas_en_este_envio
            
            if total_prendas_post_envio > suscripcion.x_max_prendas_permitidas:
                raise ValidationError(_(
                    "Límite de prendas excedido: La suscripción %s permite un máximo de %s prendas. "
                    "El cliente ya tiene %s y este envío añadiría %s, resultando en un total de %s."
                ) % (
                    suscripcion.name,
                    suscripcion.x_max_prendas_permitidas,
                    suscripcion.x_cantidad_prendas_en_posesion,
                    prendas_en_este_envio,
                    total_prendas_post_envio
                ))

    def _action_done(self):
        """
        Sobrescribe el método que se ejecuta al validar un albarán.
        Aquí se automatiza la creación y actualización de las líneas de arriendo.
        """
        # Primero, llamar a la lógica original para que el albarán se procese normalmente.
        res = super(StockPicking, self)._action_done()

        # Luego, añadir nuestra lógica personalizada.
        for picking in self:
            if not picking.x_suscripcion_id:
                continue

            suscripcion = picking.x_suscripcion_id
            ArriendoLinea = self.env['arriendo.prenda.linea']

            # --- LÓGICA PARA ENVÍOS (SALIDAS) ---
            if picking.picking_type_code == 'outgoing':
                # Incrementar el contador de cambios si aplica.
                if picking.x_es_cambio_prenda:
                    suscripcion.x_cambios_usados_mes += 1

                # Itera sobre las líneas de movimiento ya procesadas.
                for move_line in picking.move_line_ids.filtered(lambda ml: ml.product_id.x_es_prenda_arrendable and ml.lot_id):
                    ArriendoLinea.create({
                        'suscripcion_id': suscripcion.id,
                        'prenda_id': move_line.product_id.id,
                        'numero_serie_id': move_line.lot_id.id,
                        'fecha_arriendo': picking.date_done, # Usar la fecha de validación del albarán.
                        'estado': 'arrendada',
                        'active': True,
                    })

            # --- LÓGICA PARA DEVOLUCIONES (ENTRADAS) ---
            elif picking.picking_type_code == 'incoming':
                for move_line in picking.move_line_ids.filtered(lambda ml: ml.product_id.x_es_prenda_arrendable and ml.lot_id):
                    # Busca la línea de arriendo activa para esta prenda/serie y suscripción.
                    linea_a_devolver = ArriendoLinea.search([
                        ('suscripcion_id', '=', suscripcion.id),
                        ('numero_serie_id', '=', move_line.lot_id.id),
                        ('estado', '=', 'arrendada'),
                        ('active', '=', True),
                    ], limit=1)
                    
                    if linea_a_devolver:
                        linea_a_devolver.write({
                            'estado': 'devuelta',
                            'fecha_devolucion': picking.date_done, # Usar la fecha de validación del albarán.
                            'active': False, # Se desactiva para que no cuente en el total en posesión.
                        })
        return res

