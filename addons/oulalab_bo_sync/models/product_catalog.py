import re
from odoo import api, fields, models

UUID_RE = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')


class ProductCategory(models.Model):
    _inherit = 'product.category'

    x_bo_category_uuid = fields.Char(string='UUID Categoría BO', index=True, copy=False)

    @api.model
    def _find_by_bo_uuid(self, cat_uuid):
        if not cat_uuid:
            return self.browse()
        domain = [('x_bo_category_uuid', '=', cat_uuid)]
        if 'x_studio_id_bo_categoria' in self._fields:
            domain = ['|', ('x_studio_id_bo_categoria', 'ilike', cat_uuid)] + domain
        return self.search(domain)

    @api.model
    def upsert_from_bo_category(self, row, dry_run=False):
        cat_uuid = (row.get('Id') or row.get('ID') or '').strip()
        name = (row.get('Nombre') or '').strip()
        if not name or UUID_RE.match(name):
            return 'skipped', self.browse(), 'Fila de categoría sin Nombre válido.'

        existing = self._find_by_bo_uuid(cat_uuid) if cat_uuid else self.browse()
        if not existing:
            existing = self.search([('name', '=ilike', name)], limit=1)

        vals = {}
        if cat_uuid:
            vals['x_bo_category_uuid'] = cat_uuid
            if 'x_studio_id_bo_categoria' in self._fields:
                for cat in existing:
                    cur = (cat.x_studio_id_bo_categoria or '').strip()
                    if cat_uuid not in cur:
                        new_val = f"{cur},{cat_uuid}" if cur else cat_uuid
                        if not dry_run:
                            cat.with_context(skip_bo_outbound=True).write({'x_studio_id_bo_categoria': new_val, 'x_bo_category_uuid': cat_uuid})

        if existing:
            if not dry_run and vals:
                existing.with_context(skip_bo_outbound=True).write(vals)
            return 'updated', existing[:1], f"Categoría vinculada ({name})"

        create_vals = {'name': name, **vals}
        if 'x_studio_id_bo_categoria' in self._fields and cat_uuid:
            create_vals['x_studio_id_bo_categoria'] = cat_uuid
        if not dry_run:
            existing = self.with_context(skip_bo_outbound=True).create(create_vals)
        return 'created', existing, f"Categoría creada ({name})"


