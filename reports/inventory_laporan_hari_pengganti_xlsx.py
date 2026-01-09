from odoo import models
from datetime import datetime, date
import re
import json
import logging

_logger = logging.getLogger(__name__)

def format_tanggal_indonesia(dt=None):
    hari_map = {0: "SENIN", 1: "SELASA", 2: "RABU", 3: "KAMIS", 4: "JUMAT", 5: "SABTU", 6: "MINGGU"}
    bulan_map = {1: "JANUARI", 2: "FEBRUARI", 3: "MARET", 4: "APRIL", 5: "MEI", 6: "JUNI", 
                 7: "JULI", 8: "AGUSTUS", 9: "SEPTEMBER", 10: "OKTOBER", 11: "NOVEMBER", 12: "DESEMBER"}

    if not dt:
        dt = date.today()
    elif isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d").date()

    return "{} / {} {} {}".format(hari_map[dt.weekday()], dt.day, bulan_map[dt.month], dt.year)

def _grade_sort_key(grade):
    if grade == "UNCLASSIFIED":
        return (99, "")

    m = re.match(r'^([A-Z]+)', grade)
    grade_key = m.group(1) if m else grade

    grade_order = {
        'A': 1,
        'B': 2,
        'BC': 3,
        'C': 4,
        'D': 5, 
    }

    return (grade_order.get(grade_key, 50), grade_key)

def _get_oven_key(oven, prod_date):
    if not oven:
        return "NONE"

    if prod_date:
        if isinstance(prod_date, str):
            prod_date = datetime.strptime(prod_date, "%Y-%m-%d").date()
        elif isinstance(prod_date, datetime):
            prod_date = prod_date.date()

        if isinstance(prod_date, date):
            return f"{oven} ({prod_date.strftime('%d/%m')})"

    return oven

