from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ArriendoPrendaLinea(models.Model):
    _name = 'arriendo.prenda.linea'
    _description = 'Línea de Historial de Prenda Arrendada'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_arriendo desc'

    suscripcion_id = fields.Many2one(
        'sale.order',
        string='Suscripción',
        required=True,
        ondelete='cascade',
        domain="[('is_subscription', '=', True)]"
    )
    prenda_id = fields.Many2one(
        'product.product',
        string='Prenda',
        required=True,
        domain="[('x_es_prenda_arrendable', '=', True)]"
    )
    numero_serie_id = fields.Many2one(
        'stock.lot',
        string='Número de Serie',
        required=True,
        ondelete='restrict',
        domain="[('product_id.x_es_prenda_arrendable', '=', True)]"
    )
    fecha_arriendo = fields.Datetime(
        string='Fecha de Envío (Arriendo)',
        required=True,
        default=fields.Datetime.now,
        readonly=True
    )
    fecha_devolucion = fields.Datetime(
        string='Fecha de Devolución',
        readonly=True
    )
    estado = fields.Selection([
        ('arrendada', 'En posesión del cliente'),
        ('devuelta', 'Devuelta en almacén'),
        ('en_limpieza', 'En limpieza/revisión'),
        ('mantenimiento', 'En mantenimiento'),
        ('perdida', 'Declarada como perdida')
    ], string='Estado', default='arrendada', required=True, tracking=True)

    active = fields.Boolean(
        string='Activo',
        default=True,
        tracking=True,
        help="Una línea inactiva representa un arriendo histórico. Las activas representan prendas actualmente en posesión del cliente."
    )

    dias_en_posesion = fields.Integer(
        string='Días en Posesión',
        compute='_compute_dias_en_posesion',
        store=False
    )

    @api.depends('fecha_arriendo', 'fecha_devolucion')
    def _compute_dias_en_posesion(self):
        for rec in self:
            end_date = rec.fecha_devolucion or fields.Datetime.now()
            rec.dias_en_posesion = (end_date - rec.fecha_arriendo).days if rec.fecha_arriendo else 0

    @api.onchange('prenda_id')
    def _onchange_prenda_id(self):
        if self.prenda_id:
            rented_lots = self.env['arriendo.prenda.linea'].search([
                ('estado', '=', 'arrendada'),
                ('active', '=', True),
            ]).mapped('numero_serie_id').ids

            return {
                'domain': {
                    'numero_serie_id': [
                        ('product_id', '=', self.prenda_id.id),
                        ('id', 'not in', rented_lots),
                    ]
                }
            }

    @api.constrains('numero_serie_id', 'estado', 'active')
    def _check_numero_serie_disponible(self):
        for record in self:
            if record.estado == 'arrendada' and record.active and record.numero_serie_id:
                conflicto = self.search([
                    ('id', '!=', record.id),
                    ('numero_serie_id', '=', record.numero_serie_id.id),
                    ('estado', '=', 'arrendada'),
                    ('active', '=', True),
                ], limit=1)
                if conflicto:
                    raise ValidationError(_(
                        'La prenda con número de serie "%s" ya se encuentra activamente arrendada en la suscripción "%s".'
                    ) % (record.numero_serie_id.name, conflicto.suscripcion_id.name))
