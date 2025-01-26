{
    "name": "Clock Reader(ZKTECO)",
    "author": "Rightechs Solutions",
    "category": "HR",
    "website": "http://rightechs.net",
    "description": "Module for the integration between ZK Biometric Machines and Odoo.",
    'license': 'AGPL-3',
    "depends": ["base", "hr", 'hr_attendance'],
    "data": [
        "wizard/zk_create_users_wizard.xml",
        "views/biometric_machine_view.xml",
        "views/get_today_attendance.xml",
        "secuirty/res_groups.xml",
        "secuirty/ir.model.access.csv"

    ],
    'images': ['static/images/zk_screenshot.gif'],
    "active": True,
    "installable": True,
}
