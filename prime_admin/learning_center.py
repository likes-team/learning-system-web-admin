from app.core import CoreModule
from .models import (
    CashFlow, Partner, Dashboard, Earning, Equipment, Expenses, Inventory, Marketer, Member, 
    OrientationAttendance, Registration, Secretary, Supplies, Utilities
)


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
        Partner,
        Equipment,
        Supplies,
        Utilities,
        Marketer,
        CashFlow
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
            Partner,
            Marketer,
            Secretary,
            OrientationAttendance,
            # Expenses,
        ],
        'Accounting': [
            CashFlow
        ],
        'Inventory': [
            Supplies,
            # Equipment,
            # Utilities
        ]
    }
