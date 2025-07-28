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
        """
        return request.env['sale.order'].search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('is_subscription', '=', True),
            ('state', '=', 'sale'),
        ], limit=1)

    def _prepare_home_portal_values(self, counters):
        """
        Añade el contador de arriendos a la página principal de "Mi Cuenta".
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

        # Productos arrendables y disponibles en stock interno
        available_lots = request.env['stock.lot'].sudo().search([
            ('product_id.x_es_prenda_arrendable', '=', True),
            ('quant_ids.quantity', '>', 0),
            ('quant_ids.location_id.usage', '=', 'internal'),
        ])
        rented_lots = request.env['arriendo.prenda.linea'].sudo().search([
            ('estado', '=', 'arrendada'), ('active', '=', True)
        ]).mapped('numero_serie_id')
    
        final_available_lots = available_lots - rented_lots

        # Eliminar duplicados correctamente
        product_ids = list(set(final_available_lots.mapped('product_id').ids))
        available_products = request.env['product.product'].browse(product_ids)

        # Validación segura del límite de prendas restantes
        max_allowed = subscription.x_max_prendas_permitidas or 0
        currently_held = subscription.x_cantidad_prendas_en_posesion or 0
        limit_remaining = max(0, max_allowed - currently_held)

        values = {
            'productos': available_products,
            'subscription': subscription,
            'prendas_disponibles_para_seleccionar': limit_remaining,
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

            # Llama al método del modelo para crear el albarán
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
            # Llama al método del modelo para crear el albarán
            picking = subscription.sudo()._create_rental_picking('incoming', lot_ids=lot_ids)

            return request.redirect('/my/rentals?success_message=' + _("Tu solicitud de devolución para %s prenda(s) ha sido creada. El albarán %s está listo para ser procesado.") % (len(lot_ids), picking.name))

        except (ValidationError, Exception) as e:
            return request.redirect('/my/rentals?error_message=' + str(e))
