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


@bp_lms.route('/payroll/create-payslip')
def create_payslip_page():
    branches = access.get_current_user_branches()
    return render_template('lms/payroll/create_payslip_page.html', branches=branches)

    
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


@bp_lms.route('/employees/<string:employee_id>/get-salary-rate', methods=['GET'])
def get_employee_salary_rate(employee_id):
    query = mongo.db.lms_fund_wallet_transactions.find_one({'description': employee_id, 'category': 'Bookeeper'})
    
    if query is None:
        query = mongo.db.auth_users.find_one({"_id": ObjectId(employee_id)})
        employee_information = query.get('employee_information', {})
        salary_rate = str(employee_information.get('salary_rate', 0))
        return jsonify({'status': 'error', 'message': "Bookeeper not found", 'data': {'salary_rate': salary_rate}}), 200
    
    employee_information = query.get('employee_information')
    salary_rate = str(employee_information.get('salary_rate'))
    return jsonify({'status': 'success', 'data': {'salary_rate': salary_rate}})


@bp_lms.route('/payroll/create-payslip', methods=['POST'])
def create_payslip():
    form = request.form
    
    branch_id = form.get('branch')
    employee = form.get('employee')
    position = form.get('position')
    billing_month_from = form.get('billing_month_from', None)
    billing_month_to = form.get('billing_month_to', None)
    no_of_days = form.get('no_of_days')
    day_off = form.get('day_off')
    absent_days = form.get('absent_days')
    total_working_days = form.get('total_working_days')
    no_of_session = form.get('no_of_session')
    salary_rate = form.get('salary_rate')
    total_salary_amount = form.get("total_salary_amount")
    food_allowance = form.get("food_allowance")
    accommodation = form.get("accommodation")
    gross_salary = form.get('gross_salary')
    cash_advance = form.get('cash_advance')
    government_benefits = form.get('goverment_benefits')
    accommodation_deduction = form.get("accommodation_deduction")
    total_amount_due = form.get('total_amount_due')
    settled_by = form.get('settled_by')

    
    with mongo.cx.start_session() as session:
        with session.start_transaction():
            accounting = mongo.db.lms_accounting.find_one({
                "branch": ObjectId(branch_id),
            })

            if accounting:
                with decimal.localcontext(D128_CTX):
                    previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')

                    if decimal.Decimal(total_amount_due) > previous_fund_wallet.to_decimal():
                        return jsonify({
                            'status': 'error',
                            'message': "Insufficient fund wallet balance"
                        }), 400
                        
                    new_total_fund_wallet = previous_fund_wallet.to_decimal() - decimal.Decimal(total_amount_due)
                    balance = Decimal128(previous_fund_wallet.to_decimal() - Decimal128(str(total_amount_due)).to_decimal())

                    mongo.db.lms_accounting.update_one({
                        "branch": ObjectId(branch_id)
                    },
                    {'$set': {
                        "total_fund_wallet": Decimal128(new_total_fund_wallet)
                    }},session=session)
            else:
                raise Exception("Likes Error: Accounting data not found")
            
            payslip_doc = mongo.db.lms_payroll_payslips.insert_one({
                'branch': ObjectId(branch_id),
                'employee': employee,
                'position': position,
                'billing_month_from': billing_month_from,
                'billing_month_to': billing_month_to,
                'no_of_days': no_of_days,
                'day_off': day_off,
                'absent_days': absent_days,
                'total_working_days': total_working_days,
                'no_of_session': no_of_session,
                'salary_rate': salary_rate,
                'total_salary_amount': total_salary_amount,
                'food_allowance': food_allowance,
                'accommodation': accommodation,
                'gross_salary': gross_salary,
                'cash_advance': cash_advance,
                'government_benefits': government_benefits,
                'accommodation_deduction': accommodation_deduction,
                'total_amount_due': total_amount_due,
                'settled_by': settled_by
            })
            
            mongo.db.lms_fund_wallet_transactions.insert_one({
                'type': 'expenses',
                'running_balance': balance,
                'branch': ObjectId(branch_id),
                'date': get_date_now(),
                'category': 'salary',
                'description': employee,
                'bank_name': '',
                'account_name': '',
                'account_no': '',
                'billing_month_from': billing_month_from,
                'billing_month_to': billing_month_to,
                'qty': None,
                'unit_price': None,
                'total_amount_due': Decimal128(total_amount_due),
                'settled_by': settled_by,
                'remittance': '',
                'sender': '',
                'contact_no': '',
                'address': '',
                'status': None,
                'reference_no': '',
                'employee_information': None,
                'created_at': get_date_now(),
                'created_by': current_user.fname + " " + current_user.lname,
                'payslip': ObjectId(payslip_doc.inserted_id)
            },session=session)
            
    response = {
        'status': 'success',
        'message': "Payslip added successfully!"
    }
    return jsonify(response), 201
