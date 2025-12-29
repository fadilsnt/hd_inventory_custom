from odoo import models, fields
from datetime import datetime

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

        report_date = self.date.strftime('%d-%m-%Y')
        warehouse_name = self.warehouse_id.name if self.warehouse_id else 'Semua Gudang'

        filename = f"Laporan Harian {warehouse_name} - {report_date}"

        report_obj = self.env.ref(
            'hd_inventory_custom.inventory_laporan_hari_pengganti_xlsx'
        )

        report_obj.name = filename

        return report_obj.report_action(self, data={
            'date': self.date,
            'warehouse_id': self.warehouse_id.id if self.warehouse_id else False,
        })
