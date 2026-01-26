import logging
from odoo import models, fields, api, _
import io
import xlsxwriter
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    btb_number = fields.Char(string="No. BTB", readonly=True, copy=False)
    vendor_invoice_date = fields.Date(string="Tanggal Invoice Vendor")

    def action_print_btb(self):
        self.ensure_one()
        return self.env.ref('hd_inventory_custom.action_report_bukti_terima_barang').report_action(self)    

    def print_xlsx_report(self, start_date=None, end_date=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("REKAP PEMBELIAN")

        # ================= FORMAT =================
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center'
        })
        header_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_fmt = workbook.add_format({
            'border': 1, 'valign': 'top'
        })
        right_fmt = workbook.add_format({
            'border': 1, 'align': 'right'
        })
        bold_fmt = workbook.add_format({'bold': True})

        # ================= COLUMN WIDTH =================
        sheet.set_column('A:A', 5)    # NO
        sheet.set_column('B:B', 12)   # NO. BTB
        sheet.set_column('C:C', 35)   # KETERANGAN BARANG
        sheet.set_column('D:D', 8)    # QTY
        sheet.set_column('E:E', 15)   # HARGA
        sheet.set_column('F:F', 15)   # TOTAL
        sheet.set_column('G:G', 18)   # GRAND TOTAL

        # ================= HEADER =================
        sheet.merge_range('A2:G2', 'REKAP PEMBELIAN', title_fmt)

        sheet.merge_range('A5:B5', 'SUPPLIER', bold_fmt)
        sheet.merge_range('A6:B6', 'PERIODE', bold_fmt)
        sheet.merge_range('D5:E5', 'LOKASI PABRIK', bold_fmt)

        sheet.write('C5', '-')  # diisi via filter kalau perlu
        sheet.write('C6', f"{start_date or '-'} s/d {end_date or '-'}")
        sheet.merge_range('F5:G5', '-')  # diisi via filter kalau perlu

        # ================= TABLE HEADER =================
        row = 7
        headers = [
            "NO", "NO. BTB", "KETERANGAN BARANG",
            "QTY", "HARGA", "TOTAL", "GRAND TOTAL"
        ]
        for col, h in enumerate(headers):
            sheet.write(row, col, h, header_fmt)

        # ================= TABLE DATA (FULL QUERY) =================
        data_lines = self._get_rekap_pembelian_data(start_date, end_date)

        row += 1
        no = 1

        for line in data_lines:
            sheet.write(row, 0, no, cell_fmt)
            sheet.write(row, 1, line['no_btb'] or '', cell_fmt)
            sheet.write(row, 2, line['keterangan_barang'] or '', cell_fmt)
            sheet.write(row, 3, line['qty'] or 0, right_fmt)
            sheet.write(row, 4, line['harga'] or 0, right_fmt)
            sheet.write(row, 5, line['total'] or 0, right_fmt)
            sheet.write(row, 6, line['grand_total'] or 0, right_fmt)

            row += 1
            no += 1

        workbook.close()
        output.seek(0)
        return output.read()



    def _get_rekap_pembelian_data(self, start_date=None, end_date=None):
        # ================= NORMALIZE DATE =================
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%d/%m/%Y").date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%d/%m/%Y").date()

        query = """
            SELECT
                po.name            AS no_btb,
                rp.name            AS supplier,
                pol.name           AS keterangan_barang,
                pol.product_qty    AS qty,
                pol.price_unit     AS harga,
                pol.price_subtotal AS total,
                pol.price_total    AS grand_total
            FROM purchase_order po
            JOIN purchase_order_line pol ON pol.order_id = po.id
            LEFT JOIN res_partner rp ON rp.id = po.partner_id
            
        """

        params = []

        if start_date:
            query += "WHERE DATE(po.date_order) >= %s"
            params.append(start_date)

        if end_date:
            query += " AND DATE(po.date_order) <= %s"
            params.append(end_date)

        query += " ORDER BY po.name, pol.id"

        _logger.warning("🧪 FINAL SQL PARAMS (DATE CAST): %s", params)

        self.env.cr.execute(query, params)
        rows = self.env.cr.dictfetchall()

        _logger.warning("📊 QUERY RESULT COUNT: %s", len(rows))
        return rows
