from app.core import CoreModule
from .models import Dashboard, Earning, Expenses, Inventory, Member, OrientationAttendance, Partner, Registration, Secretary, Teacher, Student, TrainingCenter



class LearningManagementModule(CoreModule):
    module_name = 'learning_management'
    module_icon = 'fa-map'
    module_link = 'lms.dashboard'
    module_short_description = "Learning Management"
    module_long_description = "Learning Management System"
    models = [
        TrainingCenter, 
        Teacher, 
        Student, 
        Registration, 
        Member, Earning, 
        Partner, 
        Secretary, 
        OrientationAttendance,
        Expenses,
        Inventory,
        Dashboard
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
            Secretary,
            OrientationAttendance,
            Expenses,
            Inventory,
        ]
    }
