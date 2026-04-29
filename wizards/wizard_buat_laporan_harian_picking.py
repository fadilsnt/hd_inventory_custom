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
        return self.sudo().with_context(bypass_move_rule=True)._action_apply()

    def _action_apply(self):
        self = self.sudo()

        Move = self.env['stock.move'].sudo()
        MoveLine = self.env['stock.move.line'].sudo()

        for line in self.product_line_ids:
            move = self._get_or_create_move(line, Move)
            self._upsert_move_line(move, line, MoveLine)

    def _get_or_create_move(self, line, Move):
        move = Move.search([
            ('picking_id', '=', self.picking_id.id),
            ('product_id', '=', line.product_id.id),
            ('product_uom', '=', line.product_uom_id.id),
        ], limit=1)

        if not move:
            move = Move.create({
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'product_uom': line.product_uom_id.id,
                'picking_id': self.picking_id.id,
                'location_id': self.picking_id.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
        else:
            move.write({
                'product_uom_qty': move.product_uom_qty + line.qty
            })

        return move

    def _get_existing_move_line(self, move, line):
        return self.env['stock.move.line'].sudo().search([
            ('move_id', '=', move.id),
            ('product_id', '=', line.product_id.id),
            ('product_uom_id', '=', line.product_uom_id.id), 
        ])
    
    def _is_same_key(self, ml):
        wizard = self.sudo()
        ml = ml.sudo()
        return (
            (ml.oven_number or False) == (wizard.oven_number or False) and
            (ml.production_date or False) == (wizard.production_date or False) and
            (ml.line_packing or False) == (wizard.line_packing or False) and
            (ml.camp_tgl_briket or False) == (wizard.camp_tgl_briket or False) and
            (ml.briket_tgu or False) == (wizard.briket_tgu or False) and
            (ml.shift_briket or False) == (wizard.shift_briket or False) and
            (ml.bkr or False) == (wizard.bkr or False) and
            (ml.pembakar_penutup or False) == (wizard.pembakar_penutup or False) and
            (ml.asumsi_berat_ikat or False) == (wizard.asumsi_berat_ikat or False)
        )    

    def _prepare_move_line_vals(self, move, line):
        wizard = self.sudo()
        move = move.sudo()

        return {
            'from_wizard': True,
            'picking_id': wizard.picking_id.id,
            'move_id': move.id,
            'product_id': line.product_id.id,
            'quantity': line.qty,
            'product_uom_id': line.product_uom_id.id,
            'location_id': move.location_id.id,
            'location_dest_id': wizard.location_dest_id.id,
            'owner_id': move.owner_id.id,
            'oven_number': wizard.oven_number,
            'production_date': wizard.production_date,
            'line_packing': wizard.line_packing,
            'camp_tgl_briket': wizard.camp_tgl_briket,
            'briket_tgu': wizard.briket_tgu,
            'shift_briket': wizard.shift_briket,
            'bkr': wizard.bkr,
            'pembakar_penutup': wizard.pembakar_penutup,
            'asumsi_berat_ikat': wizard.asumsi_berat_ikat,
        }

    def _upsert_move_line(self, move, line, MoveLine):
        candidates = MoveLine.search([
            ('move_id', '=', move.id),
            ('product_id', '=', line.product_id.id),
            ('product_uom_id', '=', line.product_uom_id.id),
        ])

        wizard = self.sudo()

        matched = candidates.filtered(lambda ml: wizard._is_same_key(ml))

        if matched:
            matched[0].write({
                'quantity': matched[0].quantity + line.qty
            })
        else:
            vals = self._prepare_move_line_vals(move, line)
            MoveLine.create(vals)

class WizardBuatLaporanHarianPickingLine(models.TransientModel):
    _name = 'wizard.buat.laporan.harian.picking.line'
    _description = "Wizard Line"

    wizard_id = fields.Many2one('wizard.buat.laporan.harian.picking', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product")
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id', store=False, readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")

    qty = fields.Float(string="Qty")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
        else:
            self.product_uom_id = False