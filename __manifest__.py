# -*- coding: utf-8 -*-
{
    'name': "Heptacloud Dvintara Inventory Custom",
    'summary': "Custom inventory features and enhancements for Heptacloud Dvintara.",
    'description': """
        This module provides additional customizations and enhancements
        for the inventory management workflow in Heptacloud Dvintara.
    """,
    'author': "Michael Hubert",
    'website': "https://www.linkedin.com/in/michael-hubert/",
    'maintainer': "Michael Hubert",
    'support': "echovoid14@gmail.com",
    'category': 'Inventory',
    'version': '0.1',
    'depends': ['base', 'product', 'stock', 'fjr_custom_stock', 'export_stock_report'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
    ],
    'phone': "085156534679",
}
