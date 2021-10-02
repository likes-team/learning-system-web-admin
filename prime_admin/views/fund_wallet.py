from bson.decimal128 import create_decimal128_context
from bson.objectid import ObjectId
from flask_mongoengine import json
import pytz
from config import TIMEZONE
import decimal
from prime_admin.globals import PARTNERREFERENCE, SECRETARYREFERENCE, convert_to_utc, get_date_now
from app.auth.models import Earning, User
from prime_admin.forms import CashFlowAdminForm, CashFlowSecretaryForm, DepositForm, OrientationAttendanceForm, WithdrawForm
from flask.helpers import flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import redirect
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Accounting, Branch, CashFlow, CashOnHand, Expenses, FundWallet, OrientationAttendance, Registration, Batch, Orientator
from flask import jsonify, request
from datetime import date, datetime
from mongoengine.queryset.visitor import Q
from bson import Decimal128
from app import mongo



D128_CTX = create_decimal128_context()


@bp_lms.route('/fund-wallet')
@login_required
def fund_wallet():

    # if current_user.role.name == "Secretary":
    #     form = CashFlowSecretaryForm()

    # else:
    #     form = CashFlowAdminForm()
    
    _table_data = []

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    else:
        branches = Branch.objects

    # orientators = Orientator.objects()

    modals = [
        'lms/add_funds_modal.html',
        'lms/add_expenses_modal.html',
    ]

    return admin_table(
        FundWallet,
        fields=[],
        # form=form,
        table_data=_table_data,
        table_columns=['id'],
        heading="Fund Wallet",
        subheading="Funds and Expenses",
        title="Fund Wallet",
        table_template="lms/fund_wallet.html",
        modals=modals,
        branches=branches
        )


@bp_lms.route('/add-fund', methods=['POST'])
@login_required
def add_fund():
    date = request.form['date']
    bank_name = request.form['bank_name']
    transaction_no = request.form['transaction_no']
    sender = request.form['sender']
    amount_received = request.form['amount_received']
    receiver = request.form['receiver']
    remarks = request.form['remarks']
    
    # try:
    with mongo.cx.start_session() as session:
        with session.start_transaction():
            accounting = mongo.db.lms_accounting.find_one({
                "branch": current_user.branch.id,
            })

            if accounting:
                with decimal.localcontext(D128_CTX):
                    print(accounting)
                    previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')

                    new_total_fund_wallet = previous_fund_wallet.to_decimal() + decimal.Decimal(amount_received)

                    mongo.db.lms_accounting.update_one({
                        "branch": current_user.branch.id
                    },
                    {'$set': {
                        "total_fund_wallet": Decimal128(new_total_fund_wallet)
                    }},session=session)
            else:
                pass

            mongo.db.lms_fund_wallet_transactions.insert_one({
                'branch': current_user.branch.id,
                'date': convert_to_utc(date),
                'bank_name': bank_name,
                'transaction_no': transaction_no,
                'sender': sender,
                'amount_received': Decimal128(amount_received),
                'receiver': receiver,
                'remarks':remarks,
                'previous_total_fund_wallet': previous_fund_wallet,
                'new_total_fund_wallet': Decimal128(new_total_fund_wallet),
                'created_at': get_date_now(),
                'created_by': current_user.fname + " " + current_user.lname
            },session=session)


    flash('Fund added successfully', 'success')
    # except Exception as err:
    #     flash(str(err), 'error')
    
    return redirect(url_for('lms.fund_wallet'))


@bp_lms.route('/add-expenses', methods=['POST'])
@login_required
def add_expenses():
    date = request.form['date']
    category = request.form['category']
    account_no = request.form['account_no']
    billing_month = request.form['billing_month']
    settled_by = request.form['settled_by']
    total_amount_due = request.form['total_amount_due']
    remarks = request.form['remarks']
    
    # try:
    with mongo.cx.start_session() as session:
        with session.start_transaction():
            accounting = mongo.db.lms_accounting.find_one({
                "branch": current_user.branch.id,
            })

            # if accounting:
            #     with decimal.localcontext(D128_CTX):
            #         print(accounting)
            #         previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')

            #         new_total_fund_wallet = previous_fund_wallet.to_decimal() + decimal.Decimal(amount_received)

            #         mongo.db.lms_accounting.update_one({
            #             "branch": current_user.branch.id
            #         },
            #         {'$set': {
            #             "total_fund_wallet": Decimal128(new_total_fund_wallet)
            #         }},session=session)
            # else:
            #     pass

            mongo.db.lms_expenses_transactions.insert_one({
                'branch': current_user.branch.id,
                'date': convert_to_utc(date),
                'category': category,
                'account_no': account_no,
                'billing_month': billing_month,
                'total_amount_due': Decimal128(total_amount_due),
                'settled_by': settled_by,
                'remarks':remarks,
                'created_at': get_date_now(),
                'created_by': current_user.fname + " " + current_user.lname
            },session=session)


    flash('Process successfully', 'success')
    # except Exception as err:
    #     flash(str(err), 'error')
    
    return redirect(url_for('lms.fund_wallet'))


