# -*- coding: utf-8 -*-
{
    'name': "Rt Buget Phase",

    'summary': "Rt Budget Phase module related with rt_project_phase and rt_budget",

    'description': """
    This Module is developed for creating budget for phases and departments that are working on this phase
    And Every department has a task related to this phase
    """,

    'author': "Rightechs Solutions",
    'website': "https://www.rightechs.net",

    'category': 'Project',
    'version': '1.0',

    'depends': ['base', 'project', 'hr_timesheet', 'analytic', 'hr', 'hr_contract', 'hr_hourly_cost', 'rt_project_phase', 'rt_budget', 'timesheet_grid'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/budget_views.xml',
        'views/project_project_view.xml',
        'views/project_phase_view.xml',
        'views/project_task_view.xml',
        'views/project_milestone_view.xml',
        'views/hr_employee_views.xml',
        'views/hr_timesheet_views.xml',
    ],
    "installable": True,
}