class ProductTag(models.Model):
    _inherit = 'product.tag'

    x_bo_hex_color = fields.Char(string='Color Hex BO')
    x_bo_parent_color = fields.Char(string='Color Padre BO')
    x_bo_collection_uuid = fields.Char(string='UUID Colección BO', index=True)

    @api.model
    def upsert_from_bo_color(self, row, dry_run=False):
        name = (row.get('Nombre') or '').strip()
        hex_val = (row.get('Hex') or '').strip()
        parent_color = (row.get('Color padre') or '').strip()
        if not name:
            return 'skipped', self.browse(), 'Fila de color sin Nombre (registro vacío en BO).'

        existing = self.search([('name', '=ilike', name)], limit=1)
        vals = {
            'name': name,
            'x_bo_hex_color': hex_val or False,
            'x_bo_parent_color': parent_color or False,
        }
        if existing:
            if not dry_run:
                existing.write(vals)
            return 'updated', existing, f"Color actualizado ({name})"

        if not dry_run:
            existing = self.create(vals)
        return 'created', existing, f"Color creado ({name})"

    @api.model
    def upsert_from_bo_occasion(self, row, dry_run=False):
        name = (row.get('Nombre') or '').strip()
        if not name:
            return 'skipped', self.browse(), 'Fila de ocasión sin Nombre (registro vacío en BO).'

        existing = self.search([('name', '=ilike', name)], limit=1)
        if existing:
            return 'updated', existing, f"Ocasión existente ({name})"

        if not dry_run:
            existing = self.create({'name': name})
        return 'created', existing, f"Ocasión creada ({name})"

    @api.model
    def upsert_from_bo_collection(self, row, dry_run=False):
        col_uuid = (row.get('Id') or row.get('ID') or '').strip()
        name = (row.get('Nombre') or '').strip()
        if not name or name == col_uuid or UUID_RE.match(name):
            return 'skipped', self.browse(), f"Fila de colección sin nombre descriptivo ({name or col_uuid})."

        domain = [('name', '=ilike', name)]
        if col_uuid:
            domain = ['|', ('x_bo_collection_uuid', '=', col_uuid)] + domain
        existing = self.search(domain, limit=1)
        vals = {'name': name}
        if col_uuid:
            vals['x_bo_collection_uuid'] = col_uuid

        if existing:
            if not dry_run:
                existing.write(vals)
            return 'updated', existing, f"Colección actualizada ({name})"

        if not dry_run:
            existing = self.create(vals)
        return 'created', existing, f"Colección creada ({name})"


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_bo_operational_status = fields.Char(string='Estado Operativo BO', copy=False)
    x_bo_photo_urls = fields.Text(string='URLs Fotos BO', copy=False)
    x_bo_sku = fields.Char(string='Código SKU BO Sync', index=True, copy=False)

    @api.model
    def _filter_existing_fields(self, vals):
        return {k: v for k, v in vals.items() if k in self._fields}

    @api.model
    def _get_candidate_units_for_bo_sku(self, bo_sku=None, garment_name=None):
        Product = self.env['product.product']
        token = (bo_sku or '').strip()
        candidates = Product.browse()

        if token:
            if UUID_RE.match(token) and 'x_studio_id_bo_variante' in Product._fields:
                direct = Product.search([
                    ('active', '=', True),
                    ('rent_ok', '=', True),
                    ('x_studio_id_bo_variante', '=ilike', token),
                ])
                if direct:
                    candidates |= direct
                    bo_skus = [s for s in direct.mapped('x_bo_sku') if s]
                    if bo_skus:
                        token = bo_skus[0]
                    elif direct[0].default_code:
                        token = re.sub(r'-\d{5}$', '', direct[0].default_code).strip()

            if token and not UUID_RE.match(token):
                domain = [
                    ('active', '=', True),
                    ('rent_ok', '=', True),
                    '|',
                    ('x_bo_sku', '=ilike', token),
                    '|',
                    ('default_code', '=ilike', token),
                    ('default_code', '=ilike', f'{token}-%'),
                ]
                candidates |= Product.search(domain)

        if not candidates and garment_name:
            name_clean = garment_name.strip()
            candidates |= Product.search([('name', '=ilike', name_clean), ('active', '=', True), ('rent_ok', '=', True)])
            if not candidates and 'x_studio_descripcion' in Product._fields:
                candidates |= Product.search([('x_studio_descripcion', '=ilike', name_clean), ('active', '=', True), ('rent_ok', '=', True)])

        return candidates.sorted(key=lambda p: (p.default_code or 'ZZZZ', p.id))

    @api.model
    def _select_available_unit_for_bo_sku(self, bo_sku=None, garment_name=None, qty_needed=1.0, preferred_product_ids=None):
        candidates = self._get_candidate_units_for_bo_sku(
            bo_sku=bo_sku,
            garment_name=garment_name,
        )
        if not candidates:
            return self.env['product.product'].browse(), False, (
                f"No se encontró ninguna unidad física de alquiler en Odoo para SKU '{bo_sku or garment_name}'."
            )

        if preferred_product_ids:
            already_assigned = candidates.filtered(lambda p: p.id in preferred_product_ids)
            if already_assigned:
                chosen = already_assigned[0]
                return chosen, True, (
                    f"Unidad ya asignada mantenida: {chosen.default_code or chosen.name} (Barcode: {chosen.barcode or 'N/A'})"
                )

        stock_cfg = self.env['oulalab.bo.stock.config'].get_active_config()
        avail_locs = stock_cfg.get_available_locations_tree()
        Quant = self.env['stock.quant']

        best_unit = self.env['product.product'].browse()
        best_avail_qty = 0.0
        checked_details = []

        for unit in candidates:
            quants = Quant.search([
                ('product_id', '=', unit.id),
                ('location_id', 'in', avail_locs.ids),
            ])
            avail_qty = sum((q.quantity - q.reserved_quantity) for q in quants)
            checked_details.append(f"{unit.default_code or unit.id}:disp={avail_qty:g}")
            if avail_qty >= qty_needed:
                best_unit = unit
                best_avail_qty = avail_qty
                break

        if best_unit:
            return best_unit, True, (
                f"Unidad disponible seleccionada: {best_unit.default_code or best_unit.name} "
                f"(Disp: {best_avail_qty:g})"
            )

        fallback_unit = candidates[0]
        return fallback_unit, False, (
            f"Sin stock disponible en Racks/BTL para SKU '{bo_sku or garment_name}' "
            f"[{', '.join(checked_details)}]. Asignado por defecto: {fallback_unit.default_code or fallback_unit.name}"
        )

    @api.model
    def upsert_from_bo_garment(self, row, dry_run=False):
        garment_uuid = (row.get('Id') or row.get('ID') or '').strip()
        name = (row.get('Nombre') or '').strip()
        brand_name = (row.get('Marca') or '').strip()
        cats_raw = (row.get('Categorías') or '').strip()

        if not name and not garment_uuid:
            return 'skipped', self.browse(), 'Fila de prenda sin Nombre ni Id.'

        photos = [
            (row.get(f'foto_{i}') or '').strip()
            for i in range(1, 11)
            if (row.get(f'foto_{i}') or '').strip()
        ]

        cat_uuids = [c.strip() for c in cats_raw.split(',') if c.strip()]
        primary_categ = self.env['product.category'].browse()
        tag_ids = []
        if cat_uuids:
            Category = self.env['product.category']
            matched_cats = Category.browse()
            for cu in cat_uuids:
                matched_cats |= Category._find_by_bo_uuid(cu)
            if matched_cats:
                sub_cats = matched_cats.filtered(lambda c: 'Subscription' in (c.complete_name or ''))
                primary_categ = (sub_cats or matched_cats)[0]
                for c in matched_cats:
                    tag = self.env['product.tag'].search([('name', '=ilike', c.name)], limit=1)
                    if not tag and not dry_run:
                        tag = self.env['product.tag'].create({'name': c.name})
                    if tag:
                        tag_ids.append(tag.id)

        brand_partner = self.env['res.partner'].browse()
        if brand_name:
            brand_partner = self.env['res.partner'].search(
                [('name', '=ilike', brand_name), ('is_company', '=', True)], limit=1
            )

        existing = self.browse()
        if garment_uuid and 'x_studio_id_bo_prenda' in self._fields:
            existing = self.search([('x_studio_id_bo_prenda', '=', garment_uuid)])
        if not existing and name:
            domain = ['|', ('name', '=ilike', name), ('name', 'ilike', f' {name} ')]
            if 'x_studio_descripcion' in self._fields:
                domain = ['|', ('x_studio_descripcion', '=ilike', name)] + domain
            existing = self.search(domain)

        vals = {
            'rent_ok': True,
        }
        if garment_uuid:
            vals['x_studio_id_bo_prenda'] = garment_uuid
        if brand_name:
            vals['x_studio_marca'] = brand_name
        if brand_partner:
            vals['x_studio_nombre_marca_grupo_industrial'] = brand_partner.id
        if primary_categ:
            vals['categ_id'] = primary_categ.id
        if photos:
            vals['x_bo_photo_urls'] = '\n'.join(photos)
        if tag_ids:
            vals['x_studio_clasificacion_de_la_prenda'] = [(4, tid) for tid in tag_ids]

        if existing:
            if not dry_run:
                existing.with_context(skip_bo_outbound=True).write(self._filter_existing_fields(vals))
            return 'updated', existing[:1], f"Prenda maestra sincronizada en {len(existing)} unidad(es) ({name})"

        create_vals = {
            'name': name or garment_uuid,
            'x_studio_descripcion': name or False,
            'type': 'consu',
            'sale_ok': True,
            'rent_ok': True,
            **vals,
        }
        if not dry_run:
            existing = self.with_context(skip_bo_outbound=True).create(self._filter_existing_fields(create_vals))
        return 'created', existing, f"Prenda maestra creada ({name})"

    @api.model
    def _next_unique_barcode(self, rep_barcode, bo_sku, seq_num):
        Product = self.env['product.product']
        candidate = ''
        if rep_barcode:
            m = re.match(r'^(.+?)(\d{5})$', rep_barcode.strip())
            if m:
                candidate = f"{m.group(1)}{seq_num:05d}"
        if not candidate:
            candidate = f"{bo_sku}-{seq_num:05d}".replace('-', '')
        # Garantizar unicidad absoluta de código de barras en Odoo
        if Product.with_context(active_test=False).search_count([('barcode', '=', candidate)]):
            candidate = f"{bo_sku.replace('-', '')}{seq_num:05d}"
        return candidate

    def _reconcile_bo_unit_count_and_stock(self, bo_sku, target_stocked, target_in_stock, base_vals, garment_name, dry_run=False):
        units = self._get_candidate_units_for_bo_sku(bo_sku=bo_sku, garment_name=garment_name)
        tmpls = units.mapped('product_tmpl_id')
        stock_cfg = self.env['oulalab.bo.stock.config'].get_active_config()
        avail_locs = stock_cfg.get_available_locations_tree()
        fleet_locs = stock_cfg.get_fleet_locations_tree()
        target_loc = stock_cfg.available_location_ids[:1] or avail_locs[:1]
        Quant = self.env['stock.quant']

        created_extra = 0
        if target_stocked > len(tmpls) and bo_sku:
            existing_codes = set(tmpls.mapped('default_code'))
            max_seq = 0
            for code in existing_codes:
                m = re.search(r'-(\d{5})$', code or '')
                if m:
                    max_seq = max(max_seq, int(m.group(1)))

            rep = tmpls[:1]
            rep_barcode = rep.barcode if rep else ''
            needed = target_stocked - len(tmpls)
            for _ in range(needed):
                max_seq += 1
                new_code = f"{bo_sku}-{max_seq:05d}"
                new_barcode = self._next_unique_barcode(rep_barcode, bo_sku, max_seq)
                if dry_run:
                    created_extra += 1
                    continue
                unit_specific_vals = {
                    'default_code': new_code,
                    'barcode': new_barcode,
                    'tracking': 'none',
                    'is_storable': True,
                    **self._filter_existing_fields(base_vals),
                }
                if target_loc and 'x_studio_ubicacion_actual_1' in self._fields:
                    unit_specific_vals['x_studio_ubicacion_actual_1'] = target_loc.id

                if rep:
                    new_tmpl = rep.with_context(skip_bo_outbound=True).copy(unit_specific_vals)
                else:
                    create_vals = {
                        'name': garment_name or bo_sku,
                        'x_studio_descripcion': garment_name or False,
                        'type': 'consu',
                        'sale_ok': True,
                        'rent_ok': True,
                        **unit_specific_vals,
                    }
                    new_tmpl = self.with_context(skip_bo_outbound=True).create(create_vals)
                tmpls |= new_tmpl
                created_extra += 1

        if not dry_run and target_loc and bo_sku:
            units = self._get_candidate_units_for_bo_sku(bo_sku=bo_sku, garment_name=garment_name)
            avail_quants = Quant.search([('product_id', 'in', units.ids), ('location_id', 'in', avail_locs.ids)])
            current_in_stock = int(round(sum(max(0.0, q.quantity - q.reserved_quantity) for q in avail_quants)))

            if target_in_stock > current_in_stock:
                missing_avail = target_in_stock - current_in_stock
                for unit in units:
                    if missing_avail <= 0:
                        break
                    u_fleet = Quant.search([('product_id', '=', unit.id), ('location_id', 'in', fleet_locs.ids)])
                    if sum(max(0.0, q.quantity) for q in u_fleet) < 1.0:
                        Quant.with_context(skip_bo_outbound=True)._update_available_quantity(
                            unit, target_loc, 1.0
                        )
                        if 'x_studio_ubicacion_actual_1' in unit.product_tmpl_id._fields:
                            unit.product_tmpl_id.with_context(skip_bo_outbound=True).write({
                                'x_studio_ubicacion_actual_1': target_loc.id
                            })
                        missing_avail -= 1

        return created_extra

    @api.model
    def upsert_from_bo_inventory(self, row, dry_run=False):
        sku = (row.get('SKU') or '').strip()
        garment_name = (row.get('Prenda') or '').strip()
        variant_size = (row.get('Variante') or '').strip()
        garment_uuid = (row.get('ID de prenda') or '').strip()
        variant_uuid = (row.get('ID de variante') or '').strip()
        op_status = (row.get('Estado operativo') or '').strip()

        def _to_int(val):
            try:
                return int(float(str(val).strip()))
            except (ValueError, TypeError):
                return 0

        bo_stock_qty = _to_int(row.get('Stock'))
        bo_avail_qty = _to_int(row.get('Disponible'))

        if not sku and not garment_name:
            return 'skipped', self.browse(), 'Fila de inventario sin SKU ni nombre de prenda.'

        existing_tmpls = self._get_candidate_units_for_bo_sku(bo_sku=sku, garment_name=garment_name).mapped('product_tmpl_id')
        if not existing_tmpls and variant_uuid and 'x_studio_id_bo_variante' in self._fields:
            existing_tmpls |= self.search([('x_studio_id_bo_variante', '=', variant_uuid)])
        if not existing_tmpls and garment_uuid and 'x_studio_id_bo_prenda' in self._fields:
            existing_tmpls |= self.search([('x_studio_id_bo_prenda', '=', garment_uuid), ('default_code', '=', False)])

        is_retired = op_status.lower() in ('retirado', 'baja', 'inactivo', 'archived')
        vals = {
            'rent_ok': not is_retired,
            'x_bo_operational_status': op_status or False,
            'x_bo_sku': sku or False,
        }
        if garment_uuid:
            vals['x_studio_id_bo_prenda'] = garment_uuid
        if variant_uuid:
            vals['x_studio_id_bo_variante'] = variant_uuid
        if variant_size in ('XXL', 'XL', 'L', 'M', 'S', 'XS', 'XXS', 'UNQ'):
            vals['x_studio_talla'] = variant_size
        # Si el SKU corresponde a Book The Look (-BTL-), sincronizar preparación (6d) y multa diaria ($30.000)
        if '-btl-' in sku.lower():
            cfg = self.env['oulalab.bo.stock.config'].get_active_config()
            if 'preparation_time' in self._fields:
                vals['preparation_time'] = float(cfg.btl_prep_days * 24)
            if 'extra_daily' in self._fields:
                vals['extra_daily'] = cfg.btl_late_fee_daily

        if existing_tmpls:
            if not dry_run:
                existing_tmpls.with_context(skip_bo_outbound=True).write(self._filter_existing_fields(vals))
                for tmpl in existing_tmpls.filtered(lambda t: not t.default_code and sku):
                    tmpl.with_context(skip_bo_outbound=True).write({'default_code': f'{sku}-00001'})

            extra_created = self._reconcile_bo_unit_count_and_stock(
                bo_sku=sku,
                target_stocked=bo_stock_qty,
                target_in_stock=bo_avail_qty,
                base_vals=vals,
                garment_name=garment_name,
                dry_run=dry_run,
            )
            msg = f"SKU BO {sku} actualizado en {len(existing_tmpls)} unidad(es)"
            if extra_created:
                msg += f" + {extra_created} unidad(es) serializada(s) creada(s) desde BO"
            return 'updated', existing_tmpls[:1], msg

        create_vals = {
            'name': garment_name or sku,
            'x_studio_descripcion': garment_name or False,
            'default_code': f'{sku}-00001' if sku else False,
            'barcode': f'{sku}-00001'.replace('-', '') if sku else False,
            'type': 'consu',
            'tracking': 'none',
            'is_storable': True,
            'sale_ok': True,
            'rent_ok': not is_retired,
            **vals,
        }
        if not dry_run:
            existing_tmpls = self.with_context(skip_bo_outbound=True).create(self._filter_existing_fields(create_vals))

        extra_created = self._reconcile_bo_unit_count_and_stock(
            bo_sku=sku,
            target_stocked=max(1, bo_stock_qty),
            target_in_stock=bo_avail_qty,
            base_vals=vals,
            garment_name=garment_name,
            dry_run=dry_run,
        )
        total_units = 1 + extra_created
        return 'created', existing_tmpls, f"SKU BO {sku}: {total_units} unidad(es) física(s) serializada(s) creada(s)"

    def write(self, vals):
        res = super().write(vals)
        watched = {'name', 'default_code', 'categ_id', 'x_bo_operational_status', 'x_studio_talla', 'x_studio_marca', 'active', 'rent_ok'}
        if watched.intersection(vals.keys()) and not self.env.context.get('skip_bo_outbound'):
            Queue = self.env['oulalab.bo.outbound.queue'].sudo()
            for tmpl in self.filtered(lambda t: t.rent_ok):
                bo_sku = (tmpl.x_bo_sku or re.sub(r'-\d{5}$', '', (tmpl.default_code or ''))).strip()
                if bo_sku:
                    Queue.enqueue_sku_stock_update(bo_sku, event_type='product.updated')
        return res
