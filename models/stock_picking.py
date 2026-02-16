# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    _sql_constraints = [
        ('btb_number_unique', 'unique(btb_number)', 'BTB number must be unique!')
    ]

    pemilik_ids = fields.Many2many(
        'res.partner',
        'stock_picking_owner_rel',
        'picking_id',
        'owner_id',
        string="Owners",
        help="Owner yang terlibat pada stock move."
    )

    btb_number = fields.Char(string="No. BTB", readonly=True, copy=False)

    partner_ref = fields.Char(
        'Vendor Reference',
        copy=False,
        help="Reference of the sales order or bid sent by the vendor."
    )

    def _get_bulan_romawi(self, bulan):
        romawi = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV',
            5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII',
            9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'
        }
        return romawi.get(bulan, '')

    @api.model
    def create(self, vals):
        picking = super().create(vals)

        # hanya untuk incoming
        if picking.picking_type_code != 'incoming' or picking.btb_number:
            return picking

        date_now = fields.Datetime.context_timestamp(
            picking, fields.Datetime.now()
        )

        tahun = date_now.strftime('%y')
        bulan_romawi = self._get_bulan_romawi(date_now.month)

        start_month = date_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_month = (start_month + relativedelta(months=1)) - timedelta(microseconds=1)

        domain = [
            ('picking_type_code', '=', 'incoming'),
            ('btb_number', '!=', False),
            ('create_date', '>=', start_month),
            ('create_date', '<=', end_month),
        ]

        last = self.env['stock.picking'].sudo().search(
            domain,
            order='id desc',
            limit=1
        )

        if last and last.btb_number:
            try:
                last_urutan = int(last.btb_number.split('/')[1])
                urutan = last_urutan + 1
            except Exception:
                urutan = 1
        else:
            urutan = 1

        warehouse = picking.picking_type_id.warehouse_id
        warehouse_code = warehouse.code if warehouse else 'NA'

        btb_number = 'BTB/%02d/%s/%s/%s' % (
            urutan,
            bulan_romawi,
            tahun,
            warehouse_code
        )

        picking.sudo().write({'btb_number': btb_number})

        if picking.origin:
            po = self.env['purchase.order'].sudo().search([
                ('name', '=', picking.origin)
            ], limit=1)

            if po:
                po.write({'btb_number': btb_number})
        return picking

    def write(self, vals):
        res = super().write(vals)

        if 'move_ids' in vals:
            for picking in self:
                owners = picking.move_ids.mapped('owner_id')
                picking.with_context(skip_owner_sync=True).sudo().update({
                    'pemilik_ids': [(6, 0, owners.ids)]
                })

        return res
