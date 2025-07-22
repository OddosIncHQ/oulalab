# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_es_prenda_arrendable = fields.Boolean(
        string='Es Prenda Arrendable',
        default=False,
        help='Indica si este producto puede ser arrendado como prenda.'
    )
