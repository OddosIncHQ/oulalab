# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.portal.controllers.portal import CustomerPortal

class ArriendoCustomerPortal(CustomerPortal):
    """
    Controlador del portal para la gestión de arriendos por parte del cliente.
    """

    def _get_active_subscription(self):
        """
        Método helper para obtener la suscripción activa del usuario del portal.
        Busca una suscripción que esté en estado 'Venta' (activa).
        """
        return request.env['sale.order'].search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('is_subscription', '=', True),
            ('state', '=', 'sale'), # CORRECCIÓN: Se usa 'state' en lugar de 'stage_category'
        ], limit=1)

    def _prepare_home_portal_values(self, counters):
        """
        Sobrescribe el método estándar del portal para añadir nuestro contador de arriendos.
        """
        values = super(ArriendoCustomerPortal, self)._prepare_home_portal_values(counters)
        
        subscription = self._get_active_subscription()
        values['rental_count'] = subscription.x_cantidad_prendas_en_posesion if subscription else 0
            
        return values

    @http.route(['/my/rentals', '/my/rentals/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_rentals(self, page=1, **kw):
        """
        Muestra el panel principal del portal de arriendos.
        """
        subscription = self._get_active_subscription()
        if not subscription:
            return request.render('arriendo_prendas_suscripcion.portal_no_subscription')

        values = {
            'subscription': subscription,
            'prendas_arrendadas': subscription.x_prendas_en_posesion_ids,
            'page_name': 'rentals',
        }
        return request.render("arriendo_prendas_suscripcion.portal_dashboard", values)

    @http.route(['/my/rentals/catalog'], type='http', auth="user", website=True)
    def portal_catalog(self, **kw):
        """ Muestra el catálogo de prendas disponibles para arrendar. """
        subscription = self._get_active_subscription()
        if not subscription:
            return request.redirect('/my/rentals?error_message=' + _("Necesitas una suscripción activa para ver el catálogo."))

        # Lógica para encontrar productos disponibles
        available_lots = request.env['stock.lot'].sudo().search([
            ('product_id.x_es_prenda_arrendable', '=', True),
            ('quant_ids.quantity', '>', 0),
            ('quant_ids.location_id.usage', '=', 'internal'),
        ])
        rented_lots = request.env['arriendo.prenda.linea'].sudo().search([
            ('estado', '=', 'arrendada'), ('active', '=', True)
        ]).mapped('numero_serie_id')
        
        final_available_lots = available_lots - rented_lots
        available_products = final_available_lots.mapped('product_id')

        values = {
            'productos': available_products,
            'subscription': subscription,
            'prendas_disponibles_para_seleccionar': subscription.x_max_prendas_permitidas - subscription.x_cantidad_prendas_en_posesion,
            'page_name': 'catalog',
        }
        return request.render("arriendo_prendas_suscripcion.portal_catalogo_arriendo", values)

    @http.route('/my/rentals/request', type='http', auth='user', methods=['POST'], website=True)
    def portal_request_rental(self, **post):
        """
        Procesa la solicitud de arriendo desde el catálogo.
        """
        subscription = self._get_active_subscription()
        product_ids = [int(pid) for pid in request.httprequest.form.getlist('product_ids')]

        if not subscription or not product_ids:
            return request.redirect('/my/rentals/catalog')

        try:
            if len(product_ids) > (subscription.x_max_prendas_permitidas - subscription.x_cantidad_prendas_en_posesion):
                raise ValidationError(_("Has seleccionado más prendas de las que tu suscripción permite."))

            picking = subscription.sudo()._create_rental_picking('outgoing', product_ids=product_ids)
            
            return request.redirect('/my/rentals?success_message=' + _("Tu solicitud para %s prenda(s) ha sido creada. El albarán %s está listo para ser procesado.") % (len(product_ids), picking.name))

        except (ValidationError, Exception) as e:
            return request.redirect('/my/rentals/catalog?error_message=' + str(e))

    @http.route('/my/rentals/return', type='http', auth='user', methods=['POST'], website=True)
    def portal_request_return(self, **post):
        """
        Procesa la solicitud de devolución.
        """
        subscription = self._get_active_subscription()
        lot_ids = [int(lid) for lid in request.httprequest.form.getlist('lot_ids')]

        if not subscription or not lot_ids:
            return request.redirect('/my/rentals')

        try:
            picking = subscription.sudo()._create_rental_picking('incoming', lot_ids=lot_ids)

            return request.redirect('/my/rentals?success_message=' + _("Tu solicitud de devolución para %s prenda(s) ha sido creada. El albarán %s está listo para ser procesado.") % (len(lot_ids), picking.name))

        except (ValidationError, Exception) as e:
            return request.redirect('/my/rentals?error_message=' + str(e))
