# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError

class ArriendoPortal(http.Controller):

    @http.route(['/my/rentals'], type='http', auth='user', website=True)
    def portal_dashboard(self, **kw):
        user = request.env.user
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        if not subscription:
            return request.render('arriendo_prendas_suscripcion.portal_no_subscription')

        prendas_arrendadas = subscription.x_prendas_en_posesion_ids

        return request.render('arriendo_prendas_suscripcion.portal_dashboard', {
            'subscription': subscription,
            'prendas_arrendadas': prendas_arrendadas,
            'max_prendas': subscription.x_max_prendas_permitidas,
            'cambios_disponibles': subscription.x_cambios_permitidos_mes - subscription.x_cambios_usados_mes,
        })

    @http.route(['/my/rentals/catalog'], type='http', auth='user', website=True)
    def portal_catalogo(self, **kw):
        # Búsqueda simple: solo productos arrendables con stock disponible
        Product = request.env['product.product'].sudo()
        Quant = request.env['stock.quant'].sudo()

        products = Product.search([('x_es_prenda_arrendable', '=', True)])
        stock_quant = Quant.read_group(
            [('product_id', 'in', products.ids), ('quantity', '>', 0)],
            ['product_id'],
            ['product_id']
        )
        stock_product_ids = [res['product_id'][0] for res in stock_quant]
        productos_disponibles = products.filtered(lambda p: p.id in stock_product_ids)

        return request.render('arriendo_prendas_suscripcion.portal_catalogo_arriendo', {
            'productos': productos_disponibles,
        })

    @http.route(['/my/rentals/request_rent'], type='http', auth='user', website=True, methods=['POST'])
    def request_rent(self, **post):
        product_ids = request.httprequest.form.getlist('product_ids')
        if not product_ids:
            return request.redirect('/my/rentals')

        user = request.env.user
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        if not subscription:
            return request.redirect('/my/rentals')

        current_count = subscription.x_cantidad_prendas_en_posesion
        max_allowed = subscription.x_max_prendas_permitidas

        if current_count + len(product_ids) > max_allowed:
            return request.render('arriendo_prendas_suscripcion.portal_limited', {
                'error': _('Superas el máximo permitido de prendas (%s).' % max_allowed)
            })

        # Buscar lotes disponibles por producto
        StockQuant = request.env['stock.quant'].sudo()
        lots = []
        for pid in product_ids:
            quant = StockQuant.search([
                ('product_id', '=', int(pid)),
                ('quantity', '>', 0),
                ('lot_id', '!=', False)
            ], limit=1)
            if quant and quant.lot_id:
                lots.append(quant.lot_id)

        # Crear borrador de picking
        picking_vals = {
            'partner_id': subscription.partner_id.id,
            'picking_type_id': request.env.ref('stock.picking_type_out').id,
            'location_id': request.env.ref('stock.stock_location_stock').id,
            'location_dest_id': subscription.partner_id.property_stock_customer.id,
            'origin': 'Solicitud desde Portal',
            'x_suscripcion_id': subscription.id,
        }

        picking = request.env['stock.picking'].sudo().create(picking_vals)

        for lot in lots:
            picking.move_ids_without_package.create({
                'picking_id': picking.id,
                'product_id': lot.product_id.id,
                'name': lot.product_id.name,
                'product_uom': lot.product_id.uom_id.id,
                'product_uom_qty': 1.0,
            })

        return request.redirect('/my/rentals')

    @http.route(['/my/rentals/request_return'], type='http', auth='user', website=True, methods=['POST'])
    def request_return(self, **post):
        lot_ids = request.httprequest.form.getlist('lot_ids')
        if not lot_ids:
            return request.redirect('/my/rentals')

        user = request.env.user
        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        if not subscription:
            return request.redirect('/my/rentals')

        # Crear picking de devolución
        picking_vals = {
            'partner_id': subscription.partner_id.id,
            'picking_type_id': request.env.ref('stock.picking_type_in').id,
            'location_id': subscription.partner_id.property_stock_customer.id,
            'location_dest_id': request.env.ref('stock.stock_location_stock').id,
            'origin': 'Devolución desde Portal',
            'x_suscripcion_id': subscription.id,
        }

        picking = request.env['stock.picking'].sudo().create(picking_vals)

        for lot_id in lot_ids:
            lot = request.env['stock.production.lot'].sudo().browse(int(lot_id))
            if lot.product_id and lot:
                picking.move_ids_without_package.create({
                    'picking_id': picking.id,
                    'product_id': lot.product_id.id,
                    'name': lot.product_id.name,
                    'product_uom': lot.product_id.uom_id.id,
                    'product_uom_qty': 1.0,
                })

        return request.redirect('/my/rentals')

    @http.route(['/my/rentals/request_change'], type='http', auth='user', website=True, methods=['POST'])
    def request_change(self, **post):
        lot_ids_to_return = request.httprequest.form.getlist('lot_ids_to_return')
        new_product_ids = request.httprequest.form.getlist('new_product_ids')
        user = request.env.user

        subscription = request.env['sale.subscription'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '=', 'open')
        ], limit=1)

        if not subscription:
            return request.redirect('/my/rentals')

        if subscription.x_cambios_usados_mes >= subscription.x_cambios_permitidos_mes:
            return request.render('arriendo_prendas_suscripcion.portal_limited', {
                'error': _('Has alcanzado el límite de cambios permitidos este mes.')
            })

        # Crear devolución
        if lot_ids_to_return:
            return_picking_vals = {
                'partner_id': subscription.partner_id.id,
                'picking_type_id': request.env.ref('stock.picking_type_in').id,
                'location_id': subscription.partner_id.property_stock_customer.id,
                'location_dest_id': request.env.ref('stock.stock_location_stock').id,
                'origin': 'Cambio desde Portal - devolución',
                'x_suscripcion_id': subscription.id,
                'x_es_cambio_prenda': True,
            }

            picking_return = request.env['stock.picking'].sudo().create(return_picking_vals)

            for lot_id in lot_ids_to_return:
                lot = request.env['stock.production.lot'].sudo().browse(int(lot_id))
                picking_return.move_ids_without_package.create({
                    'picking_id': picking_return.id,
                    'product_id': lot.product_id.id,
                    'name': lot.product_id.name,
                    'product_uom': lot.product_id.uom_id.id,
                    'product_uom_qty': 1.0,
                })

        # Crear entrega de nuevas prendas
        if new_product_ids:
            lots = []
            for pid in new_product_ids:
                quant = request.env['stock.quant'].sudo().search([
                    ('product_id', '=', int(pid)),
                    ('quantity', '>', 0),
                    ('lot_id', '!=', False)
                ], limit=1)
                if quant and quant.lot_id:
                    lots.append(quant.lot_id)

            picking_vals = {
                'partner_id': subscription.partner_id.id,
                'picking_type_id': request.env.ref('stock.picking_type_out').id,
                'location_id': request.env.ref('stock.stock_location_stock').id,
                'location_dest_id': subscription.partner_id.property_stock_customer.id,
                'origin': 'Cambio desde Portal - entrega',
                'x_suscripcion_id': subscription.id,
                'x_es_cambio_prenda': True,
            }

            picking = request.env['stock.picking'].sudo().create(picking_vals)

            for lot in lots:
                picking.move_ids_without_package.create({
                    'picking_id': picking.id,
                    'product_id': lot.product_id.id,
                    'name': lot.product_id.name,
                    'product_uom': lot.product_id.uom_id.id,
                    'product_uom_qty': 1.0,
                })

        return request.redirect('/my/rentals')

