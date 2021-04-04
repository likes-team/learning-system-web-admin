from flask import redirect, url_for
from flask_login import login_required
from app.core.models import CoreModule, CoreModel
from prime_admin import bp_lms
from prime_admin.models import Dashboard
from app.admin.templating import admin_dashboard, DashboardBox


@bp_lms.route('/')
@bp_lms.route('/dashboard')
@login_required
def dashboard():
    from app.auth.models import User
    
    options = {
        'box1': DashboardBox("Number of enrollees","Current", 0),
        'box2': DashboardBox("Total Sales","Montly", 0),
        'box3': DashboardBox("Gross Income","Total users", 0),
    }

    return admin_dashboard(
        Dashboard,
        **options,
        dashboard_template="lms/dashboard.html",
        module="learning_management",
        
    )
