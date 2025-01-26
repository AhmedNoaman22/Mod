# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, SUPERUSER_ID, _
from odoo.exceptions import UserError
import datetime
from datetime import timedelta
import pytz
import time
from . import const
from .base import ZK

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging

from itertools import groupby
from operator import itemgetter

_logger = logging.getLogger(__name__)


class zkMachineLocation(models.Model):
    _name = 'zk.machine.location'
    name = fields.Char("Location", required=True)


class zkMachine(models.Model):
    _name = 'zk.machine'

    name = fields.Char("Machine IP")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], 'State', default='draft')
    location_id = fields.Many2one('zk.machine.location', string="Location")
    port = fields.Integer("Port Number")
    employee_ids = fields.Many2many("hr.employee", 'zk_machine_employee_rel', 'employee_id', 'machine_id',
                                    string='Employees', readonly=True, copy=False, required=False)
    date_to = fields.Datetime('Date To', copy=False, required=False)
    date_from = fields.Datetime('Date From', copy=False, required=False)
    time_type = fields.Selection([('s', 'Seconds'), ('m', 'Minutes')], default='')
    time_difference = fields.Integer(string="Time Difference")
    user_name = fields.Char(string='User Name')
    password = fields.Integer(string='Password')

    def try_connection(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            password = 0
            if r.password:
                password = r.password
            zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                users = conn.get_users()
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.disconnect()
                    raise UserError(_('Successful connection:  "%s".') %
                                    (users))

    def restart(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            password = 0
            if r.password:
                password = r.password
            zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.restart()
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                raise UserError('Successful')

    def synchronize(self):
        for r in self:
            employee = self.env['hr.employee']
            employee_location_line = self.env['zk.employee.location.line']
            employee_list = []
            machine_ip = r.name
            port = r.port
            password = 0
            if r.password:
                password = r.password
            zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                users = conn.get_users()
                for user in users:
                    employee_id = employee.search([('zknumber', '=', user.user_id)])
                    if len(employee_id) > 1:
                        raise UserError('There is more than one employee with the same son-in-law zk')
                    if employee_id:
                        employee_list.append(employee_id)
                        if employee_id not in r.employee_ids:
                            r.employee_ids += employee_id
                            employee_location_line.create({'employee_id': employee_id.id,
                                                           'zk_num': employee_id.zknumber,
                                                           'machine_id': r.id,
                                                           'uid': user.uid,
                                                           'location_id': r.location_id.id})
                for emp in employee_list:
                    employee += emp
                employees_unlink = r.employee_ids - employee
                for emp1 in employees_unlink:
                    employee_location_line_id = employee_location_line.search(
                        [('employee_id', '=', emp1.id), ('machine_id', '=', r.id)])
                    employee_location_line_id.unlink()
                r.employee_ids = employee
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.disconnect()

    def clear_attendance(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            password = 0
            if r.password:
                password = r.password
            zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                conn.clear_attendance()
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.enable_device()
                    conn.disconnect()

    def get_time_difference(self, start, end, current):
        if start and current and end:
            if start <= current <= end:
                return True
        else:
            return False

    def download_attendance2(self):
        users = self.env['res.users']
        attendance_obj = self.env["hr.attendance"]
        employee_location_line_obj = self.env["zk.employee.location.line"]
        user = self.env.user
        if not user.partner_id.tz:
            raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
        tz = pytz.timezone(user.partner_id.tz) or False
        for machine in self:
            machine_ip = machine.name
            port = machine.port
            password = 0
            if machine.password:
                password = machine.password
            zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                attendances = conn.get_attendance()
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.disconnect()
                    attendance = []
                    for rec in attendances:
                        date = rec.timestamp
                        date1 = datetime.datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
                        if self.date_from and self.date_to:
                            if date1 > self.date_from and date1 < self.date_to:
                                attendance.append(rec)
                            else:
                                print('no ===============')
                        elif self.date_from:
                            if date1 > self.date_from:
                                attendance.append(rec)

                    if not self.date_from:
                        raise UserError(_('Successful connection:  "%s".') % (attendances))
                    else:
                        raise UserError(_('Successful connection:  "%s".') % (attendance))

    # def download_attendance2(self):
    #     users = self.env['res.users']
    #     attendance_obj = self.env["hr.attendance"]
    #     employee_location_line_obj = self.env["zk.employee.location.line"]
    #     user = self.env.user
    #     if not user.partner_id.tz:
    #         raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
    #     tz = pytz.timezone(user.partner_id.tz) or False
    #
    #     for machine in self:
    #         machine_ip = machine.name
    #         port = machine.port
    #         password = 0
    #         if machine.password:
    #             password = machine.password
    #         zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
    #         conn = ''
    #         try:
    #             conn = zk.connect()
    #             conn.disable_device()
    #             attendances = conn.get_attendance()
    #
    #             date_convert_to = tz.normalize(tz.localize(self.date_to)).astimezone(pytz.utc).strftime(
    #                 "%Y-%m-%d %H:%M:%S")
    #             date_convert_from = tz.normalize(tz.localize(self.date_from)).astimezone(pytz.utc).strftime(
    #                 "%Y-%m-%d %H:%M:%S")
    #
    #             def attendance_data(attendance):
    #                 if date_convert_from and date_convert_to:
    #                     if datetime.datetime.strftime(attendance.timestamp,
    #                                                   '%Y-%m-%d %H:%M:%S') >= date_convert_from \
    #                             and datetime.datetime.strftime(attendance.timestamp,
    #                                                            '%Y-%m-%d %H:%M:%S') <= date_convert_to:
    #                         return True
    #                     else:
    #                         return False
    #                 elif date_convert_from and not date_convert_to:
    #                     if datetime.datetime.strftime(attendance.timestamp,
    #                                                   '%Y-%m-%d %H:%M:%S') >= date_convert_from:
    #                         return True
    #                     else:
    #                         return False
    #                 else:
    #                     return False
    #
    #             new_attendance = filter(attendance_data, attendances)
    #             new_list = list(new_attendance)
    #             new_dict = []
    #             for rec in new_list:
    #                 val = {
    #                     'id': rec.user_id,
    #                     'attend': rec
    #                 }
    #                 new_dict.append(val)
    #             sort_new_dict = sorted(new_dict, key=itemgetter('id'))
    #             final_list = []
    #             for key, value in groupby(sort_new_dict, key=itemgetter('id')):
    #                 print(key)
    #                 count = 0.0
    #                 type = ''
    #                 start_time = ''
    #                 for k in value:
    #                     attend = k['attend']
    #                     if count == 0.0:
    #                         final_list.append(k['attend'])
    #                         type = attend.punch
    #                         start_time = attend.timestamp
    #                         count = 1.0
    #                     else:
    #                         new_attend = k['attend']
    #                         if new_attend.punch != type:
    #                             final_list.append(k['attend'])
    #                             type = new_attend.punch
    #                             start_time = new_attend.timestamp
    #                         else:
    #                             end_time = new_attend.timestamp
    #                             diff = end_time - start_time
    #                             seconds = diff.total_seconds()
    #                             minutes = seconds / 60
    #                             if self.time_type:
    #                                 if self.time_difference and self.time_type == 's':
    #                                     if seconds > self.time_difference:
    #                                         final_list.append(k['attend'])
    #                                         type = new_attend.punch
    #                                         start_time = new_attend.timestamp
    #                                 if self.time_difference and self.time_type == 'm':
    #                                     if seconds > self.time_difference:
    #                                         if minutes > self.time_difference:
    #                                             final_list.append(k['attend'])
    #                                             type = new_attend.punch
    #                                             start_time = new_attend.timestamp
    #                             else:
    #                                 final_list.append(k['attend'])
    #                                 type = new_attend.punch
    #                                 start_time = new_attend.timestamp
    #             _logger.info(f'final_list is ==========={final_list}')
    #             _logger.info(f'len(final_list) ==========={len(final_list)}')
    #
    #             for attendance in final_list:
    #                 _logger.info(f'attendance ==========={attendance}')
    #                 employee_location_line = employee_location_line_obj.search(
    #                     [("zk_num", "=", int(attendance.user_id)), ('location_id', '=', machine.location_id.id),
    #                      ('machine_id', '=', machine.id)])
    #                 if employee_location_line:
    #                     employee_id = employee_location_line.employee_id
    #                     date = attendance.timestamp
    #                     date1 = datetime.datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    #                     date = tz.normalize(tz.localize(date1)).astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    #                     if attendance.punch == 0:
    #                         attendance_id = attendance_obj.search(
    #                             [('employee_id', '=', employee_id.id), ('check_in', '!=', False),
    #                              ('check_in', '=', str(date))])
    #                         if not attendance_id:
    #                             attendance_obj.create({'check_in': date, 'employee_id': employee_id.id})
    #                     if attendance.punch == 1:
    #
    #                         attendance_id = attendance_obj.search(
    #                             [('employee_id', '=', employee_id.id), ('check_out', '=', str(date))])
    #                         if not attendance_id:
    #                             attendance_ids = attendance_obj.search(
    #                                 [('employee_id', '=', employee_id.id), ('check_in', '!=', False),
    #                                  ('check_in', '<', str(date)),
    #                                  ('check_out', '=', False)], order='check_in desc', limit=1)
    #                             attendance_last = attendance_obj.search(
    #                                 [('employee_id', '=', employee_id.id), ('check_in', '!=', False)],
    #                                 order='check_in desc', limit=1)
    #                             if (
    #                                     attendance_last.check_in and attendance_ids.check_in and attendance_ids.check_in >= attendance_last.check_in) or not attendance_last.check_in or not attendance_ids.check_in:
    #                                 if attendance_ids:
    #                                     attendance_ids.write({'check_out': date})
    #                                 else:
    #                                     if attendance_last.check_in == False:
    #                                         attendance_obj.create(
    #                                             {
    #                                                 'check_in': date,
    #                                                 'check_out': date,
    #                                                 'employee_id': employee_id.id,
    #                                             }
    #                                         )
    #
    #                             else:
    #                                 if attendance_last.check_in == False:
    #                                     attendance_obj.create
    #                                     (
    #                                         {
    #                                             'check_out': date,
    #                                             'employee_id': employee_id.id
    #                                         }
    #                                     )
    #
    #
    #
    #
    #         except Exception as e:
    #             raise UserError('The connection has not been achieved: %s' % (e))
    #         finally:
    #             if conn:
    #                 conn.enable_device()
    #                 conn.disconnect()
    #
    # def get_attendance_auto2(self):
    #     users = self.env['res.users']
    #     attendance_obj = self.env["hr.attendance"]
    #     employee_location_line_obj = self.env["zk.employee.location.line"]
    #     user = self.env.user
    #     print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    #     if not user.partner_id.tz:
    #         raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
    #     tz = pytz.timezone(user.partner_id.tz) or False
    #     machines = self.search([])
    #     for machine in machines:
    #         machine_ip = machine.name
    #         port = machine.port
    #         password = 0
    #         if machine.password:
    #             password = machine.password
    #         zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
    #         conn = ''
    #         print('in for ============')
    #         try:
    #             conn = zk.connect()
    #             conn.disable_device()
    #             attendances = conn.get_attendance()
    #             # print(f'attendances ========== {attendances}')
    #
    #             date_convert_to = datetime.datetime.now()
    #             dt_format = '%Y-%m-%d %H:%M:%S'
    #             date_from = datetime.datetime.now() - timedelta(days=1)
    #             new_date = datetime.datetime.strftime(date_from, dt_format)
    #             new_date = datetime.datetime.strptime(str(new_date), dt_format)
    #             date_convert_from = new_date.replace(hour=2, minute=2, second=1)
    #
    #             date_convert_to = tz.normalize(tz.localize(date_convert_to)).astimezone(pytz.utc).strftime(
    #                 "%Y-%m-%d %H:%M:%S")
    #             date_convert_from = tz.normalize(tz.localize(date_convert_from)).astimezone(pytz.utc).strftime(
    #                 "%Y-%m-%d %H:%M:%S")
    #
    #             print(f'date_convert_from ============ {date_convert_from}')
    #             print(f'date_convert_to ============ {date_convert_to}')
    #             try:
    #                 def attendance_data(attendance):
    #                     if date_convert_from and date_convert_to:
    #                         if datetime.datetime.strftime(attendance.timestamp,
    #                                                       '%Y-%m-%d %H:%M:%S') >= date_convert_from \
    #                                 and datetime.datetime.strftime(attendance.timestamp,
    #                                                                '%Y-%m-%d %H:%M:%S') <= date_convert_to:
    #                             return True
    #                         else:
    #                             return False
    #                     elif date_convert_from and not date_convert_to:
    #                         if datetime.datetime.strftime(attendance.timestamp,
    #                                                       '%Y-%m-%d %H:%M:%S') >= date_convert_from:
    #                             return True
    #                         else:
    #                             return False
    #                     else:
    #                         return False
    #
    #                 new_attendance = filter(attendance_data, attendances)
    #                 new_list = list(new_attendance)
    #                 print(f'new_list =========== {new_list}')
    #                 new_dict = []
    #                 for rec in new_list:
    #                     val = {
    #                         'id': rec.user_id,
    #                         'attend': rec
    #                     }
    #                     new_dict.append(val)
    #                 sort_new_dict = sorted(new_dict, key=itemgetter('id'))
    #                 final_list = []
    #                 gb = groupby(sort_new_dict, key=itemgetter('id'))
    #                 print(f'gp ============ {gb}')
    #                 for key, value in groupby(sort_new_dict, key=itemgetter('id')):
    #                     print(f'key ========= {key}')
    #                     print(f'value ========= {value}')
    #                     count = 0.0
    #                     type = ''
    #                     start_time = ''
    #                     for k in value:
    #                         attend = k['attend']
    #                         if count == 0.0:
    #                             final_list.append(k['attend'])
    #                             type = attend.punch
    #                             start_time = attend.timestamp
    #                             count = 1.0
    #                         else:
    #                             new_attend = k['attend']
    #                             if new_attend.punch != type:
    #                                 final_list.append(k['attend'])
    #                                 type = new_attend.punch
    #                                 start_time = new_attend.timestamp
    #                             else:
    #                                 end_time = new_attend.timestamp
    #                                 diff = end_time - start_time
    #                                 seconds = diff.total_seconds()
    #                                 minutes = seconds / 60
    #                                 if self.time_type:
    #                                     if self.time_difference and self.time_type == 's':
    #                                         if seconds > self.time_difference:
    #                                             final_list.append(k['attend'])
    #                                             type = new_attend.punch
    #                                             start_time = new_attend.timestamp
    #                                     if self.time_difference and self.time_type == 'm':
    #                                         if seconds > self.time_difference:
    #                                             if minutes > self.time_difference:
    #                                                 final_list.append(k['attend'])
    #                                                 type = new_attend.punch
    #                                                 start_time = new_attend.timestamp
    #                                 else:
    #                                     final_list.append(k['attend'])
    #                                     type = new_attend.punch
    #                                     start_time = new_attend.timestamp
    #                 print('final_list is ===========', final_list)
    #                 print('========= TEST ==============')
    #                 for attendance in final_list:
    #                     try:
    #                         employee_location_line = employee_location_line_obj.search(
    #                             [("zk_num", "=", int(attendance.user_id)), ('location_id', '=', machine.location_id.id),
    #                              ('machine_id', '=', machine.id)])
    #                         if employee_location_line:
    #                             employee_id = employee_location_line.employee_id
    #                             date = attendance.timestamp
    #                             date1 = datetime.datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    #                             date = tz.normalize(tz.localize(date1)).astimezone(pytz.utc).strftime(
    #                                 "%Y-%m-%d %H:%M:%S")
    #                             # if attendance.punch == 0:
    #                             #     attendance_id = attendance_obj.search(
    #                             #         [('employee_id', '=', employee_id.id), ('check_in', '=', str(date))])
    #                             #     if not attendance_id:
    #                             #         attendance_obj.create({'check_in': date, 'employee_id': employee_id.id})
    #                             if attendance.punch == 1:
    #                                 attendance_id = attendance_obj.search(
    #                                     [('employee_id', '=', employee_id.id), ('check_out', '=', str(date))])
    #                                 if not attendance_id:
    #                                     attendance_ids = attendance_obj.search(
    #                                         [('employee_id', '=', employee_id.id), ('check_in', '<', str(date)),
    #                                          ('check_out', '=', False)], order='check_in desc', limit=1)
    #                                     attendance_last = attendance_obj.search(
    #                                         [('employee_id', '=', employee_id.id), ('check_in', '!=', False)],
    #                                         order='check_in desc', limit=1)
    #                                     if (
    #                                             attendance_last.check_in and attendance_ids.check_in and attendance_ids.check_in >= attendance_last.check_in) or not attendance_last.check_in or not attendance_ids.check_in:
    #                                         if attendance_ids:
    #                                             attendance_ids.write({'check_out': date})
    #                                         else:
    #                                             attendance_obj.create(
    #                                                 {'check_out': date, 'employee_id': employee_id.id})
    #                                     else:
    #                                         attendance_obj.create({'check_out': date, 'employee_id': employee_id.id})
    #                     except Exception as e:
    #                         self.continue_create_attendance()
    #             except Exception as e:
    #                 self.continue_create_attendance()
    #
    #
    #
    #         except Exception as e:
    #             raise UserError('The connection has not been achieved: %s' % (e))
    #         finally:
    #             if conn:
    #                 conn.enable_device()
    #                 conn.disconnect()

    def download_attendance(self):
        self.download_attendance_data(self.date_from, self.date_to)

    def get_attendance_auto(self):
        user = self.env.user
        if not user.partner_id.tz:
            raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
        tz = pytz.timezone(user.partner_id.tz) or False
        machines = self.search([])
        date_to = datetime.datetime.now() + timedelta(hours=3)
        dt_format = '%Y-%m-%d %H:%M:%S'
        date_from = datetime.datetime.now() - timedelta(days=2) + timedelta(hours=3)
        new_date = datetime.datetime.strftime(date_from, dt_format)
        new_date = datetime.datetime.strptime(str(new_date), dt_format)
        print('========= date_from ======', date_from)
        print('========= date_to ======', date_to)
        _logger.info(f'date_from ==========={date_from}')
        _logger.info(f'date_to ==========={date_to}')

        for machine in machines:
            machine.download_attendance_data(date_from, date_to)
        return True

    def download_attendance_data(self, date_from, date_to):
        print('========= last update =========')
        users = self.env['res.users']
        attendance_obj = self.env["hr.attendance"]
        employee_location_line_obj = self.env["zk.employee.location.line"]
        user = self.env.user
        if not user.partner_id.tz:
            raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
        tz = pytz.timezone(user.partner_id.tz) or False

        for machine in self:
            machine_ip = machine.name
            port = machine.port
            password = 0
            if machine.password:
                password = machine.password
            zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                attendances = conn.get_attendance()

                date_convert_to = tz.normalize(tz.localize(date_to)).astimezone(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S")
                date_convert_from = tz.normalize(tz.localize(date_from)).astimezone(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S")

                def attendance_data(attendance):
                    if date_convert_from and date_convert_to:
                        if datetime.datetime.strftime(attendance.timestamp,
                                                      '%Y-%m-%d %H:%M:%S') >= date_convert_from \
                                and datetime.datetime.strftime(attendance.timestamp,
                                                               '%Y-%m-%d %H:%M:%S') <= date_convert_to:
                            return True
                        else:
                            return False
                    elif date_convert_from and not date_convert_to:
                        if datetime.datetime.strftime(attendance.timestamp,
                                                      '%Y-%m-%d %H:%M:%S') >= date_convert_from:
                            return True
                        else:
                            return False
                    else:
                        return False

                new_attendance = filter(attendance_data, attendances)
                new_list = list(new_attendance)
                new_dict = []
                for rec in new_list:
                    val = {
                        'id': rec.user_id,
                        'attend': rec
                    }
                    new_dict.append(val)
                sort_new_dict = sorted(new_dict, key=itemgetter('id'))
                final_list = []
                for key, value in groupby(sort_new_dict, key=itemgetter('id')):
                    print(key)
                    count = 0.0
                    type = ''
                    start_time = ''
                    for k in value:
                        attend = k['attend']
                        if count == 0.0:
                            final_list.append(k['attend'])
                            type = attend.punch
                            start_time = attend.timestamp
                            count = 1.0
                        else:
                            new_attend = k['attend']
                            if new_attend.punch != type:
                                final_list.append(k['attend'])
                                type = new_attend.punch
                                start_time = new_attend.timestamp
                            else:
                                end_time = new_attend.timestamp
                                diff = end_time - start_time
                                seconds = diff.total_seconds()
                                minutes = seconds / 60
                                if self.time_type:
                                    if self.time_difference and self.time_type == 's':
                                        if seconds > self.time_difference:
                                            final_list.append(k['attend'])
                                            type = new_attend.punch
                                            start_time = new_attend.timestamp
                                    if self.time_difference and self.time_type == 'm':
                                        if seconds > self.time_difference:
                                            if minutes > self.time_difference:
                                                final_list.append(k['attend'])
                                                type = new_attend.punch
                                                start_time = new_attend.timestamp
                                else:
                                    final_list.append(k['attend'])
                                    type = new_attend.punch
                                    start_time = new_attend.timestamp
                _logger.info(f'final_list is ==========={final_list}')
                _logger.info(f'len(final_list) ==========={len(final_list)}')

                for attendance in final_list:
                    _logger.info(f'attendance ==========={attendance}')
                    employee_location_line = employee_location_line_obj.search(
                        [("zk_num", "=", int(attendance.user_id)), ('location_id', '=', machine.location_id.id),
                         ('machine_id', '=', machine.id)])
                    if employee_location_line:
                        employee_id = employee_location_line.employee_id
                        date = attendance.timestamp
                        date1 = datetime.datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
                        date = tz.normalize(tz.localize(date1)).astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
                        if attendance.punch == 0:
                            attendance_id = attendance_obj.search(
                                [('employee_id', '=', employee_id.id), ('check_in', '!=', False),
                                 ('check_in', '=', str(date))])
                            if not attendance_id:
                                attendance_obj.create({'check_in': date, 'employee_id': employee_id.id})
                        if attendance.punch == 1:
                            # ===== first setup check if employee not have any check out in this time =======
                            if employee_id.zknumber == "583":
                                print('========= attendance =======', attendance)
                            attendance_id = attendance_obj.search(
                                [('employee_id', '=', employee_id.id), ('check_out', '=', str(date))])
                            print('attendance_id ======', attendance_id)
                            if not attendance_id:
                                # ============ this is in without out =======
                                # get last record
                                # get last record that in without out
                                attendance_ids = attendance_obj.search(
                                    [('employee_id', '=', employee_id.id), ('check_in', '!=', False),
                                     ('check_in', '<', str(date)),
                                     ('check_out', '=', False)], order='check_in desc', limit=1)
                                print('============ attendance_ids', attendance_ids)
                                # ======= this is in and my by out
                                attendance_last = attendance_obj.search(
                                    [('employee_id', '=', employee_id.id), ('check_in', '!=', False)],
                                    order='check_in desc', limit=1)
                                if ((
                                        attendance_last.check_in and attendance_ids.check_in and attendance_ids.check_in >= attendance_last.check_in)
                                        or not attendance_last.check_in or not attendance_ids.check_in):

                                    if attendance_ids:
                                        # if date time in another day
                                        # create new record with data time out in record (in and out)
                                        print('============== enter here ============')
                                        record = attendance_ids
                                        rec_in = record.check_in
                                        rec_out = date
                                        print('========= rec_in', rec_in)
                                        print('========= rec_out', rec_out)
                                        dt2 = datetime.datetime.strptime(rec_out, '%Y-%m-%d %H:%M:%S')
                                        time_difference = dt2 - rec_in
                                        difference_in_hours = time_difference.total_seconds() / 3600
                                        print('======== difference_in_hours =========', difference_in_hours)
                                        if difference_in_hours > 24:
                                            attendance_obj.create(
                                                {
                                                    'check_in': date,
                                                    'check_out': date,
                                                    'employee_id': employee_id.id,
                                                }
                                            )
                                        else:
                                            print('============== enter here 2 ============')
                                            attendance_ids.write({'check_out': date})
                                    else:
                                        print('============== enter here 3 ============')
                                        if not attendance_last.check_in:
                                            attendance_obj.create(
                                                {
                                                    'check_in': date,
                                                    'check_out': date,
                                                    'employee_id': employee_id.id,
                                                }
                                            )
                                else:
                                    attendance_obj.create(
                                        {
                                            'check_in': date,
                                            'check_out': date,
                                            'employee_id': employee_id.id
                                        }
                                    )
            except Exception as e:
                raise UserError('The connection has not been achieved: %s' % (e))
            finally:
                if conn:
                    conn.enable_device()
                    conn.disconnect()

    def continue_create_attendance(self):
        pass


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in = fields.Datetime(string="Check In", default='', required=False)

    def name_get(self):
        result = []
        for attendance in self:
            if not attendance.check_out:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s") % {
                    'empl_name': attendance.employee_id.name,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                            fields.Datetime.from_string(
                                                                                                attendance.check_in))),
                }))
            else:
                if attendance.check_in:
                    result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
                        'empl_name': attendance.employee_id.name,
                        'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                                fields.Datetime.from_string(
                                                                                                    attendance.check_in))),
                        'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                                 fields.Datetime.from_string(
                                                                                                     attendance.check_out))),
                    }))
                else:
                    result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
                        'empl_name': attendance.employee_id.name,
                        'check_in': 'Undefined',
                        'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                                 fields.Datetime.from_string(
                                                                                                     attendance.check_out))),
                    }))
        return result

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            if attendance.check_in:
                last_attendance_before_check_in = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '!=', False),
                    ('check_in', '<=', attendance.check_in),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                    raise exceptions.ValidationError(
                        _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                            'empl_name': attendance.employee_id.name,
                            'datetime': fields.Datetime.to_string(
                                fields.Datetime.context_timestamp(self,
                                                                  fields.Datetime.from_string(attendance.check_in))),
                        })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ])
                # ~ if no_check_out_attendances:
                # ~ raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                # ~ 'empl_name': attendance.employee_id.name_related,
                # ~ 'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                # ~ })
            # ~ else:
            # ~ # we verify that the latest attendance with check_in time before our check_out time
            # ~ # is the same as the one before our check_in time computed before, otherwise it overlaps
            # ~ last_attendance_before_check_out = self.env['hr.attendance'].search([
            # ~ ('employee_id', '=', attendance.employee_id.id),
            # ~ ('check_in', '<', attendance.check_out),
            # ~ ('id', '!=', attendance.id),
            # ~ ], order='check_in desc', limit=1)
            # ~ if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
            # ~ raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
            # ~ 'empl_name': attendance.employee_id.name,
            # ~ 'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_attendance_before_check_out.check_in))),
            # ~ })


