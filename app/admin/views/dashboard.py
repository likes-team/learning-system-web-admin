import pymongo
from flask_migrate import current
from config import TIMEZONE
from datetime import datetime
from flask import redirect, url_for, request, jsonify
from flask.templating import render_template
from flask_login import login_required, current_user
from app import mongo
from app.core.models import CoreModule, CoreModel
from app.admin import bp_admin
from app.admin.models import AdminDashboard
from app.admin.templating import admin_dashboard, DashboardBox


@bp_admin.route('/') # move to views
@login_required
def dashboard():
    if current_user.is_authenticated and current_user.role.name != "Admin":
        return redirect(url_for('lms.members'))

    if current_user.role.name != "Admin":
        return render_template('auth/authorization_error.html')

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
    search_value = request.args.get("search[value]")

    # users = User.objects(is_deleted__ne=True).order_by('active').skip(start).limit(length)

    if search_value != '':
        query = list(mongo.db.auth_users.aggregate([
            {"$match": {
                "lname": {"$regex": search_value}
            }},
            {"$lookup": {"from": "auth_user_roles", "localField": "role",
                         "foreignField": "_id", 'as': "role"}},
            {"$sort": {
                'fname': pymongo.ASCENDING
            }}
        ]))
        total_records = len(query)
    else:
        query = list(mongo.db.auth_users.aggregate([
            {"$lookup": {"from": "auth_user_roles", "localField": "role",
                         "foreignField": "_id", 'as': "role"}},
            {"$skip": start},
            {"$limit": length},
            {"$sort": {
                'fname': pymongo.ASCENDING
            }}
        ]))
        total_records = mongo.db.auth_users.find().count()
        
    filtered_records = len(query)

    table_data = []

    for data in query:
        print(data)
        id = data.get('_id', '')
        full_employee_id = data.get('full_employee_id', '')
        lname = data.get('lname', '')
        fname = data.get('fname', '')
        username = data.get('username', '')
        role = data.get('role', '')
        active = data.get('active', '')
        
        table_data.append([
            str(id),
            full_employee_id,
            {
                'name': fname + " " + lname,
                'username': username
            },
            role[0]['name'],
            active,
            active
        ])
   
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }

    return jsonify(response)


@bp_admin.route('/dashboard/approve-user', methods=['POST'])
def approve_user():
    from app.auth.models import User
    from prime_admin.functions import generate_employee_id
    from prime_admin.globals import get_date_now

    user_id = request.json['user_id']

    user = User.objects.get_or_404(id=user_id)

    generated_employee_id = ""
    
    last_registration_number = User.objects(active=True).order_by('-employee_id_no').first()

    date_now = get_date_now()

    if last_registration_number:
        generated_employee_id = generate_employee_id(last_registration_number.employee_id_no)
    else:
        generated_employee_id = str(date_now.year) + '%02d' % date_now.month + "0001"

    user.full_employee_id = generated_employee_id
    user.employee_id_no = last_registration_number.employee_id_no + 1 if last_registration_number is not None else 1
    user.active = True

    user.save()

    return jsonify(True)


@bp_admin.route('/dashboard/reject-user', methods=['POST'])
def reject_user():
    from app.auth.models import User

    user_id = request.json['user_id']

    user = User.objects.get_or_404(id=user_id)

    user.is_deleted = True
    user.is_archived = True
    user.status = "rejected"

    user.save()

    return jsonify(True)


