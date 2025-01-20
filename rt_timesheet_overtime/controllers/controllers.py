# -*- coding: utf-8 -*-
# from odoo import http


# class RtTimesheetOvertime(http.Controller):
#     @http.route('/rt_timesheet_overtime/rt_timesheet_overtime', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_timesheet_overtime/rt_timesheet_overtime/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_timesheet_overtime.listing', {
#             'root': '/rt_timesheet_overtime/rt_timesheet_overtime',
#             'objects': http.request.env['rt_timesheet_overtime.rt_timesheet_overtime'].search([]),
#         })

#     @http.route('/rt_timesheet_overtime/rt_timesheet_overtime/objects/<model("rt_timesheet_overtime.rt_timesheet_overtime"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_timesheet_overtime.object', {
#             'object': obj
#         })

