# -*- coding: utf-8 -*-
from odoo import models, api, fields, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    pemilik_ids = fields.Many2many(
        'res.partner',
        'stock_picking_owner_rel',
        'picking_id',
        'partner_id',
        string="Owners",
        help="Owner yang terlibat pada stock move."
    )

    @api.model
    def create(self, vals):
        picking = super().create(vals)

        if picking.move_ids:
            owners = picking.move_ids.mapped('owner_id')
            picking.with_context(skip_owner_sync=True).pemilik_ids = [(6, 0, owners.ids)]

        return picking

    def write(self, vals):
        res = super().write(vals)

        if self.env.context.get('skip_owner_sync'):
            return res

        for picking in self:
            owners = picking.move_ids.mapped('owner_id')

            picking.with_context(skip_owner_sync=True).pemilik_ids = [(6, 0, owners.ids)]

        return res
