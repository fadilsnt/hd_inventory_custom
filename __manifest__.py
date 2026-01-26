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
    'depends': ['base', 'web', 'product', 'stock', 'fjr_custom_stock', 'export_stock_report', 'report_xlsx', 'uom', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/wizard_inventory_laporan_hari_pengganti_view.xml',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_line_inherit_view.xml',
        'views/uom_uom_views.xml',
        'views/purchase_views.xml',
        'views/product_attribute_views.xml',
        'reports/paperformat.xml',
        'reports/report_action.xml',
        'reports/bukti_terima_barang_pdf_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hd_inventory_custom/static/src/js/purchase_order_list.js',
            'hd_inventory_custom/static/src/js/purchase_date_search.js',
            'hd_inventory_custom/static/src/js/purchase_dashboard.js',
            'hd_inventory_custom/static/src/xml/purchase_dashboard.xml',
        ],
    },    
    'phone': "085156534679",
}
