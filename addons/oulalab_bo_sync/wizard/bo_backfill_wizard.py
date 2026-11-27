import base64
import csv
import io
from odoo import fields, models, _
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None


class BoBackfillWizard(models.TransientModel):
    _name = 'bo.backfill.wizard'
    _description = 'Wizard de Sincronización Histórica BO'

    file_data = fields.Binary(string='Archivo Excel / CSV', required=True)
    file_name = fields.Char(string='Nombre del archivo')
    skip_unlinked_cancelled = fields.Boolean(
        string='Omitir cancelados sin arriendo vinculado',
        default=True,
        help='Ignora los pedidos en estado cancelled que no tienen Arriendo vinculado.',
    )
    overwrite = fields.Boolean(
        string='Sobrescribir datos existentes',
        default=False,
        help='Si está desmarcado, solo completará campos BO vacíos.',
    )
    dry_run = fields.Boolean(
        string='Modo simulación (Dry Run)',
        default=True,
        help='Analiza coincidencias y diferencias sin modificar la base de datos.',
    )
    result_log = fields.Text(string='Resultado de la ejecución', readonly=True)

    def _parse_rows(self):
        self.ensure_one()
        raw = base64.b64decode(self.file_data)
        fname = (self.file_name or '').lower()

        if fname.endswith('.csv'):
            text = raw.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(text))
            return list(reader)

        if fname.endswith('.xlsx'):
            if not openpyxl:
                raise UserError(_('La librería openpyxl no está instalada en el servidor.'))
            wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            ws = wb.active
            rows_iter = ws.iter_rows(values_only=True)
            headers = [str(h).strip() if h is not None else '' for h in next(rows_iter)]
            return [
                dict(zip(headers, row))
                for row in rows_iter
                if any(cell is not None for cell in row)
            ]

        raise UserError(_('Formato no soportado. Sube un archivo .xlsx o .csv.'))

    def _parse_bo_orders(self, rows):
        orders = []
        for row in rows:
            ref = str(row.get('Código del pedido') or '').strip()
            if not ref:
                continue

            estado = str(row.get('Estado') or '').strip().lower()
            rental_id = str(row.get('Arriendo vinculado') or '').strip() or False

            if self.skip_unlinked_cancelled and estado == 'cancelled' and not rental_id:
                continue

            item_ids = [x.strip() for x in str(row.get('IDs de ítems del pedido') or '').split(';') if x.strip()]
            item_skus = [x.strip() for x in str(row.get('SKUs de ítems') or '').split(';') if x.strip()]
            item_names = [x.strip() for x in str(row.get('Nombres de ítems') or '').split(';') if x.strip()]

            lines = []
            for i in range(max(len(item_ids), len(item_skus))):
                lines.append({
                    'line_id': item_ids[i] if i < len(item_ids) else False,
                    'sku': item_skus[i] if i < len(item_skus) else False,
                    'name': item_names[i] if i < len(item_names) else '',
                })

            orders.append({
                'order_ref': ref,
                'internal_id': str(row.get('ID interno') or '').strip() or False,
                'rental_id': rental_id,
                'rental_state': str(row.get('Estado del arriendo vinculado') or '').strip() or False,
                'channel': str(row.get('Canal') or '').strip() or False,
                'customer_email': str(row.get('Email del cliente') or '').strip() or False,
                'order_date': str(row.get('Fecha de creación') or '').strip() or False,
                'lines': lines,
            })
        return orders

    def action_run_sync(self):
        self.ensure_one()
        rows = self._parse_rows()
        bo_orders = self._parse_bo_orders(rows)

        if not bo_orders:
            raise UserError(_('No se encontraron pedidos válidos en el archivo.'))

        summary = self.env['bo.backfill.service'].sync_historical_orders(
            bo_orders=bo_orders,
            overwrite=self.overwrite,
            dry_run=self.dry_run,
        )

        mode_label = 'SIMULACIÓN (sin cambios guardados)' if self.dry_run else 'EJECUCIÓN REAL'
        lines = [
            f'=== {mode_label} ===',
            f"Pedidos leídos: {len(bo_orders)}",
            f"Sincronizados exactos: {summary['synced']}",
            f"Sincronizados parciales (dif. prendas): {summary['partial']}",
            f"Sin coincidencia / Revisión manual: {summary['unmatched']}",
        ]
        if summary['errors']:
            lines.append('\n--- Detalle sin coincidencia ---')
            for err in summary['errors']:
                lines.append(f"- BO {err['bo_ref']}: {err['reason']}")

        self.result_log = '\n'.join(lines)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
