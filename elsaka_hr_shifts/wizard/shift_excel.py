# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import base64,os
import time,calendar
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging
import xlsxwriter
import math, pytz
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class shift_report(models.TransientModel):
    _name = "shift.report"
    _description = "Employee Shifts Wizard For Excel Report"

    @api.model
    def _get_month_start(self):
        year = time.strftime("%Y")
        month = time.strftime("%m")
        return year + '-' + month + '-' + '01'

    @api.model
    def _get_month_end(self):
        year = time.strftime("%Y")
        month = time.strftime("%m")
        last_day = calendar.monthrange(int(year),int(month))[1]
        return year + '-' + month + '-' + str(last_day)

    mode = fields.Selection([('all_employees', 'All Departments'),
                              ('department', 'Department(s)')],
                             string="Mode", required=True, default="all_employees")
    department_ids = fields.Many2many('hr.department', 
                                       'shiftreport_department_rel',
                                       'shiftreport_id',
                                       'department_id', 
                                       'Department(s)')
    shift_mode = fields.Selection([('all_shifts','All Shifts'),('shift','Several Shift(s)')], 
                                   string="Shift Option", required=True, default="all_shifts")
    shift_ids = fields.Many2many('hr.shifts', 
                                   'shiftreport_shift_rel',
                                   'shiftreport_id',
                                   'shift_id', 
                                   'Shift(s)')
    date_from = fields.Date("Date From", default=_get_month_start)
    date_to = fields.Date("Date To", default=_get_month_end)
    excelfile = fields.Binary('Excel File')
    file_name = fields.Char('Excel File')

    def convert_datetime_to_tz(self, date):
        tz = "tz" in self.env.context and self.env.context.get('tz') or 'UTC' if self.env.context else "UTC"
        local_timezone = pytz.timezone(tz)
        utc_time = date
        converted_date = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone).strftime("%Y-%m-%d %H:%M:%S")
        return converted_date

    def first_and_last_action(self, attendance_pool, employee_id, key):
        first_signin = "00:00:00"
        last_signout = "00:00:00"
        last_att_ids = attendance_pool.search([
            ('employee_id','=', employee_id),
            ('check_in','>=',key + ' 00:00:01'),
            ('check_out','<=',key + ' 23:59:59')], order="check_in DESC")
        first_att_ids = attendance_pool.search([
            ('employee_id','=', employee_id),
            ('check_in','>=',key + ' 00:00:01'),
            ('check_out','<=',key + ' 23:59:59')], order="check_in ASC")
        if first_att_ids:
            sign_date = first_att_ids[0].check_in
            sign_date = self.convert_datetime_to_tz(sign_date)
            first_signin = sign_date.split(' ')[1]
        if last_att_ids:
            temp_date = last_att_ids[0].check_out
            temp_date = self.convert_datetime_to_tz(temp_date)
            last_signout = temp_date.split(' ')[1]
        return last_signout, first_signin

    def get_data(self):
        lines = []
        DATE_FORMAT = "%Y-%m-%d"

        emp_pool = self.env['hr.employee']
        assing_shift_line_pool = self.env['assign.shift.line']
        shift_pool = self.env['hr.shifts']
        attendance_pool = self.env['hr.attendance']

        date_from = self.date_from
        date_to = self.date_to

        domain_employee = [('active','=',True)]
        employee_ids = emp_pool.search(domain_employee)
        if self.mode == 'department':
            if self.department_ids:
                employee_ids = emp_pool.search(domain_employee + 
                       [('department_id','in',[x.id for x in self.department_ids])])

        if not employee_ids: return []
        employee_ids = [x.id for x in employee_ids]

        shift_ids = [x.id for x in shift_pool.search([])]
        if self.shift_mode == 'shift':
            if self.shift_ids:
                shift_ids = [x.id for x in self.shift_ids]

        temp_date1 = self.date_from.strftime('%Y-%m-%d') + ' 00:00:00'
        temp_date2 = self.date_to.strftime('%Y-%m-%d') + ' 23:59:59'
        self.env.cr.execute("""
SELECT a.check_in as check_in, a.check_out as check_out, a.employee_id, emp.department_id AS department_id FROM hr_attendance AS a
LEFT JOIN hr_employee AS emp ON emp.id=a.employee_id
LEFT JOIN hr_department AS d on d.id=emp.department_id
WHERE (a.check_in BETWEEN %s and %s OR a.check_out BETWEEN %s and %s) and a.employee_id in %s
GROUP BY a.check_in, a.check_out, a.employee_id, emp.department_id
ORDER BY a.employee_id ASC, a.check_in ASC, a.check_out ASC;
        """, (temp_date1, temp_date2, temp_date1, temp_date2, tuple(employee_ids) ))
        attendance_ids = self.env.cr.dictfetchall()

        #AVOID DUPLICATING ON SAME DAY: reducing system load
        temp = {}
        for element in attendance_ids:
            check_in = element['check_in'].strftime('%Y-%m-%d %H:%M:%S')
            if element['employee_id'] not in temp.keys():
                temp[element['employee_id']] = [check_in.split(' ')[0]]
            else:
                if check_in.split(' ')[0] not in temp[element['employee_id']]:
                    temp[element['employee_id']].append(check_in.split(' ')[0])

        att_data = []
        emp_not_found = []
        for attendance in attendance_ids:
            check_in = attendance['check_in'].strftime('%Y-%m-%d %H:%M:%S')
            if check_in.split(' ')[0] not in temp[attendance['employee_id']]:
                continue
            temp[attendance['employee_id']].remove(check_in.split(' ')[0])

            assign_shift_line_ids = attendance_pool.get_employee_shift( 
                   attendance['employee_id'], check_in, check_in)

            if not assign_shift_line_ids:
                employee = self.env['hr.employee'].browse(attendance['employee_id'])
                emp_not_found.append(employee.name)
                continue

            assing_shift_line = assign_shift_line_ids[0]
            if assing_shift_line.shift_id.id not in shift_ids:
                continue

            employee = self.env['hr.employee'].browse(attendance['employee_id'])
            attendance['employee_id'] = employee.name
            attendance['department_id'] = employee.department_id and employee.department_id.name or '-'
            attendance['shift'] = assing_shift_line.shift_id.name
            attendance['shift_id'] = assing_shift_line.shift_id.id
            attendance['shift_hours'] = assing_shift_line.shift_id.total_working_hours
            attendance['shift_from_hours'] = assing_shift_line.shift_id.from_hours
            attendance['shift_to_hours'] = assing_shift_line.shift_id.to_hours

            signout, signin = self.first_and_last_action(attendance_pool, 
                    attendance['employee_id'], check_in.split(' ')[0])

            attendance['signin'] = signin
            attendance['signout'] = signout

            att_data.append(attendance)

        shift_data = {}
        for element in att_data:
            if element['shift'] not in shift_data.keys():
                shift_data[element['shift']] = [element]
            else:
                shift_data[element['shift']].append(element)

