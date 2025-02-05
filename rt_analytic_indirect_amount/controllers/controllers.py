# -*- coding: utf-8 -*-
# from odoo import http


# class RtAnalyticIndirectAmount(http.Controller):
#     @http.route('/rt_analytic_indirect_amount/rt_analytic_indirect_amount', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_analytic_indirect_amount/rt_analytic_indirect_amount/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_analytic_indirect_amount.listing', {
#             'root': '/rt_analytic_indirect_amount/rt_analytic_indirect_amount',
#             'objects': http.request.env['rt_analytic_indirect_amount.rt_analytic_indirect_amount'].search([]),
#         })

#     @http.route('/rt_analytic_indirect_amount/rt_analytic_indirect_amount/objects/<model("rt_analytic_indirect_amount.rt_analytic_indirect_amount"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_analytic_indirect_amount.object', {
#             'object': obj
#         })

