from odoo import models, fields, api, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    owner_id = fields.Many2one(comodel_name='res.partner', related='product_tmpl_id.owner_id', store=True, readonly=False)
    sales_person_ids = fields.Many2many(comodel_name='res.users', related='product_tmpl_id.sales_person_ids', store=False, help='Sales persons who are responsible for this product template.')