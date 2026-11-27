# wizard/bo_backfill_wizard.py
import base64
import csv
import io
from collections import defaultdict
from odoo import api, fields, models, _
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

    def _group_by_order(self, rows):
        grouped = {}
        for row in rows:
            ref = str(row.get('order_ref') or '').strip()
            if not ref:
                continue
            if ref not in grouped:
                grouped[ref] = {
                    'order_ref': ref,
                    'rental_id': str(row.get('rental_id') or '').strip() or False,
                    'customer_email': str(row.get('customer_email') or '').strip() or False,
                    'customer_vat': str(row.get('customer_vat') or '').strip() or False,
                    'order_date': row.get('order_date'),
                    'lines': [],
                }
            sku = str(row.get('sku') or '').strip()
            if sku:
                grouped[ref]['lines'].append({
                    'sku': sku,
                    'garment_id': str(row.get('garment_id') or '').strip() or False,
                    'line_id': str(row.get('line_id') or '').strip() or False,
                })
        return list(grouped.values())

    def action_run_sync(self):
        self.ensure_one()
        rows = self._parse_rows()
        bo_orders = self._group_by_order(rows)

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