class hrEmployee(models.Model):
    _inherit = 'hr.employee'

    zk_location_line_ids = fields.One2many('zk.employee.location.line', 'employee_id', string='Locations')
    zknumber = fields.Char("Number zk")

    def delete_employee_zk(self):
        machine_id = self.env['zk.machine'].search([('id', '=', int(self.env.context.get('machine_id')))])
        machine_ip = machine_id.name
        port = machine_id.port
        password = 0
        if machine_id.password:
            password = machine_id.password
        zk = ZK(machine_ip, port=port, timeout=50, password=password, force_udp=False, ommit_ping=False)
        conn = ''
        try:
            conn = zk.connect()
            conn.disable_device()
            employee_location_line = self.env['zk.employee.location.line'].search(
                [('employee_id', '=', self.id), ('machine_id', '=', machine_id.id)])
            conn.delete_user(uid=employee_location_line.uid)
            machine_id.employee_ids = machine_id.employee_ids - self
            employee_location_line.unlink()
        except Exception as e:
            raise UserError('Unable to complete user registration')
        finally:
            if conn != '':
                conn.enable_device()
                conn.disconnect()
        return True

    def _compute_hours_last_month(self):
        """
        Compute hours in the current month, if we are the 15th of october, will compute hours from 1 oct to 15 oct
        """
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
            tz = pytz.timezone(employee.tz or 'UTC')
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            end_tz = now_tz
            end_naive = end_tz.astimezone(pytz.utc).replace(tzinfo=None)

            hours = sum(
                att.worked_hours or 0
                for att in employee.attendance_ids.filtered(
                    lambda
                        att: att.check_in and att.check_in >= start_naive and att.check_out and att.check_out <= end_naive
                )
            )

            employee.hours_last_month = round(hours, 2)
            employee.hours_last_month_display = "%g" % employee.hours_last_month

    def disassociate_employee_zk(self):
        machine_id = self.env['zk.machine'].search([('id', '=', int(self.env.context.get('machine_id')))])
        employee_location_line = self.env['zk.employee.location.line'].search(
            [('employee_id', '=', self.id), ('machine_id', '=', machine_id.id)])
        machine_id.employee_ids = machine_id.employee_ids - self
        employee_location_line.unlink()
        return True


class hrZkEmployeeLocationLine(models.Model):
    _name = 'zk.employee.location.line'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    zk_num = fields.Integer(string="ZKSoftware Number", help="ZK Attendance User Code", required=True)
    machine_id = fields.Many2one('zk.machine', string="Machine", required=True)
    location_id = fields.Many2one('zk.machine.location', related='machine_id.location_id', string="Location")
    uid = fields.Integer('Uid')

    _sql_constraints = [('unique_location_emp', 'unique(employee_id,location_id)',
                         'There is a record of this employee for this location.')]


class PublicEmployeeProfile(models.Model):
    _inherit = "hr.employee.public"

    zknumber = fields.Char("Number zk")