#         lines = sorted(lines, key=lambda k: k['date'])
        return shift_data,list(set(emp_not_found))

    def do_generate_excel(self):
        today = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT).replace(':','').replace(' ','_').replace('-','')
        filename = 'Shifts_Wise_Employee_Report_%s.xlsx' % (today)
        title = 'Shifts Wise Employee Report'
        if self.date_from and self.date_to:
            title += ' (%s-%s)'%(self.date_from,self.date_to)

        workbook = xlsxwriter.Workbook('/tmp/%s'%(filename))
        worksheet = workbook.add_worksheet()

        #FORMATING PROPERTIES
        title_format = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#99ff66',##A9A9A9
        'underline': 2,
        'border': 1,
        'size': 14})
        total_format = workbook.add_format({'bold': 1, 'bg_color': '#ccccff', 'top': 1,
                                            'underline': 2, 'size': 10})
        total_format.set_num_format('0.00')

        td_center = workbook.add_format({'size': 10,'align': 'center','valign': 'vcenter',})
        td_left = workbook.add_format({'size': 10,'align': 'left','valign': 'vcenter',})

        float_format = workbook.add_format({'size': 10})
        float_format.set_num_format('0.00')

        FOOTER = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#ccccff',
            'underline': 2,
            'top': 1,
            'size': 10})

        blueHEADING = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#ccccff',
            #'underline': 2,
            'border': 1,
            'size': 10})

        data,emp_not_found = self.get_data()
        if not data.keys():
            #ADJUST WIDTH OF COLUMNS
            worksheet.set_column('A:A', 100)
            worksheet.write(1, 0, "Shift Not Found for Some Employees:- " + ', '.join(emp_not_found), title_format)
            workbook.close()
            return True

        #ADJUST WIDTH OF COLUMNS
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)

        worksheet.set_row(0, 30)

        #REPORT HEADING
        worksheet.merge_range('A1:E1', title, title_format)

        #HEADINGS
        headings = ['Date', 'Employee', 'Department', 'Sign-IN', 'Sign-Out']

        row = 3
        col = 0
        for shift,shift_data in data.items():
            worksheet.write(row, col, shift, blueHEADING)
            if shift_data:
                shift_timing = 'From ' + str(shift_data[0]['shift_from_hours']) + ' To ' + \
                                            str(shift_data[0]['shift_to_hours'])
                worksheet.write(row, col+1, shift_timing, blueHEADING)
                worksheet.write(row, col+2, str(shift_data[0]['shift_hours']) + ' Hours', blueHEADING)

            row += 1
            col = 0
            for h in headings:
                worksheet.write(row, col, h, blueHEADING)
                col += 1

            row += 1
            col = 0
            for v in shift_data:
                checkin = v['check_in'].strftime('%Y-%m-%d %H:%M:%S')
                worksheet.write(row, col, checkin.split(' ')[0], td_center)
                worksheet.write(row, col+1, v['employee_id'], td_left)
                worksheet.write(row, col+2, v['department_id'], td_left)
                worksheet.write(row, col+3, v['signin'], td_center)
                worksheet.write(row, col+4, v['signout'], td_center)
                row += 1
                col = 0

            row += 2

        row += 3
        if emp_not_found:
            worksheet.write(row, 0, "Shift Not Found for Some Employees:- " + ', '.join(emp_not_found), td_left)
        workbook.close()

        #FILE UPLOAD
        tf = open('/tmp/%s'%(filename), 'rb')
        buf = tf.read()
        out=base64.encodestring(buf)
        self[0].write({'excelfile': out, 'file_name': filename})
        tf.close()
        os.remove('/tmp/%s'%(filename))
        return { 'type': 'ir.actions.act_window', 
                'res_model': 'shift.report', 'view_mode': 'form', 
                'view_type': 'form', 'res_id': self[0].id, 'target': 'new'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
