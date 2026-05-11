# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    owner_id = fields.Many2one(comodel_name='res.partner', string="Pemilik", related='product_id.owner_id', store=True, readonly=False)
    sales_person_ids = fields.Many2many('res.users', string="Sales Persons", compute='_compute_sales_person_ids', inverse='_inverse_sales_person_ids', store=False)
    is_consume = fields.Boolean(string="Is Consume", default=False)
    sparepart_category_id = fields.Many2one('product.category', string="Sparepart Category", default=lambda self: self.env.ref('hd_inventory_custom.product_category_sparepart', raise_if_not_found=False))

    @api.depends('product_id.sales_person_ids')
    def _compute_sales_person_ids(self):
        for move in self:
            move.sales_person_ids = move.product_id.sales_person_ids

    def _inverse_sales_person_ids(self):
        for move in self:
            move.product_id.sales_person_ids = move.sales_person_ids

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)

        if not vals.get('owner_id') and self.owner_id:
            vals['owner_id'] = self.owner_id.id

        return vals
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') and vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['name'] = product.display_name

        return super().create(vals_list)    
    
    def write(self, vals):
        if vals.get('product_id') and not vals.get('name'):
            product = self.env['product.product'].browse(vals['product_id'])
            vals['name'] = product.display_name

        return super().write(vals)    