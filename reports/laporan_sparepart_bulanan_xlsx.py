from odoo import models, _
from collections import defaultdict
from datetime import timedelta

class ReportLaporanSparepartXlsx(models.AbstractModel):
    _name = 'report.hd_inventory_custom.report_laporan_sparepart_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet("Laporan Sparepart")

        # =========================================================
        # FORMAT
        # =========================================================

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
        })

        subtitle_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
        })

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        subheader_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        text_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
        })

        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        })

        category_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#D9EAD3',
        })

        # =========================================================
        # COLUMN WIDTH
        # =========================================================
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 40)
        sheet.set_column('C:G', 18)

        # =========================================================
        # TITLE
        # =========================================================
        sheet.merge_range('A1:G1', 'LAPORAN SPARE PART PUSAT', title_format)
        period = wizard.start_date.strftime('%B %Y').upper()
        sheet.merge_range('A2:G2', f'BULAN {period}', subtitle_format)
        company_name = self.env.company.name or ''
        sheet.merge_range('A3:G3', company_name.upper(), subtitle_format)

        # =========================================================
        # HEADER
        # =========================================================
        sheet.merge_range('A5:A6', 'KATEGORI', header_format)
        sheet.merge_range('B5:B6', 'ITEM', header_format)
        sheet.merge_range('C5:C6', 'STOCK AWAL', header_format)

        sheet.merge_range('D5:E5', 'TERIMA', header_format)

        sheet.write('D6', 'BELI', subheader_format)
        sheet.write('E6', 'MUTASI', subheader_format)

        sheet.merge_range('F5:F6', 'PAKAI', header_format)
        sheet.merge_range('G5:G6', 'STOCK AKHIR', header_format)

        # =========================================================
        # DATA
        # =========================================================
        sparepart_category = self.env.ref('hd_inventory_custom.product_category_sparepart', raise_if_not_found=False)
        usage_location = self.env.ref('hd_inventory_custom.stock_location_sparepart_usage', raise_if_not_found=False)

        if not sparepart_category:
            return

        domain_product = [
            ('categ_id', 'child_of', sparepart_category.id),
            ('categ_id', '!=', sparepart_category.id),
        ]

        products = self.env['product.product'].search(domain_product, order='categ_id, name')
        grouped_products = defaultdict(list)

        for product in products:
            grouped_products[product.categ_id].append(product)

        row = 6

        date_before = wizard.start_date - timedelta(days=1)

        for category, category_products in grouped_products.items():
            # =====================================================
            # CATEGORY
            # =====================================================

            sheet.merge_range(row, 0, row, 6, (category.name or '').upper(), category_format)
            row += 1

            for product in category_products:

                # =================================================
                # STOCK AWAL
                # =================================================

                stock_awal = product.with_context(warehouse=wizard.warehouse_id.id if wizard.warehouse_id else False, to_date=date_before,).qty_available

                # =================================================
                # QTY MASUK (BELI)
                # =================================================

                qty_beli = 0.0

                incoming_moves = self.env['stock.move'].search([
                    ('product_id', '=', product.id),
                    ('state', '=', 'done'),
                    ('date', '>=', wizard.start_date),
                    ('date', '<=', wizard.end_date),
                    ('picking_id.picking_type_id.code', '=', 'incoming'),
                ])

                qty_beli = sum(incoming_moves.mapped('product_uom_qty'))

                # =================================================
                # QTY MUTASI
                # =================================================

                qty_mutasi = 0.0

                internal_moves = self.env['stock.move'].search([
                    ('product_id', '=', product.id),
                    ('state', '=', 'done'),
                    ('date', '>=', wizard.start_date),
                    ('date', '<=', wizard.end_date),
                    ('picking_id.picking_type_id.code', '=', 'internal'),
                    ('location_dest_id', '!=', usage_location.id if usage_location else False),
                ])

                qty_mutasi = sum(internal_moves.mapped('product_uom_qty'))

                # =================================================
                # QTY PAKAI
                # =================================================

                qty_pakai = 0.0

                if usage_location:
                    usage_moves = self.env['stock.move'].search([
                        ('product_id', '=', product.id),
                        ('state', '=', 'done'),
                        ('date', '>=', wizard.start_date),
                        ('date', '<=', wizard.end_date),
                        ('location_dest_id', '=', usage_location.id),
                    ])

                    qty_pakai = sum(usage_moves.mapped('product_uom_qty'))

                # =================================================
                # STOCK AKHIR
                # =================================================

                stock_akhir = (
                    stock_awal
                    + qty_beli
                    - qty_mutasi
                    - qty_pakai
                )

                # =================================================
                # WRITE ROW
                # =================================================
                sheet.write(row, 0, "", text_format)
                sheet.write(row, 1, product.display_name, text_format)

                sheet.write_number(row, 2, stock_awal, number_format)
                sheet.write_number(row, 3, qty_beli, number_format)
                sheet.write_number(row, 4, qty_mutasi, number_format)
                sheet.write_number(row, 5, qty_pakai, number_format)
                sheet.write_number(row, 6, stock_akhir, number_format)

                row += 1