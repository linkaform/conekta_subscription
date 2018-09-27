# -*- coding: utf-8 -*-
from odoo import http

# class ConektaSubscriptions(http.Controller):
#     @http.route('/conekta_subscriptions/conekta_subscriptions/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/conekta_subscriptions/conekta_subscriptions/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('conekta_subscriptions.listing', {
#             'root': '/conekta_subscriptions/conekta_subscriptions',
#             'objects': http.request.env['conekta_subscriptions.conekta_subscriptions'].search([]),
#         })

#     @http.route('/conekta_subscriptions/conekta_subscriptions/objects/<model("conekta_subscriptions.conekta_subscriptions"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('conekta_subscriptions.object', {
#             'object': obj
#         })