from odoo import api, fields, models


class OulalabBoSyncLog(models.Model):
    _name = 'oulalab.bo.sync.log'
    _description = 'Historial de Sincronización BackOffice OulaLab'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Referencia', required=True, readonly=True, default='Nuevo')
    file_name = fields.Char(string='Origen / Archivo', readonly=True)
    entity_type = fields.Selection(
        [
            ('plans', 'Planes BO (oulalab.bo.plan.map)'),
            ('categories', 'Categorías (product.category)'),
            ('brands', 'Marcas (res.partner / product.tag)'),
            ('collections', 'Colecciones (product.tag)'),
            ('colors', 'Colores (product.tag)'),
            ('occasions', 'Ocasiones (product.tag)'),
            ('garments', 'Prendas Maestras (product.template)'),
            ('inventory', 'Inventario / Variantes SKU (product.template)'),
            ('customers', 'Clientes (res.partner)'),
            ('leads', 'Leads (crm.lead)'),
            ('appointments', 'Citas (calendar.event)'),
            ('subscriptions', 'Suscripciones -> Contrato OULAPLAN (sale.order)'),
            ('payments', 'Pagos BO -> Contrato OULAPLAN (sale.order)'),
            ('mercadopago_sales', 'Ventas Mercado Pago -> Conciliación OULAPLAN (sale.order)'),
            ('rentals', 'Órdenes de Alquiler -> RO/STKOUT (sale.order)'),
            ('orders', 'Detalle Pedidos / Líneas -> RO/STKOUT (sale.order)'),
            ('inventory_reservations', 'Reservas Inventario -> RO/STKOUT (sale.order)'),
            ('return_orders', 'Órdenes de Devolución -> RO/STKOUT (sale.order)'),
            ('webhook_event', 'Webhook Tiempo Real (integration-service)'),
        ],
        string='Entidad Sincronizada',
        required=True,
        readonly=True,
    )
    is_dry_run = fields.Boolean(string='Modo Simulación (Dry-Run)', readonly=True, default=False)
    state = fields.Selection(
        [
            ('done', 'Completado'),
            ('partial', 'Completado con Advertencias/Errores'),
            ('failed', 'Fallido'),
        ],
        string='Estado',
        default='done',
        readonly=True,
    )
    total_rows = fields.Integer(string='Total Filas / Eventos', readonly=True)
    created_count = fields.Integer(string='Creados', readonly=True)
    updated_count = fields.Integer(string='Actualizados', readonly=True)
    skipped_count = fields.Integer(string='Omitidos', readonly=True)
    error_count = fields.Integer(string='Errores', readonly=True)
    line_ids = fields.One2many('oulalab.bo.sync.log.line', 'log_id', string='Detalle por Fila', readonly=True)
    notes = fields.Text(string='Resumen Técnico', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Nuevo':
                vals['name'] = f"BO-SYNC-{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return super().create(vals_list)


class OulalabBoSyncLogLine(models.Model):
    _name = 'oulalab.bo.sync.log.line'
    _description = 'Detalle de Fila Sincronizada BO OulaLab'
    _order = 'row_number asc, id asc'

    log_id = fields.Many2one('oulalab.bo.sync.log', string='Log', required=True, ondelete='cascade')
    row_number = fields.Integer(string='Fila')
    external_key = fields.Char(string='Identificador / Email / Op MP')
    action = fields.Selection(
        [
            ('created', 'Creado'),
            ('updated', 'Actualizado'),
            ('skipped', 'Omitido'),
            ('error', 'Error'),
        ],
        string='Acción',
        required=True,
    )
    res_model = fields.Char(string='Modelo Odoo')
    res_id = fields.Integer(string='ID Registro Odoo')
    message = fields.Char(string='Detalle')
