import pymongo
from bson import ObjectId
from flask import redirect, url_for, request, jsonify
from flask.templating import render_template
from flask_login import login_required, current_user
from app import mongo
from app.core.models import CoreModule, CoreModel
from app.admin import bp_admin
from app.admin.models import AdminDashboard
from app.admin.templating import admin_dashboard, DashboardBox



@bp_admin.route('/dashboard/get-dashboard-users', methods=['GET'])
def get_dashboard_users():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    role = request.args.get('role')

    _filter = {
        'status': {'$ne': 'rejected'}
    }

    if search_value != '':
        _filter['lname'] = {"$regex": search_value}
    
    if role != 'all':
        _filter['role'] = ObjectId(role)

    query = list(mongo.db.auth_users.aggregate([
        {"$match": _filter},
        {"$lookup": {"from": "auth_user_roles", "localField": "role",
                        "foreignField": "_id", 'as': "role"}},
        {"$skip": start},
        {"$limit": length},
        {"$sort": {
            'fname': pymongo.ASCENDING
        }}
    ]))
    filtered_records = mongo.db.auth_users.find(_filter).count()

    table_data = []

    for data in query:
        full_employee_id = data.get('full_employee_id', '')
        lname = data.get('lname', '')
        fname = data.get('fname', '')
        username = data.get('username', '')
        role = data.get('role', '')
        active = data.get('active', False)
        is_employee = data.get('is_employee', False)
        is_teacher = data.get('is_teacher', False)
        branch_id = data.get('branch')
        branch_ids = data.get('branches')
        branches = []
        if branch_ids and len(branch_ids) > 0:
            for id in branch_ids:
                name = mongo.db.lms_branches.find_one({'_id': ObjectId(id)})['name']
                branches.append(name)
        else:
            branch = mongo.db.lms_branches.find_one({'_id': ObjectId(branch_id)})
            if branch:
                branches.append(branch['name'])
        branches = ', '.join(branches)
        employee_information = data.get('employee_information', {})
        ee = employee_information.get('ee', {})
        er = employee_information.get('er', {})
    
        table_data.append([
            str(data.get('_id', '')),
            full_employee_id,
            {
                'name': fname + " " + lname,
                'username': username
            },
            role[0]['name'],
            branches,
            str(employee_information.get('salary_rate', '')),
            str(ee.get('sss', '')),
            str(ee.get('phil', '')),
            str(ee.get('pag_ibig', '')),
            str(er.get('sss', '')),
            str(er.get('phil', '')),
            str(er.get('pag_ibig', '')),
            is_employee,
            is_teacher,
            active,
            active
        ])
   
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': filtered_records,
        'data': table_data,
    }

    return jsonify(response)


@bp_admin.route('/dashboard/reject-user', methods=['POST'])
def reject_user():
    from app.auth.models import User

    user_id = request.json['user_id']
    mongo.db.auth_users.update_one({
        '_id': ObjectId(user_id)
    },
    {'$set': {
        'is_deleted': True,
        'is_archived': True,
        'status': 'rejected'
    }})
    return jsonify(True)


