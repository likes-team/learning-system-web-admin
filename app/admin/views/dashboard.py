from flask import redirect, url_for, request, jsonify
from flask_login import login_required
from app.core.models import CoreModule, CoreModel
from app.admin import bp_admin
from app.admin.models import AdminDashboard
from app.admin.templating import admin_dashboard, DashboardBox


@bp_admin.route('/') # move to views
@login_required
def dashboard():
    from app.auth.models import User

    if AdminDashboard.__view_url__ == 'bp_admin.no_view_url':
        return redirect(url_for('bp_admin.no_view_url'))
    
    options = {
        'box1': DashboardBox("Total Modules","Installed",CoreModule.objects.count()),
        'box2': DashboardBox("System Models","Total models",CoreModel.objects.count()),
        'box3': DashboardBox("Users","Total users",User.objects.count()),
        'scripts': [{'bp_admin.static': 'js/dashboard.js'}]
    }

    return admin_dashboard(AdminDashboard, **options)


@bp_admin.route('/dashboard/get-dashboard-users', methods=['GET'])
def get_dashboard_users():
    from app.auth.models import User

    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))

    users = User.objects().order_by('active').skip(start).limit(length)

    _table_data = []

    for user in users:
        _table_data.append([
            str(user.id),
            {
                'name': user.full_name, 
                'username': user.username},
            user.role.name,
            user.active,
            user.active,
        ])

    response = {
        'draw': draw,
        'recordsTotal': users.count(),
        'recordsFiltered': users.count(),
        'data': _table_data,
    }

    return jsonify(response)


@bp_admin.route('/dashboard/approve-user', methods=['POST'])
def approve_user():
    from app.auth.models import User

    user_id = request.json['user_id']

    user = User.objects.get_or_404(id=user_id)

    user.active = True

    user.save()

    return jsonify(True)