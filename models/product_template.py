from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    owner_id = fields.Many2one(comodel_name='res.partner', help="Pemilik default untuk produk ini.")
    