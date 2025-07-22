# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError # Importar ValidationError para mensajes más específicos


class ArriendoPortal(http.Controller):

    @http.route(['/my/rentals'], type='http', auth='user', website=True)
    def portal_dashboard(self, **kw):
        user = request.env.user
        # Siempre es buena práctica intentar buscar la suscripción sin sudo() primero
        # y luego usar sudo() si se requiere acceso a campos no públicos o para operaciones internas.
        # Aquí, como es para el propio usuario, no debería necesitar sudo, pero el modelo sale.subscription
        # puede tener reglas de registro que lo requieran para el portal. Lo mantendremos así por ahora.
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        # Si no hay suscripción activa, redirigir a una página informativa o de error.
        # La plantilla 'portal_no_subscription' es una buena idea.
        if not subscription:
            return request.render('arriendo_prendas_suscripcion.portal_no_subscription', {
                'error_message': _("No tienes una suscripción de arriendo de prendas activa.")
            })

        # Las prendas en posesión ya están filtradas por el dominio del One2many en el modelo.
        prendas_arrendadas = subscription.x_prendas_en_posesion_ids

        return request.render('arriendo_prendas_suscripcion.portal_dashboard', {
            'subscription': subscription,
            'prendas_arrendadas': prendas_arrendadas,
            'max_prendas': subscription.x_max_prendas_permitidas,
            'cambios_disponibles': subscription.x_cambios_permitidos_mes - subscription.x_cambios_usados_mes,
            # Añadir aquí cualquier otro dato relevante para el dashboard.
        })

    @http.route(['/my/rentals/catalog'], type='http', auth='user', website=True)
    def portal_catalogo(self, **kw):
        Product = request.env['product.product'].sudo()
        Quant = request.env['stock.quant'].sudo()

        # Filtrar por productos que son "prendas arrendables"
        products = Product.search([('x_es_prenda_arrendable', '=', True)])

        # Usar read_group para obtener la cantidad disponible por producto que tiene un número de serie.
        # Es crucial que las prendas arrendables sean productos con números de serie.
        stock_quant_groups = Quant.read_group(
            [('product_id', 'in', products.ids), ('quantity', '>', 0), ('lot_id', '!=', False)],
            ['product_id', 'quantity:sum'], # Pedir la suma de cantidad
            ['product_id']
        )
        
        # Crear un diccionario para un acceso más fácil {product_id: available_qty}
        available_products_qty = {res['product_id'][0]: res['quantity'] for res in stock_quant_groups}
        
        # Filtrar los productos para mostrar solo aquellos que tienen stock disponible
        productos_disponibles = products.filtered(lambda p: available_products_qty.get(p.id, 0) > 0)
        
        # Obtener la suscripción del usuario para mostrar límites en el catálogo
        user = request.env.user
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        return request.render('arriendo_prendas_suscripcion.portal_catalogo_arriendo', {
            'productos': productos_disponibles,
            'subscription': subscription, # Pasar la suscripción para mostrar límites en el catálogo
            'max_prendas_permitidas': subscription.x_max_prendas_permitidas if subscription else 0,
            'current_prendas_en_posesion': subscription.x_cantidad_prendas_en_posesion if subscription else 0,
        })

    @http.route(['/my/rentals/request_rent'], type='http', auth='user', website=True, methods=['POST'])
    def request_rent(self, **post):
        # Asegurarse de que product_ids sea una lista de enteros
        product_ids = [int(p_id) for p_id in request.httprequest.form.getlist('product_ids') if p_id.isdigit()]
        
        if not product_ids:
            # Redirigir con un mensaje de error si no se seleccionó nada
            return request.redirect('/my/rentals?error_message=%s' % _("Debes seleccionar al menos una prenda para arrendar."))

        user = request.env.user
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        if not subscription:
            return request.redirect('/my/rentals?error_message=%s' % _("No tienes una suscripción activa para realizar esta acción."))

        current_count = subscription.x_cantidad_prendas_en_posesion
        max_allowed = subscription.x_max_prendas_permitidas

        # Validación temprana de límites (antes de buscar lotes y crear pickings)
        # Esto previene la creación de pickings innecesarios si el límite se excede.
        if current_count + len(product_ids) > max_allowed:
            return request.redirect('/my/rentals?error_message=%s' % _('Superas el máximo permitido de prendas (%s) para tu suscripción. Tienes %s y quieres añadir %s.') % (max_allowed, current_count, len(product_ids)))

        # Buscar lotes disponibles por producto
        StockQuant = request.env['stock.quant'].sudo()
        lots = request.env['stock.production.lot'] # Colección vacía de lotes
        for pid in product_ids:
            # Buscar el primer lote disponible para el producto.
            # Se asume que el stock.quant solo tiene una unidad por lot_id.
            quant = StockQuant.search([
                ('product_id', '=', pid),
                ('quantity', '>', 0),
                ('lot_id', '!=', False)
            ], order='create_date asc', limit=1) # Tomar el más antiguo para FIFO

            if quant and quant.lot_id:
                # Comprobar que el lote no esté ya "arrendado" por otra suscripción (a través de arriendo.prenda.linea activa)
                # Esta es una validación crítica para evitar asignar el mismo lote dos veces.
                existing_rent_line = request.env['arriendo.prenda.linea'].sudo().search([
                    ('numero_serie_id', '=', quant.lot_id.id),
                    ('estado', '=', 'arrendada'),
                    ('active', '=', True)
                ], limit=1)
                if existing_rent_line:
                    # Esto no debería pasar si el filtro de catálogo es correcto, pero es una buena salvaguarda.
                    return request.redirect('/my/rentals?error_message=%s' % _('La prenda "%s" (Serie: %s) ya está arrendada por otro cliente. Por favor, selecciona otra.') % (quant.product_id.display_name, quant.lot_id.display_name))
                
                lots += quant.lot_id # Añadir lote a la colección de lotes a mover
            else:
                # Esto significa que una prenda seleccionada ya no tiene stock o lote.
                # Redirigir con error y mensaje útil.
                product_name = request.env['product.product'].sudo().browse(pid).display_name
                return request.redirect('/my/rentals?error_message=%s' % _('La prenda "%s" no está disponible actualmente. Por favor, revisa tu selección.') % product_name)

        # Crear borrador de picking
        # Odoo requiere 'move_ids_without_package' o 'move_lines' para crear el picking con movimientos.
        # Aquí lo haremos creando los movimientos después de crear el picking, es más controlable.
        picking_vals = {
            'partner_id': subscription.partner_id.id,
            'picking_type_id': request.env.ref('stock.picking_type_out').id,
            'location_id': request.env.ref('stock.stock_location_stock').id, # Origen: Tu almacén principal
            'location_dest_id': subscription.partner_id.property_stock_customer.id, # Destino: Ubicación del cliente
            'origin': 'Solicitud de Arriendo desde Portal - Suscripción %s' % subscription.name,
            'x_suscripcion_id': subscription.id,
        }

        try:
            picking = request.env['stock.picking'].sudo().create(picking_vals)
            
            # Crear los movimientos del picking
            for lot in lots:
                request.env['stock.move'].sudo().create({
                    'picking_id': picking.id,
                    'product_id': lot.product_id.id,
                    'name': lot.product_id.name,
                    'product_uom': lot.product_id.uom_id.id,
                    'product_uom_qty': 1.0, # Asumimos una prenda por lote
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'origin_returned_move_id': False, # No es una devolución de movimiento original
                    'move_line_ids': [(0, 0, { # Crear la línea de movimiento con el lote asignado directamente
                        'product_id': lot.product_id.id,
                        'product_uom_id': lot.product_id.uom_id.id,
                        'qty_done': 0, # Se llenará al validar el picking si se usa 'set_quantities_to_reserve'
                        'lot_id': lot.id,
                        'location_id': picking.location_id.id,
                        'location_dest_id': picking.location_dest_id.id,
                    })]
                })
            
            # Validar el picking si quieres que se procese automáticamente, o dejarlo en borrador.
            # Si lo dejas en borrador, tu equipo debe validarlo manualmente.
            # pickings.action_confirm() # Confirmar el picking
            # pickings.action_assign()  # Reservar cantidades
            # pickings.button_validate() # Validar el picking (mover stock)

            request.session['rental_success_message'] = _("Tu solicitud de arriendo ha sido enviada con éxito. Será procesada a la brevedad.")
            return request.redirect('/my/rentals')

        except ValidationError as e:
            # Capturar errores de validación de Odoo (ej. de _check_subscription_limits en stock.picking)
            request.session['rental_error_message'] = e.name
            return request.redirect('/my/rentals')
        except Exception as e:
            # Capturar cualquier otro error inesperado
            request.session['rental_error_message'] = _("Ocurrió un error al procesar tu solicitud: %s" % str(e))
            return request.redirect('/my/rentals')

    @http.route(['/my/rentals/request_return'], type='http', auth='user', website=True, methods=['POST'])
    def request_return(self, **post):
        lot_ids_str = request.httprequest.form.getlist('lot_ids')
        lot_ids = [int(l_id) for l_id in lot_ids_str if l_id.isdigit()]

        if not lot_ids:
            return request.redirect('/my/rentals?error_message=%s' % _("Debes seleccionar al menos una prenda para devolver."))

        user = request.env.user
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        if not subscription:
            return request.redirect('/my/rentals?error_message=%s' % _("No tienes una suscripción activa para realizar esta acción."))

        # Asegurarse de que los lotes pertenecen a la suscripción actual y están en estado 'arrendada'
        # Esto previene devoluciones de prendas que no corresponden o ya fueron devueltas
        valid_lots_to_return = request.env['arriendo.prenda.linea'].sudo().search([
            ('suscripcion_id', '=', subscription.id),
            ('numero_serie_id', 'in', lot_ids),
            ('estado', '=', 'arrendada'),
            ('active', '=', True)
        ]).mapped('numero_serie_id')

        if len(valid_lots_to_return) != len(lot_ids):
             return request.redirect('/my/rentals?error_message=%s' % _("Una o más prendas seleccionadas para devolver no están en tu posesión o no son válidas."))

        # Crear picking de devolución (entrada)
        picking_vals = {
            'partner_id': subscription.partner_id.id,
            'picking_type_id': request.env.ref('stock.picking_type_in').id, # Tipo de operación de entrada
            'location_id': subscription.partner_id.property_stock_customer.id, # Origen: Ubicación del cliente
            'location_dest_id': request.env.ref('stock.stock_location_stock').id, # Destino: Tu almacén principal
            'origin': 'Devolución desde Portal - Suscripción %s' % subscription.name,
            'x_suscripcion_id': subscription.id,
            # 'x_es_cambio_prenda': False, # No es un cambio en sí mismo, solo una devolución
        }

        try:
            picking = request.env['stock.picking'].sudo().create(picking_vals)
            
            # Crear los movimientos del picking
            for lot in valid_lots_to_return:
                request.env['stock.move'].sudo().create({
                    'picking_id': picking.id,
                    'product_id': lot.product_id.id,
                    'name': lot.product_id.name,
                    'product_uom': lot.product_id.uom_id.id,
                    'product_uom_qty': 1.0, # Asumimos una prenda por lote
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'move_line_ids': [(0, 0, { # Crear la línea de movimiento con el lote asignado
                        'product_id': lot.product_id.id,
                        'product_uom_id': lot.product_id.uom_id.id,
                        'qty_done': 0, # Se llenará al validar el picking
                        'lot_id': lot.id,
                        'location_id': picking.location_id.id,
                        'location_dest_id': picking.location_dest_id.id,
                    })]
                })

            # pickings.action_confirm()
            # pickings.action_assign()
            # pickings.button_validate()

            request.session['rental_success_message'] = _("Tu solicitud de devolución ha sido enviada con éxito. Será procesada a la brevedad.")
            return request.redirect('/my/rentals')

        except ValidationError as e:
            request.session['rental_error_message'] = e.name
            return request.redirect('/my/rentals')
        except Exception as e:
            request.session['rental_error_message'] = _("Ocurrió un error al procesar tu solicitud de devolución: %s" % str(e))
            return request.redirect('/my/rentals')


    @http.route(['/my/rentals/request_change'], type='http', auth='user', website=True, methods=['POST'])
    def request_change(self, **post):
        lot_ids_to_return_str = request.httprequest.form.getlist('lot_ids_to_return')
        new_product_ids_str = request.httprequest.form.getlist('new_product_ids')
        
        lot_ids_to_return = [int(l_id) for l_id in lot_ids_to_return_str if l_id.isdigit()]
        new_product_ids = [int(p_id) for p_id in new_product_ids_str if p_id.isdigit()]

        user = request.env.user
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        if not subscription:
            return request.redirect('/my/rentals?error_message=%s' % _("No tienes una suscripción activa para realizar esta acción."))

        # Validación del límite de cambios mensuales
        if subscription.x_cambios_usados_mes >= subscription.x_cambios_permitidos_mes:
            return request.redirect('/my/rentals?error_message=%s' % _('Has alcanzado el límite de cambios permitidos este mes para tu suscripción.'))

        # Validar que la cantidad de prendas a devolver sea igual a la cantidad de prendas nuevas a recibir
        if len(lot_ids_to_return) != len(new_product_ids):
            return request.redirect('/my/rentals?error_message=%s' % _('Debes devolver la misma cantidad de prendas que solicitas nuevas para un cambio.'))

        # Validar que los lotes a devolver realmente pertenezcan a la suscripción activa del cliente
        valid_lots_to_return = request.env['arriendo.prenda.linea'].sudo().search([
            ('suscripcion_id', '=', subscription.id),
            ('numero_serie_id', 'in', lot_ids_to_return),
            ('estado', '=', 'arrendada'),
            ('active', '=', True)
        ]).mapped('numero_serie_id')

        if len(valid_lots_to_return) != len(lot_ids_to_return):
            return request.redirect('/my/rentals?error_message=%s' % _("Una o más prendas seleccionadas para devolver no están en tu posesión o no son válidas."))

        try:
            # Paso 1: Crear el picking de DEVOLUCIÓN (entrada)
            if lot_ids_to_return:
                return_picking_vals = {
                    'partner_id': subscription.partner_id.id,
                    'picking_type_id': request.env.ref('stock.picking_type_in').id,
                    'location_id': subscription.partner_id.property_stock_customer.id,
                    'location_dest_id': request.env.ref('stock.stock_location_stock').id,
                    'origin': 'Cambio desde Portal - devolución de Suscripción %s' % subscription.name,
                    'x_suscripcion_id': subscription.id,
                    'x_es_cambio_prenda': True, # Marcar como parte de un cambio
                }

                picking_return = request.env['stock.picking'].sudo().create(return_picking_vals)

                for lot in valid_lots_to_return:
                    request.env['stock.move'].sudo().create({
                        'picking_id': picking_return.id,
                        'product_id': lot.product_id.id,
                        'name': lot.product_id.name,
                        'product_uom': lot.product_id.uom_id.id,
                        'product_uom_qty': 1.0,
                        'location_id': picking_return.location_id.id,
                        'location_dest_id': picking_return.location_dest_id.id,
                        'move_line_ids': [(0, 0, {
                            'product_id': lot.product_id.id,
                            'product_uom_id': lot.product_id.uom_id.id,
                            'qty_done': 0,
                            'lot_id': lot.id,
                            'location_id': picking_return.location_id.id,
                            'location_dest_id': picking_return.location_dest_id.id,
                        })]
                    })

            # Paso 2: Crear el picking de ENTREGA de nuevas prendas (salida)
            if new_product_ids:
                lots_for_new_items = request.env['stock.production.lot']
                for pid in new_product_ids:
                    quant = request.env['stock.quant'].sudo().search([
                        ('product_id', '=', pid),
                        ('quantity', '>', 0),
                        ('lot_id', '!=', False)
                    ], order='create_date asc', limit=1)
                    if quant and quant.lot_id:
                        # Revalidación de disponibilidad para la nueva prenda
                        existing_rent_line = request.env['arriendo.prenda.linea'].sudo().search([
                            ('numero_serie_id', '=', quant.lot_id.id),
                            ('estado', '=', 'arrendada'),
                            ('active', '=', True)
                        ], limit=1)
                        if existing_rent_line:
                            return request.redirect('/my/rentals?error_message=%s' % _('La nueva prenda "%s" (Serie: %s) no está disponible. Por favor, selecciona otra.') % (quant.product_id.display_name, quant.lot_id.display_name))
                        
                        lots_for_new_items += quant.lot_id
                    else:
                        product_name = request.env['product.product'].sudo().browse(pid).display_name
                        return request.redirect('/my/rentals?error_message=%s' % _('La nueva prenda "%s" no está disponible actualmente. Por favor, revisa tu selección de cambio.') % product_name)
                
                # Asegurarse de que tenemos un lote por cada producto nuevo solicitado
                if len(lots_for_new_items) != len(new_product_ids):
                    return request.redirect('/my/rentals?error_message=%s' % _('No se encontraron todas las prendas nuevas solicitadas para el cambio. Por favor, revisa tu selección.'))


                picking_delivery_vals = {
                    'partner_id': subscription.partner_id.id,
                    'picking_type_id': request.env.ref('stock.picking_type_out').id,
                    'location_id': request.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': subscription.partner_id.property_stock_customer.id,
                    'origin': 'Cambio desde Portal - entrega de Suscripción %s' % subscription.name,
                    'x_suscripcion_id': subscription.id,
                    'x_es_cambio_prenda': True, # Marcar como parte de un cambio
                }

                picking_delivery = request.env['stock.picking'].sudo().create(picking_delivery_vals)

                for lot in lots_for_new_items:
                    request.env['stock.move'].sudo().create({
                        'picking_id': picking_delivery.id,
                        'product_id': lot.product_id.id,
                        'name': lot.product_id.name,
                        'product_uom': lot.product_id.uom_id.id,
                        'product_uom_qty': 1.0,
                        'location_id': picking_delivery.location_id.id,
                        'location_dest_id': picking_delivery.location_dest_id.id,
                        'move_line_ids': [(0, 0, {
                            'product_id': lot.product_id.id,
                            'product_uom_id': lot.product_id.uom_id.id,
                            'qty_done': 0,
                            'lot_id': lot.id,
                            'location_id': picking_delivery.location_id.id,
                            'location_dest_id': picking_delivery.location_dest_id.id,
                        })]
                    })

            request.session['rental_success_message'] = _("Tu solicitud de cambio ha sido enviada con éxito. Será procesada a la brevedad.")
            return request.redirect('/my/rentals')

        except ValidationError as e:
            request.session['rental_error_message'] = e.name
            return request.redirect('/my/rentals')
        except Exception as e:
            request.session['rental_error_message'] = _("Ocurrió un error al procesar tu solicitud de cambio: %s" % str(e))
            return request.redirect('/my/rentals')
