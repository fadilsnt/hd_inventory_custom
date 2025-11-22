# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    owner_id = fields.Many2one(comodel_name='res.partner', string="Pemilik", related='product_id.owner_id', store=True, readonly=False)
    sales_person_ids = fields.Many2many(
        'res.users',
        string="Sales Persons",
        compute='_compute_sales_person_ids',
        inverse='_inverse_sales_person_ids',
        store=False,
    )

    @api.depends('product_id.sales_person_ids')
    def _compute_sales_person_ids(self):
        for move in self:
            move.sales_person_ids = move.product_id.sales_person_ids

    def _inverse_sales_person_ids(self):
        for move in self:
            move.product_id.sales_person_ids = move.sales_person_ids

