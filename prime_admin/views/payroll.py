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