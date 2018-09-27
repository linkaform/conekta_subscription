# -*- coding: utf-8 -*-
{
    'name': "conekta_subscriptions",

    'description': """
        Conectar subscriptions con conekta para cuando se valide una factura de una subscription que tenga conekta como provider pueda hacer el cargo automaticamente
    """,

    'author': "Erick Hillo",
    'website': "http://www.linkaform.com",
    'category': 'Payment',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','payment','sale_subscription'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
}