@bp_lms.route('/api/dtbl/add-funds-transactions', methods=['GET'])
def get_dtbl_add_funds_transactions():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        if current_user.role.name == "Admin":
            transactions = FundWallet.objects()
            accounting = mongo.db.lms_accounting.find()
        elif current_user.role.name == "Partner":
            transactions = FundWallet.objects(branch__in=current_user.branches)
            accounting = mongo.db.lms_accounting.find()

        # total_fund_wallet = accounting['fund_wallet']

    else:
        print(branch_id)
        if current_user.role.name == "Secretary":
            transactions = FundWallet.objects()(branch=current_user.branch)
            accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id})
        elif current_user.role.name == "Admin":
            transactions = FundWallet.objects(branch=branch_id)
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
        elif current_user.role.name == "Partner":
            transactions = FundWallet.objects(branch=branch_id)
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})

        total_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else '0.00' 

    data = []
    
    for transaction in transactions:
        if type(transaction.date) == datetime:
            local_datetime = transaction.date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(transaction.date == str):
            to_date = datetime.strptime(transaction.date, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''

        data.append([
            local_datetime,
            transaction.bank_name,
            transaction.transaction_no,
            transaction.sender,
            str(transaction.amount_received),
            transaction.receiver,
            transaction.remarks,
        ])

    print(data)

    response = {
        'draw': draw,
        'recordsTotal': transactions.count(),
        'recordsFiltered': transactions.count(),
        'data': data,
        'totalFundWallet': str(total_fund_wallet)
        }

    return jsonify(response)




@bp_lms.route('/api/dtbl/expenses-transactions', methods=['GET'])
def get_dtbl_expenses_transactions():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        if current_user.role.name == "Admin":
            transactions = Expenses.objects()
            accounting = mongo.db.lms_accounting.find()
        elif current_user.role.name == "Partner":
            transactions = Expenses.objects(branch__in=current_user.branches)
            accounting = mongo.db.lms_accounting.find()

        # total_fund_wallet = accounting['fund_wallet']

    else:
        print(branch_id)
        if current_user.role.name == "Secretary":
            transactions = Expenses.objects()(branch=current_user.branch)
            accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id})
        elif current_user.role.name == "Admin":
            transactions = Expenses.objects(branch=branch_id)
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
        elif current_user.role.name == "Partner":
            transactions = Expenses.objects(branch=branch_id)
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})

        # total_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else '0.00' 

    data = []
    total_utilities = decimal.Decimal(0)
    total_office_supplies = decimal.Decimal(0)
    total_salaries_and_rebates = decimal.Decimal(0)
    total_other_expenses = decimal.Decimal(0)
    
    for transaction in transactions:
        if type(transaction.date) == datetime:
            local_datetime = transaction.date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(transaction.date == str):
            to_date = datetime.strptime(transaction.date, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''

        if transaction.category == "utilities":
            total_utilities = total_utilities + transaction.total_amount_due
        elif transaction.category == "office_supplies":
            total_office_supplies = total_office_supplies + transaction.total_amount_due
        elif transaction.category == "salary_and_rebates":
            total_salaries_and_rebates = total_salaries_and_rebates + transaction.total_amount_due
        elif transaction.category == "other_expenses":
            total_other_expenses = total_other_expenses + transaction.total_amount_due

        data.append([
            local_datetime,
            transaction.category,
            transaction.account_no,
            transaction.billing_month,
            transaction.settled_by,
            str(transaction.total_amount_due),
            transaction.remarks,
        ])

    print(data)

    response = {
        'draw': draw,
        'recordsTotal': transactions.count(),
        'recordsFiltered': transactions.count(),
        'data': data,
        'totalUtilities': str(total_utilities),
        'totalOfficeSupplies': str(total_office_supplies),
        'totalSalariesAndRebates': str(total_salaries_and_rebates),
        'totalOtherExpenses': str(total_other_expenses)
        }

    return jsonify(response)
