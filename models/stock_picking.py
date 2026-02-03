# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from dateutil.relativedelta import relativedelta
from datetime import timedelta

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    pemilik_ids = fields.Many2many('res.partner', 'stock_picking_owner_rel', 'picking_id', 'owner_id', string="Owners", help="Owner yang terlibat pada stock move.")
    btb_number = fields.Char(string="No. BTB", readonly=True, copy=False)

    def _get_bulan_romawi(self, bulan):
        romawi = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV',
            5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII',
            9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'
        }
        return romawi.get(bulan, '')

    def button_validate(self):
        res = super().button_validate()

        for picking in self.filtered(lambda p: p.picking_type_code == 'incoming'):
            if not picking.btb_number:
                date_done = picking.date_done or fields.Datetime.now()
                date_done_dt = fields.Datetime.context_timestamp(picking, date_done)

                tahun = date_done_dt.strftime('%y')
                bulan_romawi = self._get_bulan_romawi(date_done_dt.month)

                domain = [
                    ('picking_type_code', '=', 'incoming'),
                    ('btb_number', '!=', False),
                    ('date_done', '>=', date_done_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)),
                    ('date_done', '<=', date_done_dt.replace(day=1, hour=23, minute=59, second=59, microsecond=999999)
                                + relativedelta(months=1) - timedelta(microseconds=1))
                ]
                last = self.env['stock.picking'].search(domain, order='btb_number desc', limit=1)

                if last:
                    last_urutan = int(last.btb_number.split('/')[1])
                    urutan = last_urutan + 1
                else:
                    urutan = 1

                warehouse = picking.picking_type_id.warehouse_id
                warehouse_code = warehouse.code if warehouse else 'NA'

                btb = 'BTB/%02d/%s/%s/%s' % (
                    urutan,
                    bulan_romawi,
                    tahun,
                    warehouse_code
                )
                picking.btb_number = btb

                # update PO
                po_ids = picking.move_ids.mapped('purchase_line_id.order_id')
                if po_ids:
                    po_ids.write({'btb_number': btb})

        return res

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
