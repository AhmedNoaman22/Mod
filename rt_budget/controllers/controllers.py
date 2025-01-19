# -*- coding: utf-8 -*-
# from odoo import http


# class RtBudget(http.Controller):
#     @http.route('/rt_budget/rt_budget', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_budget/rt_budget/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_budget.listing', {
#             'root': '/rt_budget/rt_budget',
#             'objects': http.request.env['rt_budget.rt_budget'].search([]),
#         })

#     @http.route('/rt_budget/rt_budget/objects/<model("rt_budget.rt_budget"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_budget.object', {
#             'object': obj
#         })