class InventoryLaporanHariPenggantiXlsx(models.AbstractModel):
    _name = 'report.hd_inventory_custom.hari_pengganti_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Laporan Inventory Hari Pengganti XLSX'
    _auto = False 

    def _get_data_xlsx_report(self, report_date, warehouse_id=None):
        warehouse_filter = ""
        params = {'report_date': report_date}
        
        if warehouse_id:
            warehouse_filter = "AND sw.id = %(warehouse_id)s"
            params['warehouse_id'] = warehouse_id

        query = f"""
            WITH base_move AS (
                SELECT
                    sw.name AS warehouse,
                    sml.oven_number AS oven,
                    sml.production_date AS production_date,
                    sml.product_id,
                    SUM(sml.quantity) AS qty,
                    sml.product_uom_id
                FROM stock_move_line sml
                JOIN stock_move sm ON sml.move_id = sm.id
                JOIN stock_picking sp ON sm.picking_id = sp.id
                JOIN stock_location sl ON sl.id = sml.location_dest_id
                JOIN stock_warehouse sw
                    ON (sl.id = sw.view_location_id
                    OR sl.parent_path LIKE '%%/' || sw.view_location_id || '/%%')
                WHERE sp.scheduled_date::date = %(report_date)s
                AND sp.state IN ('confirmed', 'assigned', 'done')
                {warehouse_filter}
                GROUP BY sw.name, sml.oven_number, sml.production_date, sml.product_id, sml.product_uom_id
            ),
            base_data AS (
                SELECT
                    bm.warehouse,
                    bm.oven,
                    bm.production_date,
                    pt.name->>'en_US' AS product,
                    pc.name AS product_category,
                    uu.name->>'en_US' AS uom_category,
                    -- uc.name->>'en_US' AS uom_category,
                    MAX(CASE WHEN pa.name->>'en_US' = 'Grade' THEN pav.name->>'en_US' END)
                        || ' (' ||
                    MAX(CASE WHEN pa.name->>'en_US' = 'BOX' THEN pav.name->>'en_US' END)
                        || ')' AS classification,
                    bm.qty
                FROM base_move bm
                JOIN product_product pp ON bm.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                -- Tambahan JOIN untuk category & uom
                LEFT JOIN product_category pc ON pt.categ_id = pc.id
                LEFT JOIN uom_uom uu ON uu.id = bm.product_uom_id
                --LEFT JOIN uom_category uc ON pt.uom_category_id = uc.id
                LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
                LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
                LEFT JOIN product_attribute pa ON pa.id = ptav.attribute_id
                LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
                GROUP BY
                    bm.warehouse,
                    bm.oven,
                    bm.production_date,
                    pt.name->>'en_US',
                    pc.name,
                    -- uc.name->>'en_US',
                    uu.name,
                    bm.qty
            ),
            oven_group AS (
                SELECT
                    warehouse,
                    oven,
                    production_date,
                    classification,
                    product_category,
                    uom_category,
                    json_agg(
                        json_build_object(
                            'product', product,
                            'qty', qty
                        ) ORDER BY product
                    ) AS products,
                    SUM(qty) AS total_per_oven
                FROM base_data
                GROUP BY warehouse, oven, production_date, classification, product_category, uom_category
            ),
            total_per_grade_cte AS (
                SELECT
                    warehouse,
                    COALESCE(classification,'UNCLASSIFIED') AS classification,
                    SUM(total_per_oven) AS total_per_grade
                FROM oven_group
                GROUP BY warehouse, COALESCE(classification,'UNCLASSIFIED')
            ),
            warehouse_group AS (
                SELECT
                    og.warehouse,
                    json_agg(
                        json_build_object(
                            'oven', og.oven,
                            'production_date', og.production_date,
                            'classification', og.classification,
                            'product_category', og.product_category,
                            'uom_category', og.uom_category,
                            'products', og.products,
                            'total_per_oven', og.total_per_oven
                        )
                        ORDER BY og.oven
                    ) AS ovens,
                    json_object_agg(COALESCE(tpg.classification,'UNCLASSIFIED'), tpg.total_per_grade) AS total_per_grade
                FROM oven_group og
                LEFT JOIN total_per_grade_cte tpg
                    ON og.warehouse = tpg.warehouse
                    AND og.classification = tpg.classification
                GROUP BY og.warehouse
            )
            SELECT json_object_agg(
                warehouse,
                json_build_object(
                    'ovens', ovens,
                    'total_per_grade', total_per_grade
                )
            )
            FROM warehouse_group;
        """
        self.env.cr.execute(query, params)
        row = self.env.cr.fetchone()

        if row and row[0]:
            try:
                pretty_json = json.dumps(row[0], indent=2, ensure_ascii=False)
                _logger.info("Isi Querynya:\n%s", pretty_json)
            except Exception as e:
                _logger.error("Gagal mem-parse JSON dari query: %s", e)
                _logger.info("Raw query result: %s", row[0])
        else:
            _logger.info("Query mengembalikan hasil kosong.")

        return row[0] if row and row[0] else {}

    def generate_xlsx_report(self, workbook, data, wizard):
        report_date = data.get('date')
        warehouse_id = data.get('warehouse_id')

        # === NORMALISASI WAREHOUSE ===
        warehouse = None
        if warehouse_id:
            if isinstance(warehouse_id, int):
                warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            elif hasattr(warehouse_id, 'id'):  
                warehouse = warehouse_id
            elif isinstance(warehouse_id, str) and 'stock.warehouse' in warehouse_id:
                match = re.search(r'\((\d+),?\)', warehouse_id)
                if match:
                    warehouse = self.env['stock.warehouse'].browse(int(match.group(1)))

        date_today = format_tanggal_indonesia(report_date)
        data_report = self._get_data_xlsx_report(report_date, warehouse.id if warehouse else None)

        # =========================================================
        # RENDER SHEET
        # =========================================================
        def _render_sheet(sheet, warehouse_name, ovens, total_per_grade=None):
            # ================= FORMATS =================
            fmt_header = workbook.add_format({'border': 1, 'bold': True, 'align': 'center', 'valign': 'vcenter'})
            fmt_label = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            fmt_header_packing = workbook.add_format({'border': 1, 'bold': True, 'align': 'left', 'valign': 'vcenter'})
            fmt_number = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            fmt_text_center = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            fmt_total = workbook.add_format({'border': 1, 'bold': True, 'align': 'right', 'valign': 'vcenter'})
            fmt_grade_total = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter'})
            fmt_grade = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter', 'bold': True})

            # ================= OVEN LIST =================
            oven_list = []

            for o in ovens:
                oven_key = _get_oven_key(o.get("oven"), o.get("production_date"))

                if oven_key not in oven_list:
                    oven_list.append(oven_key)

            # ================= TITLE =================
            total_oven = len(oven_list)
            total_cols = 1 + (total_oven * 2)
            last_col = total_cols - 1
            warehouse_end_col = int((total_cols - 1) * 0.7)
            date_start_col = min(warehouse_end_col + 1, last_col)

            sheet.merge_range(0, 0, 0, warehouse_end_col, f"Gudang {warehouse_name}", fmt_label)
            if date_start_col == last_col:
                sheet.write(0, last_col, f"TANGGAL : {date_today}", fmt_label)
            else:
                sheet.merge_range(0, date_start_col, 0, last_col, f"TANGGAL : {date_today}", fmt_label)

            # ================= HEADER ROW 1 =================
            header_row = 1
            col = 0
            sheet.write(header_row, col, "PACKING", fmt_header_packing)
            col += 1
            for oven in oven_list:
                sheet.merge_range(header_row, col, header_row, col + 1, oven, fmt_header)
                col += 2

            # ================= MAP DATA =================
            data_map = {}
            total_per_oven = {}

            # ================= AGGREGATE LOKAL & FUEL =================
            aggregated_special = {}  # key: product name, value: {"qty": x, "uom": y}

            other_ovens = []

            for o in ovens:
                category = o.get("product_category")
                if category in ["LOKAL", "FUEL"]:
                    for p in o.get("products", []):
                        product_name = p.get("product")
                        qty = p.get("qty", 0)
                        uom = o.get("uom_category")
                        category = o.get("product_category")
                        if product_name in aggregated_special:
                            aggregated_special[product_name]["qty"] += qty
                        else:
                            aggregated_special[product_name] = {"qty": qty, "uom": uom, "category": category}
                else:
                    other_ovens.append(o)  # keep other products for normal mapping

            # ================= MAP OTHER OVENS =================
            for o in other_ovens:
                grade = o.get("classification") or "UNCLASSIFIED"

                oven = o.get("oven")
                prod_date = o.get("production_date")

                prod_date_obj = None
                if prod_date:
                    if isinstance(prod_date, str):
                        prod_date_obj = datetime.strptime(prod_date, "%Y-%m-%d").date()
                    elif isinstance(prod_date, (datetime, date)):
                        prod_date_obj = prod_date

                if oven and prod_date_obj:
                    oven_key = f"{oven} ({prod_date_obj.strftime('%d/%m')})"
                elif oven:
                    oven_key = oven
                else:
                    oven_key = "NONE"

                data_map.setdefault(grade, {})
                data_map[grade].setdefault(oven_key, {"qty": 0, "products": set()})
                total_per_oven.setdefault(oven_key, 0)

                for p in o.get("products", []):
                    qty = p.get("qty", 0)
                    data_map[grade][oven_key]["qty"] += qty
                    data_map[grade][oven_key]["products"].add(p.get("product"))
                    total_per_oven[oven_key] += qty

            # ================= COMPUTE TOTAL PER GRADE =================
            if total_per_grade is None:
                total_per_grade = {}
                for grade in sorted(data_map.keys(), key=_grade_sort_key):
                    oven_data = data_map[grade]

            unclassified_total = sum(
                p.get("qty", 0)
                for o in ovens
                if not o.get("classification")
                for p in o.get("products", [])
            )
            if unclassified_total > 0:
                total_per_grade["UNCLASSIFIED"] = unclassified_total

            # ================= STATIC PICKING ROWS =================
            static_rows = ["CAMP.", "BRKT TUNGGU JAM", "SHIFT BRIKEТ/РА",
                        "BKR(HR/JM)/KROAK", "PEMBAKAR/PENUTUP", "ASUMSI/BERAT PER IKAT"]
            row = header_row + 1
            for label in static_rows:
                sheet.write(row, 0, label, fmt_grade)
                col = 1
                for _ in oven_list:
                    sheet.merge_range(row, col, row, col + 1, "", fmt_number)
                    col += 2
                row += 1

            # ================= WRITE DATA (GRADE) =================
            grade_start_row = row

            for grade in sorted(data_map.keys(), key=_grade_sort_key):
                oven_data = data_map[grade]

                # skip UNCLASSIFIED jika semua produk LOKAL/FUEL
                if grade == "UNCLASSIFIED":
                    all_products = set()
                    for o in ovens:
                        if not o.get("classification"):
                            for p in o.get("products", []):
                                all_products.add(o.get("product_category"))
                    if all(x in ["LOKAL", "FUEL"] for x in all_products):
                        continue  # skip baris UNCLASSIFIED

                col = 0
                sheet.write(row, col, grade, fmt_grade)
                col += 1

                for oven in oven_list:
                    data = oven_data.get(oven)
                    if data:
                        sheet.write(row, col, data["qty"], fmt_number)
                        sheet.write(row, col + 1, ", ".join(sorted(data["products"])), fmt_text_center)
                    else:
                        sheet.write(row, col, "-", fmt_number)
                        sheet.write(row, col + 1, "-", fmt_text_center)
                    col += 2

                row += 1

            # ================= WRITE LOKAL/FUEL PER OVEN (TANPA HEADER) =================
            if aggregated_special:
                # Buat mapping: produk -> oven -> {qty, uom}
                product_per_oven = {}
                for o in ovens:
                    if o.get("product_category") in ["LOKAL", "FUEL"]:
                        oven_key = _get_oven_key(o.get("oven"), o.get("production_date")) or "NONE"
                        for p in o.get("products", []):
                            product_name = p["product"]
                            qty = p["qty"]
                            uom = o.get("uom_category")
                            product_per_oven.setdefault(product_name, {})
                            product_per_oven[product_name][oven_key] = {"qty": qty, "uom": uom}

                products = sorted(product_per_oven.keys())

                for product_name in products:
                    sheet.write(row, 0, product_name, fmt_grade)  # nama produk
                    col = 1
                    for oven in oven_list:
                        data = product_per_oven[product_name].get(oven)
                        if data:
                            sheet.write(row, col, data["qty"], fmt_number)
                            sheet.write(row, col + 1, data["uom"], fmt_text_center)
                        else:
                            sheet.write(row, col, "-", fmt_number)
                            sheet.write(row, col + 1, "-", fmt_text_center)
                        col += 2
                    row += 1
                    
            # ================= TOTAL ROW =================
            sheet.write(row, 0, "TOTAL QTY (KG)", fmt_header)
            col = 1
            for oven in oven_list:
                # ambil total dari total_per_oven
                total = total_per_oven.get(oven, 0)
                
                # tambahkan qty dari aggregated_special untuk oven ini
                if aggregated_special:
                    for p_name, p_data in aggregated_special.items():
                        # cek apakah oven punya produk ini
                        qty_per_oven = 0
                        for o in ovens:
                            if o.get("product_category") in ["LOKAL", "FUEL"]:
                                oven_key = _get_oven_key(o.get("oven"), o.get("production_date")) or "NONE"
                                if oven_key == oven:
                                    for prod in o.get("products", []):
                                        if prod["product"] == p_name:
                                            qty_per_oven += prod.get("qty", 0)
                        total += qty_per_oven

                sheet.merge_range(row, col, row, col + 1, total if total else "-", fmt_total)
                col += 2


            # ================= TOTAL PER GRADE DI KANAN =================
            grade_col_start = last_col + 1
            grade_row_header = grade_start_row - 1
            sheet.write(grade_row_header, grade_col_start, "PRODUK", fmt_header)
            sheet.write(grade_row_header, grade_col_start + 1, "QTY", fmt_header)
            sheet.write(grade_row_header, grade_col_start + 2, "TOTAL", fmt_header)
            sheet.write(grade_row_header, grade_col_start + 3, "GRADE", fmt_header)


            grade_row = grade_start_row
            for grade in sorted(data_map.keys(), key=_grade_sort_key):
                oven_data = data_map.get(grade, {})

                product_qty = {}
                for oven_data_item in oven_data.values():
                    for product in oven_data_item.get("products", []):
                        product_qty.setdefault(product, 0)

                # hitung qty per produk
                for oven_data_item in oven_data.values():
                    for p in oven_data_item.get("products", []):
                        pass  # sudah dihandle di bawah

                # cara AMAN: hitung ulang dari ovens
                for o in ovens:
                    if (o.get("classification") or "UNCLASSIFIED") == grade:
                        for p in o.get("products", []):
                            product_qty[p["product"]] = product_qty.get(p["product"], 0) + p.get("qty", 0)

                products = sorted(product_qty.keys())
                qtys = [str(int(product_qty[p])) for p in products]
                total_grade = int(sum(product_qty.values()))

                sheet.write(grade_row, grade_col_start, " | ".join(products), fmt_text_center)
                sheet.write(grade_row, grade_col_start + 1, " | ".join(qtys), fmt_text_center)
                sheet.write(grade_row, grade_col_start + 2, total_grade, fmt_grade_total)
                sheet.write(grade_row, grade_col_start + 3, grade, fmt_grade)

                grade_row += 1

            # ================= LOOP PRODUK LOKAL / FUEL =================
            if aggregated_special:
                _logger.info("aggregated_special: %s", aggregated_special)
                for p_name, p_data in sorted(aggregated_special.items()):
                    qty = p_data.get("qty", 0)
                    category = p_data.get("category", "-")  # bisa juga pakai p_data.get("category", "-") jika ada
                    uom = p_data.get("uom", "-")

                    sheet.write(grade_row, grade_col_start, p_name, fmt_text_center)
                    sheet.write(grade_row, grade_col_start + 1, qty, fmt_number)
                    sheet.write(grade_row, grade_col_start + 2, qty, fmt_grade_total)  # total sama dengan qty
                    sheet.write(grade_row, grade_col_start + 3, f"{uom} ({category})", fmt_grade)

                    grade_row += 1

            # ================= TOTAL SELURUH GRADE & RATA-RATA =================
            # total dari semua grade
            total_all_grades = sum(
                int(p.get("qty", 0))
                for grade in data_map.keys()
                for o in ovens
                if (o.get("classification") or "UNCLASSIFIED") == grade
                for p in o.get("products", [])
            )

            # tambahkan qty dari aggregated_special (LOKAL & FUEL)
            if aggregated_special:
                total_all_grades += sum(int(p_data.get("qty", 0)) for p_data in aggregated_special.values())

            sheet.write(grade_row, grade_col_start + 2, total_all_grades, fmt_total)
            sheet.write(grade_row, grade_col_start + 3, "TTL TONASE", fmt_header)

            # rata-rata per oven
            average_per_oven = round(total_all_grades / len(oven_list), 2) if oven_list else 0.00

            sheet.write(grade_row + 1, grade_col_start + 2, average_per_oven, fmt_total)
            sheet.write(grade_row + 1, grade_col_start + 3, "RATA-RATA", fmt_header)


            # ================= COLUMN WIDTH =================
            sheet.set_column(0, 0, 25)  # PICKING / GRADE

            col_idx = 1
            for _ in range(total_oven):
                sheet.set_column(col_idx, col_idx, 7)      # QTY oven
                sheet.set_column(col_idx + 1, col_idx + 1, 18)  # PRODUK oven
                col_idx += 2

            # ===== KOLOM KANAN (SUMMARY GRADE) =====
            sheet.set_column(grade_col_start, grade_col_start, 40)       # PRODUK (A | B | D)
            sheet.set_column(grade_col_start + 1, grade_col_start + 1, 25)  # QTY (2 | 4 | 6)
            sheet.set_column(grade_col_start + 2, grade_col_start + 2, 10)  # TOTAL
            sheet.set_column(grade_col_start + 3, grade_col_start + 3, 15)  # GRADE

        # =========================================================
        # CASE 1 : SINGLE WAREHOUSE
        # =========================================================
        if warehouse:
            wh_name = warehouse.name
            ovens = data_report.get(wh_name, {}).get("ovens", [])
            total_per_grade = data_report.get(wh_name, {}).get("total_per_grade")
            sheet = workbook.add_worksheet(wh_name[:31])
            _render_sheet(sheet, wh_name, ovens, total_per_grade=total_per_grade)

        # =========================================================
        # CASE 2 : ALL WAREHOUSE
        # =========================================================
        else:
            for wh_name, wh_data in data_report.items():
                ovens = wh_data.get("ovens", [])
                total_per_grade = wh_data.get("total_per_grade")
                sheet = workbook.add_worksheet(wh_name[:31])
                _render_sheet(sheet, wh_name, ovens, total_per_grade=total_per_grade)
