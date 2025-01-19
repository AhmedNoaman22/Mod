# -*- coding: utf-8 -*-
# from odoo import http


# class RtCustomTimesheet(http.Controller):
#     @http.route('/rt_custom_timesheet/rt_custom_timesheet', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_custom_timesheet/rt_custom_timesheet/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_custom_timesheet.listing', {
#             'root': '/rt_custom_timesheet/rt_custom_timesheet',
#             'objects': http.request.env['rt_custom_timesheet.rt_custom_timesheet'].search([]),
#         })

#     @http.route('/rt_custom_timesheet/rt_custom_timesheet/objects/<model("rt_custom_timesheet.rt_custom_timesheet"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_custom_timesheet.object', {
#             'object': obj
#         })

