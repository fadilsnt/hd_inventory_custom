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