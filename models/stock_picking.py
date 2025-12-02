# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    owner_id = fields.Many2one(
        'res.partner',
        string="Owner",
        help="Owner akan otomatis mengikuti owner dari Stock Move pertama."
    )

    @api.model
    def create(self, vals):
        picking = super().create(vals)

        if picking.move_ids and not picking.owner_id:
            picking.owner_id = picking.move_ids[0].owner_id.id

        return picking

    def write(self, vals):
        res = super().write(vals)

        # Setelah perubahan, lakukan cek konsistensi owner
        for picking in self:

            owners = picking.move_ids.mapped('owner_id')
            owners = list(set(owners))

            # Jika tidak ada owner, tidak perlu dicek
            if not owners:
                continue

            # Jika owner lebih dari 1 → ERROR
            if len(owners) > 1:
                raise UserError(
                    _("Semua stock move pada picking ini harus memiliki owner yang sama.")
                )

            # Jika picking.owner_id belum diisi, isi otomatis dari owner move
            if not picking.owner_id:
                picking.owner_id = owners[0]

        return res
