from odoo import models, fields, api, _

class WizardBuatLaporanHarianPicking(models.TransientModel):
    _name = 'wizard.buat.laporan.harian.picking'
    _description = "Wizard Buat Laporan Harian Picking"

    picking_id = fields.Many2one('stock.picking', required=True, readonly=True)
    oven_number = fields.Char(string="Nomor Oven")
    production_date = fields.Date(string="Tanggal Produksi")
    product_line_ids = fields.One2many('wizard.buat.laporan.harian.picking.line', 'wizard_id', string="Product Lines")
    location_dest_id = fields.Many2one('stock.location', 'To', domain="[('usage', '!=', 'view')]", check_company=True, required=True, readonly=True)

    line_packing = fields.Char(string="Line")
    camp_tgl_briket = fields.Char(string="Camp/TGL Briket")
    briket_tgu = fields.Char(string="Briket TGU (Jam)")
    shift_briket = fields.Char(string="Shift Briket/PA")
    bkr = fields.Char(string="BKR (HR/Jam/Kroak)")
    pembakar_penutup = fields.Char(string="Pembakar / Penutup")
    asumsi_berat_ikat = fields.Char(string="Asumsi Berat @Ikat")
                
    def action_apply(self):
        self.ensure_one()

        for line in self.product_line_ids:
            move = self._get_or_create_move(line)
            self._upsert_move_line(move, line)

    def _get_or_create_move(self, line):
        move = self.picking_id.move_ids.filtered(
            lambda m: m.product_id == line.product_id
        )[:1]

        if not move:
            move = self.env['stock.move'].sudo().create({
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': self.picking_id.id,
                'location_id': self.picking_id.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
        else:
            move.product_uom_qty += line.qty

        return move

    def _get_existing_move_line(self, move, line):
        return self.env['stock.move.line'].sudo().search([
            ('move_id', '=', move.id),
            ('product_id', '=', line.product_id.id),
        ])    
    
    def _is_same_key(self, ml):
        return (
            (ml.oven_number or False) == (self.oven_number or False) and
            (ml.production_date or False) == (self.production_date or False) and
            (ml.line_packing or False) == (self.line_packing or False) and
            (ml.camp_tgl_briket or False) == (self.camp_tgl_briket or False) and
            (ml.briket_tgu or False) == (self.briket_tgu or False) and
            (ml.shift_briket or False) == (self.shift_briket or False) and
            (ml.bkr or False) == (self.bkr or False) and
            (ml.pembakar_penutup or False) == (self.pembakar_penutup or False) and
            (ml.asumsi_berat_ikat or False) == (self.asumsi_berat_ikat or False)
        )    

    def _prepare_move_line_vals(self, move, line):
        return {
            'picking_id': self.picking_id.id,
            'move_id': move.id,
            'product_id': line.product_id.id,
            'quantity': line.qty,
            'product_uom_id': line.product_id.uom_id.id,
            'location_id': move.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'owner_id': move.owner_id.id,
            'oven_number': self.oven_number,
            'production_date': self.production_date,
            'line_packing': self.line_packing,
            'camp_tgl_briket': self.camp_tgl_briket,
            'briket_tgu': self.briket_tgu,
            'shift_briket': self.shift_briket,
            'bkr': self.bkr,
            'pembakar_penutup': self.pembakar_penutup,
            'asumsi_berat_ikat': self.asumsi_berat_ikat
        }

    def _upsert_move_line(self, move, line):
        candidates = self._get_existing_move_line(move, line)

        matched = candidates.filtered(lambda ml: self._is_same_key(ml))

        if matched:
            matched[0].quantity += line.qty
        else:
            vals = self._prepare_move_line_vals(move, line)
            self.env['stock.move.line'].sudo().create(vals)

class WizardBuatLaporanHarianPickingLine(models.TransientModel):
    _name = 'wizard.buat.laporan.harian.picking.line'
    _description = "Wizard Line"

    wizard_id = fields.Many2one('wizard.buat.laporan.harian.picking', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product")
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id', store=False, readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]", readonly=True)

    qty = fields.Float(string="Qty")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
        else:
            self.product_uom_id = False