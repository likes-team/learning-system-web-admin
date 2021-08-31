from flask import current_app
from app.core import CoreModule
from .models import AdminDashboard, AdminApp
from app.auth.models import User,Role
from prime_admin.models import Branch, Batch



class AdminModule(CoreModule):
    module_name = 'admin'
    module_icon = 'fa-home'
    module_link = current_app.config['ADMIN']['HOME_URL']
    module_short_description = 'Administration'
    module_long_description = "Administration Dashboard and pages"
    models = [AdminDashboard, AdminApp, User, Role, Branch, Batch]
    version = '1.0'
    sidebar = {
        'Control Panels': [
            AdminDashboard,
            Batch,
            Branch,
        ],
        'SYSTEM': [
            User, Role
        ],
    }