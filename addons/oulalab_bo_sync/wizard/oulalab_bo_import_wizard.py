import base64
import csv
import io
import json
from odoo import fields, models
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None


class OulalabBoImportWizard(models.TransientModel):
    _name = 'oulalab.bo.import.wizard'
    _description = 'Asistente de Importación CSV / Excel BackOffice & Mercado Pago OulaLab'

    csv_file = fields.Binary(string='Archivo (.csv o .xlsx Mercado Pago)', required=True)
    file_name = fields.Char(string='Nombre del Archivo')
    entity_type = fields.Selection(
        [
            ('auto', 'Detectar automáticamente según columnas'),
            ('plans', '1. Planes BO (plans-*.csv -> oulalab.bo.plan.map)'),
            ('categories', '2. Categorías (categories-*.csv -> product.category)'),
            ('brands', '3. Marcas (brands-*.csv -> res.partner / product.tag)'),
            ('collections', '4. Colecciones (collections-*.csv -> product.tag)'),
            ('colors', '5. Colores (colors-*.csv -> product.tag)'),
            ('occasions', '6. Ocasiones (occasions-*.csv -> product.tag)'),
            ('garments', '7. Prendas Maestras (garments-*.csv -> product.template)'),
            ('inventory', '8. Inventario / Variantes SKU (inventory-*.csv -> product.template)'),
            ('customers', '9. Clientes (customers-*.csv -> res.partner)'),
            ('leads', '10. Leads (leads-*.csv -> crm.lead)'),
            ('appointments', '11. Citas Showroom (appointments-*.csv -> calendar.event)'),
            ('subscriptions', '12. Suscripciones -> Contrato OULAPLAN (sale.order)'),
            ('payments', '13. Pagos BO -> Contrato OULAPLAN (sale.order)'),
            ('mercadopago_sales', '14. Ventas Mercado Pago (.xlsx/.csv) -> Conciliación OULAPLAN'),
            ('rentals', '15. Órdenes de Alquiler -> RO/STKOUT/BTL (sale.order)'),
            ('orders', '16. Detalle Pedidos / Ítems -> RO/STKOUT/BTL (sale.order)'),
            ('inventory_reservations', '17. Reservas de Inventario -> RO/STKOUT/BTL (sale.order)'),
            ('return_orders', '18. Órdenes de Devolución -> RO/STKOUT/BTL (sale.order)'),
        ],
        string='Tipo de Registro',
        default='auto',
        required=True,
    )
    execution_mode = fields.Selection(
        [
            ('review', 'Revisar cambios e incongruencias antes de registrar en Odoo (Recomendado)'),
            ('direct', 'Registrar directamente en Odoo sin revisión previa'),
        ],
        string='Modo de Procesamiento',
        default='review',
        required=True,
    )
    auto_create_partner_from_lead = fields.Boolean(
        string='Crear Contacto automáticamente si el Lead no existe en Clientes',
        default=False,
    )
    only_update_existing = fields.Boolean(
        string='Solo actualizar registros existentes en Odoo (No crear nuevos)',
        default=False,
        help='Ideal para cargas históricas del BO: vincula y actualiza los registros que ya existen en Odoo '
             '(sin tocar las prendas reales ya cargadas manualmente en órdenes de alquiler), y omite cualquier fila que intentaría crear un registro nuevo.',
    )

    def _decode_xlsx_mercadopago(self, raw_bytes):
        if not openpyxl:
            raise UserError('La librería openpyxl no está instalada en el servidor para leer archivos .xlsx.')
        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=True, read_only=True)
        ws = wb['Ventas'] if 'Ventas' in wb.sheetnames else wb.active
        header_row_idx = None
        headers = []
        rows = []
        for idx, row_vals in enumerate(ws.iter_rows(values_only=True), start=1):
            cleaned = [str(v).strip() if v is not None else '' for v in row_vals]
            if header_row_idx is None:
                if 'Número de operación' in cleaned and 'Referencia externa' in cleaned:
                    header_row_idx = idx
                    headers = cleaned
                continue
            if not any(cleaned):
                continue
            row_dict = {headers[i]: (cleaned[i] if i < len(cleaned) else '') for i in range(len(headers)) if headers[i]}
            rows.append((idx, row_dict))
        if not headers:
            raise UserError('No se encontraron los encabezados de Mercado Pago ("Número de operación", "Referencia externa") en el Excel.')
        return [h for h in headers if h], rows

    def _decode_input_file(self):
        if not self.csv_file:
            raise UserError('Debe seleccionar un archivo CSV o XLSX válido.')
        raw_bytes = base64.b64decode(self.csv_file)
        fname = (self.file_name or '').lower()

        if fname.endswith('.xlsx') or raw_bytes[:2] == b'PK':
            return self._decode_xlsx_mercadopago(raw_bytes)

        for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                text = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise UserError('No se pudo decodificar el archivo CSV. Verifique que esté en UTF-8.')

        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;')
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        if not reader.fieldnames:
            raise UserError('El archivo CSV no contiene encabezados.')
        headers = [h.strip() for h in reader.fieldnames if h]
        rows = [(idx, row) for idx, row in enumerate(reader, start=2)]
        return headers, rows

    def _detect_entity_type(self, headers):
        if self.entity_type != 'auto':
            return self.entity_type
        hset = {h.strip().lower() for h in headers}
        fname = (self.file_name or '').lower()

        if {'número de operación', 'referencia externa', 'cobro'}.issubset(hset) or 'mercadopago' in fname:
            return 'mercadopago_sales'
        if {'duración (días)', 'máx. prendas'}.issubset(hset) or 'plan' in fname:
            return 'plans'
        if {'código de reserva', 'origen de la reserva', 'arriendo asociado'}.issubset(hset) or 'reservation' in fname:
            return 'inventory_reservations'
        if {'sku', 'prenda', 'variante', 'id de variante'}.issubset(hset) or ('inventory' in fname and 'reservation' not in fname):
            return 'inventory'
        if {'foto_1', 'marca', 'categorías'}.issubset(hset) or 'garment' in fname:
            return 'garments'
        if {'url del logo', 'slug', 'nombre'}.issubset(hset) or 'brand' in fname:
            return 'brands'
        if {'imagen', 'marca', 'categorías'}.issubset(hset) or 'collection' in fname:
            return 'collections'
        if {'hex', 'color padre'}.issubset(hset) or 'color' in fname:
            return 'colors'
        if {'descripción', 'orden', 'activo'}.issubset(hset) and 'slug' not in hset or 'occasion' in fname:
            return 'occasions'
        if hset == {'id', 'nombre', 'fecha de alta'} or 'categor' in fname:
            return 'categories'
        if {'nombre', 'apellido', 'activo'}.issubset(hset) or 'customer' in fname:
            return 'customers'
        if {'origen', 'comuna', 'estado'}.issubset(hset) or 'lead' in fname:
            return 'leads'
        if {'inicio', 'showroom', 'cliente'}.issubset(hset) or 'appointment' in fname:
            return 'appointments'
        if {'monto (clp)', 'método', 'referencia'}.issubset(hset) or 'payment' in fname:
            return 'payments'
        if {'cliente', 'plan de arriendo', 'expiración'}.issubset(hset) or 'subscription' in fname:
            return 'subscriptions'
        if {'código del pedido', 'skus de ítems'}.issubset(hset) or (fname.startswith('orders') and 'return' not in fname):
            return 'orders'
        if {'arriendo', 'activo'}.issubset(hset) or 'return' in fname:
            return 'return_orders'
        if {'prendas', 'fecha del arriendo'}.issubset(hset) or 'rental' in fname:
            return 'rentals'

        raise UserError(
            f"No se pudo detectar automáticamente el tipo de archivo para los encabezados: {', '.join(headers)}. "
            "Seleccione el 'Tipo de Registro' manualmente."
        )

    def action_import_csv(self):
        self.ensure_one()
        headers, indexed_rows = self._decode_input_file()
        resolved_type = self._detect_entity_type(headers)

        model_map = {
            'plans': 'oulalab.bo.plan.map',
            'categories': 'product.category',
            'brands': 'res.partner',
            'collections': 'product.tag',
            'colors': 'product.tag',
            'occasions': 'product.tag',
            'garments': 'product.template',
            'inventory': 'product.template',
            'customers': 'res.partner',
            'leads': 'crm.lead',
            'appointments': 'calendar.event',
            'subscriptions': 'sale.order',
            'payments': 'sale.order',
            'mercadopago_sales': 'sale.order',
            'rentals': 'sale.order',
            'orders': 'sale.order',
            'inventory_reservations': 'sale.order',
            'return_orders': 'sale.order',
        }
        target_model = model_map[resolved_type]

        if self.execution_mode == 'review':
            batch = self.env['oulalab.bo.staging.batch'].create({
                'source_type': 'csv_upload',
                'file_name': self.file_name or f'{resolved_type}.csv',
                'entity_type': resolved_type,
                'auto_create_partner_from_lead': self.auto_create_partner_from_lead,
                'only_update_existing': self.only_update_existing,
                'notes': f"Encabezados detectados: {', '.join(headers)}",
            })
            line_vals_list = []
            for idx, row in indexed_rows:
                ext_key = (
                    row.get('Número de operación')
                    or row.get('Código de reserva')
                    or row.get('Email')
                    or row.get('Email del cliente')
                    or row.get('Código del pedido')
                    or row.get('SKU')
                    or row.get('Cliente')
                    or row.get('Nombre')
                    or row.get('ID')
                    or row.get('Id')
                    or f'Fila {idx}'
                )
                line_vals_list.append({
                    'batch_id': batch.id,
                    'row_number': idx,
                    'effective_entity_type': resolved_type,
                    'external_key': str(ext_key)[:120],
                    'target_res_model': target_model,
                    'raw_payload_json': json.dumps(row, ensure_ascii=False),
                })
            lines = self.env['oulalab.bo.staging.line'].create(line_vals_list)
            lines._run_precheck_validation()

            return {
                'type': 'ir.actions.act_window',
                'name': 'Revisión Previa de Cambios e Incongruencias BO',
                'res_model': 'oulalab.bo.staging.batch',
                'res_id': batch.id,
                'view_mode': 'form',
                'target': 'current',
            }

        batch = self.env['oulalab.bo.staging.batch'].create({
            'source_type': 'csv_upload',
            'file_name': self.file_name or f'{resolved_type}.csv',
            'entity_type': resolved_type,
            'auto_create_partner_from_lead': self.auto_create_partner_from_lead,
                'only_update_existing': self.only_update_existing,
        })
        line_vals_list = []
        for idx, row in indexed_rows:
            ext_key = (
                row.get('Número de operación')
                or row.get('Código de reserva')
                or row.get('Email')
                or row.get('Email del cliente')
                or row.get('Código del pedido')
                or row.get('SKU')
                or row.get('Cliente')
                or row.get('Nombre')
                or row.get('ID')
                or row.get('Id')
                or f'Fila {idx}'
            )
            line_vals_list.append({
                'batch_id': batch.id,
                'row_number': idx,
                'effective_entity_type': resolved_type,
                'external_key': str(ext_key)[:120],
                'target_res_model': target_model,
                'review_decision': 'approved',
                'raw_payload_json': json.dumps(row, ensure_ascii=False),
            })
        self.env['oulalab.bo.staging.line'].create(line_vals_list)
        return batch.action_apply_approved_lines()
