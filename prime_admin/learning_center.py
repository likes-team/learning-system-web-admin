from app.admin.models import AdminDashboard, SystemLogs
from app.auth.models import User
from app.core import CoreModule
from .models import (
    Accommodation, Batch, Branch, BuyItems, CashFlow, CashOnHand, FundWallet, Partner, Dashboard, Earning, Equipment, Expenses, Inventory, Marketer, Member, 
    OrientationAttendance, Registration, Secretary, StoreRecords, Supplies, Utilities
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
        CashFlow,
        CashOnHand,
        FundWallet,
        BuyItems,
        Accommodation,
        StoreRecords,
        Batch,
        AdminDashboard, User, Branch, SystemLogs
    ]
    version = '1.0'
    sidebar = {
        'Dashboard': [
            Dashboard
        ],
        'Enrollment': [
            OrientationAttendance,
            Registration,
            Member,
            Earning,
            Partner,
            Marketer,
            Secretary,
            Batch,
            # Expenses,
        ],
        'Accounting': [
            CashOnHand,
            FundWallet,
            CashFlow,
        ],
        'Store': [
            BuyItems,
            Accommodation,
            StoreRecords,
        ],
        'Inventory': [
            Supplies,
            # Equipment,
            # Utilities
        ],
        'System': [
            AdminDashboard,
            Branch,
        ]
    }
