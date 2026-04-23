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
        # 🔑 jangan override kalau dari wizard
        if not vals.get('from_wizard'):
            if not vals.get('product_uom_id') and vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])

                if vals.get('move_id'):
                    move = self.env['stock.move'].browse(vals['move_id'])
                    vals['product_uom_id'] = move.product_uom.id or product.uom_id.id
                else:
                    vals['product_uom_id'] = product.uom_id.id

        return super().create(vals)

    @api.constrains('product_uom_id', 'product_id')
    def _check_uom_category(self):
        for rec in self:
            if rec.product_uom_id and rec.product_id:
                if rec.product_uom_id.category_id != rec.product_id.uom_id.category_id:
                    raise ValueError("Kategori UoM tidak sesuai dengan produk.")
