{
    'name': 'Custom Service Order',
    'version': '1.0',
    'summary': 'Manage and track service sales orders.',
    'description': 'Allows sales team to manage and organize service sales orders efficiently.',
    'category': 'Sales',
    'author': 'Md Imtiaj Hossain',
    'depends': ['base', 'sale_management', 'mail', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/sale_service_order_views.xml',
        'views/menu.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
