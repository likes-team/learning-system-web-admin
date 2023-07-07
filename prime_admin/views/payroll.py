import decimal
from bson import Decimal128
from bson.objectid import ObjectId
from datetime import datetime
import pymongo
from config import TIMEZONE
from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from app import mongo
from app.auth.models import User
from prime_admin.globals import D128_CTX, convert_to_utc, get_date_now
from prime_admin import bp_lms
from prime_admin.models import Branch, FundWallet, Registration
from prime_admin.services.fund_wallet import BusinessExpensesService
from prime_admin.helpers.employee import get_employees
from prime_admin.helpers import access
from prime_admin.services.student import StudentService
from prime_admin.services.inventory import InventoryService
from prime_admin.helpers.query_filter import StudentQueryFilter
from prime_admin.models_v2 import StudentV2
from prime_admin.services.payment import PaymentService
from prime_admin.helpers.query_filter import PaymentQueryFilter
from prime_admin.models_v2 import PaymentV2



@bp_lms.route('/payroll')
@login_required
def payroll():
    branches = access.get_current_user_branches()
    return render_template('lms/payroll/payroll_page.html', branches=branches)


@bp_lms.route('/datatables/payroll/employees', methods=['GET'])
def dt_payroll_employees():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    role = request.args.get('role')

    _filter = {
        'status': {'$ne': 'rejected'},
        'is_employee': True
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
            ''
        ])
   
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': filtered_records,
        'data': table_data,
    }

    return jsonify(response)


@bp_lms.route('/payroll/employees/<string:user_id>/edit', methods=['POST'])
def edit_payroll_employee(user_id):
    values = request.json['values']
    print(values)
    for i , val in enumerate(values):
        if val == '':
            values[i] = Decimal128(decimal.Decimal(0))
        else:
            values[i] = Decimal128(decimal.Decimal(val))
    
    salary_rate = values[0]
    ee_sss = values[1]
    ee_phil = values[2]
    ee_pag_ibig = values[3]
    er_sss = values[4]
    er_phil = values[5]
    er_pag_ibig = values[6]

    mongo.db.auth_users.update_one({
        '_id': ObjectId(user_id)
    }, {'$set': {
        'employee_information': {
            'salary_rate': salary_rate,
            'ee': {
                'sss': ee_sss,
                'phil': ee_phil,
                'pag_ibig': ee_pag_ibig
            },
            'er': {
                'sss': er_sss,
                'phil': er_phil,
                'pag_ibig': er_pag_ibig
            }
        }
    }})
    
    return jsonify({'result': True})