# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ArriendoPrendaLinea(models.Model):
    _name = 'arriendo_prendas_suscripcion.arriendo_prenda_linea'
    _description = 'Línea de Prenda Arrendada'
    _order = 'fecha_arriendo desc'

    suscripcion_id = fields.Many2one(
        'sale.order',
        string='Suscripción',
        required=True,
        ondelete='cascade'
    )

    prenda_id = fields.Many2one(
        'product.product',
        string='Prenda',
        required=True,
        domain=[('type', '=', 'product')]
    )

    numero_serie_id = fields.Many2one(
        'stock.production.lot',
        string='Número de Serie',
        required=False,
        check_company=False,
    )

    fecha_arriendo = fields.Datetime(
        string='Fecha de Arriendo',
        required=True,
        default=fields.Datetime.now
    )

    fecha_devolucion = fields.Datetime(
        string='Fecha de Devolución'
    )

    estado = fields.Selection([
        ('arrendada', 'Arrendada'),
        ('devuelta', 'Devuelta'),
        ('en_limpieza', 'En Limpieza'),
        ('mantenimiento', 'Mantenimiento'),
        ('perdida', 'Perdida')
    ], string='Estado', default='arrendada', required=True)

    active = fields.Boolean(string='Activo', default=True)

    @api.onchange('prenda_id')
    def _onchange_prenda_id(self):
        """
        Limpia la serie si no corresponde a la prenda,
        y filtra el dominio para las series según el producto.
        """
        try:
            if self.numero_serie_id and getattr(self.numero_serie_id, 'product_id', False):
                if self.numero_serie_id.product_id != self.prenda_id:
                    self.numero_serie_id = False
            else:
                self.numero_serie_id = False
        except Exception as e:
            _logger.warning("⚠️ Error en onchange de prenda_id: %s", e)
            self.numero_serie_id = False

        return {
            'domain': {
                'numero_serie_id': [('product_id', '=', self.prenda_id.id)] if self.prenda_id else []
            }
        }

    @api.constrains('numero_serie_id', 'estado', 'active')
    def _check_numero_serie_disponible(self):
        for record in self:
            if record.estado == 'arrendada' and record.active and record.numero_serie_id:
                conflict = self.search([
                    ('numero_serie_id', '=', record.numero_serie_id.id),
                    ('estado', '=', 'arrendada'),
                    ('active', '=', True),
                    ('id', '!=', record.id)
                ], limit=1)
                if conflict:
                    raise ValidationError(_(
                        'La prenda con número de serie "%s" ya está arrendada en la suscripción "%s" y está activa. '
                        'No puede ser arrendada nuevamente.'
                    ) % (record.numero_serie_id.display_name, conflict.suscripcion_id.display_name))
