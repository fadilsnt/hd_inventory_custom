from odoo import models, fields, api

class WizardBuatLaporanHarianPicking(models.TransientModel):
    _name = 'wizard.buat.laporan.harian.picking'
    _description = "Wizard Buat Laporan Harian Picking"

    picking_id = fields.Many2one('stock.picking', required=True, readonly=True)
    oven_number = fields.Char(string="Nomor Oven")
    production_date = fields.Date(string="Tanggal Produksi")
    product_line_ids = fields.One2many('wizard.buat.laporan.harian.picking.line', 'wizard_id', string="Product Lines")
    location_dest_id = fields.Many2one('stock.location', 'To', domain="[('usage', '!=', 'view')]", check_company=True, required=True, readonly=True)

    def action_apply(self):
        self.ensure_one()

        for line in self.product_line_ids:
            move = self.picking_id.move_ids.filtered(lambda m: m.product_id == line.product_id)[:1]

            if not move:
                move = self.env['stock.move'].create({
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

            self.env['stock.move.line'].create({
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
            })
            
class WizardBuatLaporanHarianPickingLine(models.TransientModel):
    _name = 'wizard.buat.laporan.harian.picking.line'
    _description = "Wizard Line"

    wizard_id = fields.Many2one('wizard.buat.laporan.harian.picking', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string="Qty")