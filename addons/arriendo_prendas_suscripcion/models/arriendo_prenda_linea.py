# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ArriendoPrendaLinea(models.Model):
    _name = 'arriendo.prenda.linea'
    _description = 'Línea de Prenda Arrendada'
    _order = 'fecha_arriendo desc'
    
    # Hemos eliminado la restricción _sql_constraints aquí.
    # La unicidad de la prenda activa en todo el sistema se maneja con _check_numero_serie_disponible.

    suscripcion_id = fields.Many2one(
        'sale.subscription',
        string='Suscripción',
        required=True,
        ondelete='cascade'
    )

    prenda_id = fields.Many2one(
        'product.product',
        string='Prenda',
        required=True,
        # Considera actualizar este dominio una vez que 'x_es_prenda_arrendable' esté en product.product
        domain=[('type', '=', 'product')]
    )

    numero_serie_id = fields.Many2one(
        'stock.production.lot',
        string='Número de Serie',
        required=True,
        domain="[('product_id', '=', prenda_id)]"
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

    @api.constrains('numero_serie_id', 'estado', 'active')
    def _check_numero_serie_disponible(self):
        for record in self:
            if record.estado == 'arrendada' and record.active:
                conflict = self.search([
                    ('numero_serie_id', '=', record.numero_serie_id.id),
                    ('estado', '=', 'arrendada'),
                    ('active', '=', True),
                    ('id', '!=', record.id)
                ], limit=1)
                if conflict:
                    raise ValidationError(_(
                        'La prenda con número de serie "%s" ya está arrendada en la suscripción "%s" y está activa. No puede ser arrendada nuevamente.'
                    ) % (record.numero_serie_id.display_name, conflict.suscripcion_id.display_name))
