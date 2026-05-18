from odoo import models, fields, api, _

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    oven_number = fields.Char(string="Nomor Oven")
    production_date = fields.Date(string="Tanggal Produksi")
    line_packing = fields.Char(string="Line")
    camp_tgl_briket = fields.Char(string="Camp/TGL Briket")
    briket_tgu = fields.Char(string="Briket TGU (Jam)")
    shift_briket = fields.Char(string="Shift Briket/PA")
    bkr = fields.Char(string="BKR (HR/Jam/Kroak)")
    pembakar_penutup = fields.Char(string="Pembakar / Penutup")
    asumsi_berat_ikat = fields.Char(string="Asumsi Berat @Ikat")    
    from_wizard = fields.Boolean(default=False)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, domain="[('category_id', '=', product_uom_category_id)]", readonly=True)

    @api.onchange('product_id', 'move_id')
    def _onchange_product_uom_id(self):
        for line in self:
            if not line.product_id:
                continue

            if line.from_wizard:
                continue

            if line.move_id and line.move_id.product_uom:
                line.product_uom_id = line.move_id.product_uom
            else:
                line.product_uom_id = line.product_id.uom_id    

    @api.model
    def create(self, vals):
        if not vals.get('from_wizard'):
            if not vals.get('product_uom_id') and vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])

                if vals.get('move_id'):
                    move = self.env['stock.move'].browse(vals['move_id'])
                    vals['product_uom_id'] = move.product_uom.id or product.uom_id.id
                else:
                    vals['product_uom_id'] = product.uom_id.id

        return super().create(vals)

    def _find_or_create_move(self, product_uom_id):
        self.ensure_one()

        Move = self.env['stock.move']

        move = Move.search([
            ('picking_id', '=', self.picking_id.id),
            ('product_id', '=', self.product_id.id),
            ('product_uom', '=', product_uom_id),
            ('state', 'not in', ('done', 'cancel')),
        ], limit=1)

        if move:
            return move

        return Move.sudo().with_context(
            tracking_disable=True,
            mail_notrack=True,
            mail_create_nosubscribe=True,
        ).create({
            'name': self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_qty': 0,
            'product_uom': product_uom_id,
            'picking_id': self.picking_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
        })        
    
    def write(self, vals):
        old_moves = self.mapped('move_id')
        uom_changed = 'product_uom_id' in vals

        res = super().write(vals)

        # =================================================
        # PINDAH MOVE JIKA UOM BERUBAH
        # =================================================
        if uom_changed:
            for line in self:

                target_move = line._find_or_create_move(
                    line.product_uom_id.id
                )

                if line.move_id != target_move:
                    line.sudo().with_context(
                        tracking_disable=True,
                        mail_notrack=True,
                        mail_create_nosubscribe=True,
                    ).write({
                        'move_id': target_move.id
                    })

        # =================================================
        # RECOMPUTE QTY
        # =================================================
        all_moves = old_moves | self.mapped('move_id')
        all_moves._recompute_quantities()

        return res

    def unlink(self):
        moves = self.mapped('move_id')
        res = super().unlink()
        moves._recompute_quantities()

        return res

    @api.constrains('product_uom_id', 'product_id')
    def _check_uom_category(self):
        for rec in self:
            if rec.product_uom_id and rec.product_id:
                if rec.product_uom_id.category_id != rec.product_id.uom_id.category_id:
                    raise ValueError("Kategori UoM tidak sesuai dengan produk.")
