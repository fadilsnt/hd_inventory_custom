from odoo import http
from odoo.http import request
from odoo.http import content_disposition
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrderXlsx(http.Controller):

    def _build_filename(self, start_date=None, end_date=None):
        filename = "Purchase Order"
        if start_date and end_date:
            filename += f" {start_date} - {end_date}"
        elif start_date:
            filename += f" from {start_date}"
        elif end_date:
            filename += f" until {end_date}"
        filename += ".xlsx"
        return filename

    @http.route('/purchase/xlsx_report', type='http', auth='user')
    def generate_report_po_xlsx(self, start_date=None, end_date=None, **kw):

        _logger.info("📥 CONTROLLER RAW start_date=%s end_date=%s",
                    start_date, end_date)

        fmt = "%Y-%m-%d"
        try:
            start_dt = datetime.strptime(start_date, fmt) if start_date else None
            end_dt = datetime.strptime(end_date, fmt) if end_date else None
        except ValueError:
            return "❌ Format tanggal salah (yyyy-mm-dd)"

        _logger.info("📥 PARSED start_dt=%s end_dt=%s", start_dt, end_dt)

        if start_dt and end_dt and end_dt < start_dt:
            return "❌ End Date tidak boleh lebih kecil dari Start Date"

        domain = []
        if start_dt:
            domain.append(('date_order', '>=', start_dt))
        if end_dt:
            domain.append(('date_order', '<=', end_dt))

        _logger.info("🔎 DOMAIN: %s", domain)

        orders = request.env['purchase.order'].search(domain)
        _logger.info("📊 PO FOUND: %s", len(orders))

        xlsx_data = orders.print_xlsx_report(
            start_dt.strftime("%d/%m/%Y") if start_dt else None,
            end_dt.strftime("%d/%m/%Y") if end_dt else None,
        )

        return request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition("Purchase Order.xlsx")),
            ]
        )
