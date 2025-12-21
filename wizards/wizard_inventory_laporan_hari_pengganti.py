from odoo import models, fields

class WizardInventoryLaporanHariPengganti(models.TransientModel):
    _name = 'wizard.inventory.laporan.hari.pengganti'
    _description = "Wizard Inventory Laporan Hari Pengganti"

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.context_today
    )

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string="Warehouse",
        required=False
    )

    def action_print_xlsx_report(self):
        self.ensure_one()
        data = {
            'date': self.date,
            'warehouse_id': self.warehouse_id,
        }
        return self.env.ref('hd_inventory_custom.inventory_laporan_hari_pengganti_xlsx').report_action(self, data=data)