from odoo import models, fields, api, _ 

class WizardInventoryDetailProduct(models.TransientModel):
    _name = 'wizard.inventory.detail.product'
    _description = "Wizard Inventory Detail Product"

    # product_id = fields.Many2one('product.product', 'Product', domain="[('type', '=', 'consu')]", index=True, readonly=True
