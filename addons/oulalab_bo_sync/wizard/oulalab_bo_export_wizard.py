import base64
import csv
import io
import re
from odoo import fields, models
from odoo.exceptions import UserError


def _slugify(text):
    if not text:
        return ''
    s = re.sub(r'[^a-zA-Z0-9]+', '-', str(text).strip().lower()).strip('-')
    return s


class OulalabBoExportWizard(models.TransientModel):
    _name = 'oulalab.bo.export.wizard'
    _description = 'Asistente de Exportación de Planillas CSV hacia BackOffice OulaLab'

    export_type = fields.Selection(
        [
            ('inventory_import', 'Inventario Consolidado por SKU BO (inventory-import.csv)'),
            ('product_bulk_import', 'Carga Masiva de Prendas / Catálogo BO (product-bulk-import.csv)'),
        ],
        string='Planilla a Generar para BO',
        default='inventory_import',
        required=True,
    )
    updated_since = fields.Datetime(
        string='Solo cambios desde (Opcional)',
        help='Si se indica una fecha/hora, exporta únicamente los SKUs cuya ficha o movimiento de stock haya cambiado desde ese momento.',
    )
    include_zero_stock = fields.Boolean(
        string='Incluir SKUs con Stock = 0',
        default=True,
    )
    csv_data = fields.Binary(string='Archivo CSV Generado', readonly=True)
    file_name = fields.Char(string='Nombre Archivo', readonly=True)
    summary_text = fields.Text(string='Resumen de Exportación', readonly=True)

    def _get_grouped_bo_products(self):
        Product = self.env['product.product']
        domain = [('active', '=', True), ('rent_ok', '=', True), ('default_code', '!=', False)]

        all_units = Product.search(domain, order='default_code asc, id asc')
        grouped = {}
        for unit in all_units:
            tmpl = unit.product_tmpl_id
            bo_sku = (
                (tmpl.x_bo_sku if 'x_bo_sku' in tmpl._fields else '')
                or re.sub(r'-\d{5}$', '', (unit.default_code or ''))
            ).strip()
            if not bo_sku:
                continue
            grouped.setdefault(bo_sku, self.env['product.product'].browse())
            grouped[bo_sku] |= unit
        return grouped

    def _build_inventory_import_csv(self):
        stock_cfg = self.env['oulalab.bo.stock.config'].get_active_config()
        avail_locs = stock_cfg.get_available_locations_tree()
        fleet_locs = stock_cfg.get_fleet_locations_tree()
        Quant = self.env['stock.quant']
        MoveLine = self.env['stock.move.line']

        grouped = self._get_grouped_bo_products()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['sku', 'garment_name', 'variant_title', 'stocked', 'reserved', 'in_stock'])

        exported_rows = 0
        for bo_sku in sorted(grouped.keys()):
            units = grouped[bo_sku]
            tmpls = units.mapped('product_tmpl_id')

            if self.updated_since:
                tmpl_changed = any(t.write_date and t.write_date >= self.updated_since for t in tmpls)
                move_changed = bool(MoveLine.search_count([
                    ('product_id', 'in', units.ids),
                    ('write_date', '>=', self.updated_since),
                ]))
                if not tmpl_changed and not move_changed:
                    continue

            fleet_quants = Quant.search([
                ('product_id', 'in', units.ids),
                ('location_id', 'in', fleet_locs.ids),
            ])
            avail_quants = Quant.search([
                ('product_id', 'in', units.ids),
                ('location_id', 'in', avail_locs.ids),
            ])

            stocked_qty = int(round(sum(max(0.0, q.quantity) for q in fleet_quants)))
            in_stock_qty = int(round(sum(max(0.0, q.quantity - q.reserved_quantity) for q in avail_quants)))
            if in_stock_qty > stocked_qty:
                stocked_qty = in_stock_qty
            reserved_qty = max(0, stocked_qty - in_stock_qty)

            if not self.include_zero_stock and stocked_qty == 0:
                continue

            rep = tmpls[0]
            garment_name = (
                (rep.x_studio_descripcion if 'x_studio_descripcion' in rep._fields else '')
                or rep.name
                or bo_sku
            ).strip()
            variant_title = (
                (rep.x_studio_talla if 'x_studio_talla' in rep._fields else '')
                or (bo_sku.split('-')[-1] if '-' in bo_sku else 'UNQ')
            ).strip()

            writer.writerow([bo_sku, garment_name, variant_title, stocked_qty, reserved_qty, in_stock_qty])
            exported_rows += 1

        return output.getvalue(), exported_rows

    def _build_product_bulk_import_csv(self):
        grouped = self._get_grouped_bo_products()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'sku', 'name', 'brand', 'color', 'season', 'occasion',
            'sizeGuide', 'category', 'subcategory', 'tags', 'details',
            'bookTheLook', 'garmentKind',
        ])

        exported_rows = 0
        for bo_sku in sorted(grouped.keys()):
            units = grouped[bo_sku]
            tmpls = units.mapped('product_tmpl_id')

            if self.updated_since:
                if not any(t.write_date and t.write_date >= self.updated_since for t in tmpls):
                    continue

            rep = tmpls[0]
            name = (
                (rep.x_studio_descripcion if 'x_studio_descripcion' in rep._fields else '')
                or rep.name
                or bo_sku
            ).strip()
            brand = (
                (rep.x_studio_marca if 'x_studio_marca' in rep._fields else '')
                or (rep.x_studio_nombre_marca_grupo_industrial.name if 'x_studio_nombre_marca_grupo_industrial' in rep._fields and rep.x_studio_nombre_marca_grupo_industrial else '')
            ).strip()

            color = ''
            if 'x_studio_colores' in rep._fields and rep.x_studio_colores:
                color = '|'.join(rep.x_studio_colores.mapped('name'))

            season = (rep.x_studio_clima_ideal if 'x_studio_clima_ideal' in rep._fields else '') or ''
            occasion = ''
            if 'x_studio_ocasiones' in rep._fields and rep.x_studio_ocasiones:
                occasion = '|'.join(rep.x_studio_ocasiones.mapped('name'))

            size_guide = f"{_slugify(brand)}-guide" if brand else ''

            categ_path = (rep.categ_id.complete_name or '') if rep.categ_id else ''
            is_btl = 'book the look' in categ_path.lower() or '-btl-' in bo_sku.lower()
            category = ''
            subcategory = ''
            if categ_path:
                parts = [p.strip() for p in categ_path.split('/')]
                for anchor in ('Subscription Apparels', 'Book The Look', 'BO Categories'):
                    if anchor in parts:
                        idx = parts.index(anchor)
                        if idx + 1 < len(parts):
                            category = parts[idx + 1]
                        if idx + 2 < len(parts):
                            subcategory = parts[idx + 2]
                        break
                if not category and parts:
                    category = parts[-1]

            tag_names = list(rep.product_tag_ids.mapped('name'))
            if 'x_studio_estilos' in rep._fields and rep.x_studio_estilos:
                tag_names.extend(rep.x_studio_estilos.mapped('name'))
            tags = '|'.join(dict.fromkeys(tag_names))

            details = (
                (rep.x_studio_materialidad if 'x_studio_materialidad' in rep._fields else '')
                or rep.description_sale
                or ''
            ).strip()

            book_the_look = 'si' if is_btl else ''
            garment_kind = ''
            if is_btl:
                garment_kind = 'clutch' if ('clutch' in category.lower() or 'accesorio' in category.lower() or 'clutch' in name.lower()) else 'garment'

            writer.writerow([
                bo_sku, name, brand, color, season, occasion,
                size_guide, category, subcategory, tags, details,
                book_the_look, garment_kind,
            ])
            exported_rows += 1

        return output.getvalue(), exported_rows

    def action_generate_export(self):
        self.ensure_one()
        today_str = fields.Date.context_today(self).strftime('%Y-%m-%d')
        if self.export_type == 'inventory_import':
            csv_text, count = self._build_inventory_import_csv()
            fname = f"inventory-import-{today_str}.csv"
        elif self.export_type == 'product_bulk_import':
            csv_text, count = self._build_product_bulk_import_csv()
            fname = f"product-bulk-import-{today_str}.csv"
        else:
            raise UserError('Tipo de exportación no soportado.')

        self.write({
            'csv_data': base64.b64encode(csv_text.encode('utf-8-sig')),
            'file_name': fname,
            'summary_text': f"Planilla generada con éxito: {fname} ({count} SKUs consolidados listos para importar en bo.oulalab.com).",
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/?model={self._name}&id={self.id}&field=csv_data&filename_field=file_name&download=true",
            'target': 'self',
        }
