from flask import current_app
from app.core import CoreModule
from .models import AdminDashboard, AdminApp, SystemLogs
from app.auth.models import User,Role
from prime_admin.models import Branch, Batch



class AdminModule(CoreModule):
    module_name = 'admin'
    module_icon = 'fa-home'
    module_link = ''
    module_short_description = 'Administration'
    module_long_description = "Administration Dashboard and pages"
    models = [AdminDashboard, AdminApp, User, Role, Branch, Batch, SystemLogs]
    version = '1.0'