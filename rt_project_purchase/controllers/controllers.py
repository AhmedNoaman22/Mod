# -*- coding: utf-8 -*-
# from odoo import http


# class RtProjectPurchase(http.Controller):
#     @http.route('/rt_project_purchase/rt_project_purchase', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_project_purchase/rt_project_purchase/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_project_purchase.listing', {
#             'root': '/rt_project_purchase/rt_project_purchase',
#             'objects': http.request.env['rt_project_purchase.rt_project_purchase'].search([]),
#         })

#     @http.route('/rt_project_purchase/rt_project_purchase/objects/<model("rt_project_purchase.rt_project_purchase"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_project_purchase.object', {
#             'object': obj
#         })

