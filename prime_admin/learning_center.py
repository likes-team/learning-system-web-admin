from app.core import CoreModule
from .models import ContactPerson, Dashboard, Earning, Equipment, Expenses, Inventory, Member, OrientationAttendance, Registration, Secretary, Supplies



class LearningManagementModule(CoreModule):
    module_name = 'learning_management'
    module_icon = 'fa-map'
    module_link = 'lms.dashboard'
    module_short_description = "Learning Management"
    module_long_description = "Learning Management System"
    models = [
        Registration,
        Member,
        Earning,
        Secretary,
        OrientationAttendance,
        Expenses,
        Inventory,
        Dashboard,
        ContactPerson,
        Equipment,
        Supplies
    ]
    version = '1.0'
    sidebar = {
        'Dashboard': [
            Dashboard
        ],
        'System': [
            Registration,
            Member,
            Earning,
            ContactPerson,
            Secretary,
            OrientationAttendance,
            Expenses,
        ],
        'Inventory': [
            Equipment,
            Supplies
        ]
    }
