{
    'name': 'Smart POS & Loyalty Point',
    'version': '19.0.1.0.0',
    'author': 'Dafa Adi Raharjo',
    'summary': 'Tambah fitur Loyalty Point pada Point of Sale',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/loyalty_history_views.xml',
        'views/loyalty_reward_product_views.xml',
        'views/loyalty_redeem_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
}
