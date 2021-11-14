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
    
    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                accounting = mongo.db.lms_accounting.find_one({
                    "branch": current_user.branch.id,
                })

                if accounting:
                    with decimal.localcontext(D128_CTX):
                        previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')
                        new_total_fund_wallet = previous_fund_wallet.to_decimal() + decimal.Decimal(amount_received)
                        balance = Decimal128(Decimal128(
                            str(accounting["total_fund_wallet"] if 'total_fund_wallet' in accounting else 0.00)).to_decimal() + Decimal128(str(amount_received)).to_decimal())

                        mongo.db.lms_accounting.update_one({
                            "branch": current_user.branch.id
                        },
                        {'$set': {
                            "total_fund_wallet": Decimal128(new_total_fund_wallet)
                        }},session=session)
                else:
                    raise Exception("Likes Error: Accounting data not found")

                mongo.db.lms_fund_wallet_transactions.insert_one({
                    'type': 'add_fund',
                    'running_balance': balance,
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
    except Exception as err:
        flash(str(err), 'error')
    
    return redirect(url_for('lms.fund_wallet'))


@bp_lms.route('/add-expenses', methods=['POST'])
@login_required
def add_expenses():
    date = request.form['date']
    category = request.form['category']
    description = request.form['description']
    account_no = request.form.get('account_no', None)
    billing_month_from = request.form.get('billing_month_from', None)
    billing_month_to = request.form.get('billing_month_to', None)
    qty = request.form.get('qty', None)
    unit_price = request.form.get('unit_price', None)
    settled_by = request.form['settled_by']
    total_amount_due = request.form['total_amount_due']
    remarks = request.form['remarks']
    
    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                accounting = mongo.db.lms_accounting.find_one({
                    "branch": current_user.branch.id,
                })

                if accounting:
                    with decimal.localcontext(D128_CTX):
                        previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')
                        new_total_fund_wallet = previous_fund_wallet.to_decimal() - decimal.Decimal(total_amount_due)
                        print("balance", str(previous_fund_wallet.to_decimal()), str(total_amount_due))
                        balance = Decimal128(previous_fund_wallet.to_decimal() - Decimal128(str(total_amount_due)).to_decimal())

                        mongo.db.lms_accounting.update_one({
                            "branch": current_user.branch.id
                        },
                        {'$set': {
                            "total_fund_wallet": Decimal128(new_total_fund_wallet)
                        }},session=session)
                else:
                    raise Exception("Likes Error: Accounting data not found")

                mongo.db.lms_fund_wallet_transactions.insert_one({
                    'type': 'expenses',
                    'running_balance': balance,
                    'branch': current_user.branch.id,
                    'date': convert_to_utc(date),
                    'category': category,
                    'description': description,
                    'account_no': account_no,
                    'billing_month_from': billing_month_from,
                    'billing_month_to': billing_month_to,
                    'qty': qty,
                    'unit_price': unit_price,
                    'total_amount_due': Decimal128(total_amount_due),
                    'settled_by': settled_by,
                    'remarks':remarks,
                    'created_at': get_date_now(),
                    'created_by': current_user.fname + " " + current_user.lname
                },session=session)
        flash('Process successfully', 'success')
    except Exception as err:
        flash(str(err), 'error')
    return redirect(url_for('lms.fund_wallet'))


@bp_lms.route('/api/dtbl/fund-wallet-statements', methods=['GET'])
def get_dtbl_fund_wallet_statements():
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

        total_fund_wallet = 0.00

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
    
    transaction: FundWallet
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
            transaction.description,
            str(transaction.amount_received) if transaction.type == "add_fund" else '',
            str(transaction.total_amount_due) if transaction.type == "expenses" else '',
            str(transaction.running_balance),
            transaction.created_by,
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


@bp_lms.route('/api/dtbl/add-funds-transactions', methods=['GET'])
def get_dtbl_add_funds_transactions():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        if current_user.role.name == "Admin":
            transactions = FundWallet.objects(type="add_fund")
            accounting = mongo.db.lms_accounting.find()
        elif current_user.role.name == "Partner":
            transactions = FundWallet.objects(branch__in=current_user.branches).filter(type="add_fund")
            accounting = mongo.db.lms_accounting.find()

        total_fund_wallet = 0.00

    else:
        print(branch_id)
        if current_user.role.name == "Secretary":
            transactions = FundWallet.objects()(branch=current_user.branch).filter(type="add_fund")
            accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id})
        elif current_user.role.name == "Admin":
            transactions = FundWallet.objects(branch=branch_id).filter(type="add_fund")
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
        elif current_user.role.name == "Partner":
            transactions = FundWallet.objects(branch=branch_id).filter(type="add_fund")
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
            transactions = FundWallet.objects(type="expenses")
            accounting = mongo.db.lms_accounting.find()
        elif current_user.role.name == "Partner":
            transactions = FundWallet.objects(branch__in=current_user.branches).filter(type="expenses")
            accounting = mongo.db.lms_accounting.find()
    else:
        if current_user.role.name == "Secretary":
            transactions = FundWallet.objects()(branch=current_user.branch).filter(type="expenses")
        elif current_user.FundWallet.name == "Admin":
            transactions = FundWallet.objects(branch=branch_id).filter(type="expenses")
        elif current_user.role.name == "Partner":
            transactions = FundWallet.objects(branch=branch_id).filter(type="expenses")

    data = []
    total_utilities = decimal.Decimal(0)
    total_office_supplies = decimal.Decimal(0)
    total_salaries_and_rebates = decimal.Decimal(0)
    total_other_expenses = decimal.Decimal(0)
    
    transaction: FundWallet
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
        elif transaction.category == "office_supply":
            total_office_supplies = total_office_supplies + transaction.total_amount_due
        elif transaction.category == "salary_and_rebates":
            total_salaries_and_rebates = total_salaries_and_rebates + transaction.total_amount_due
        elif transaction.category == "other_expenses":
            total_other_expenses = total_other_expenses + transaction.total_amount_due

        data.append([
            local_datetime,
            transaction.category,
            transaction.description,
            transaction.account_no,
            str(transaction.unit_price),
            str(transaction.qty),
            str(transaction.billing_month_from if transaction.billing_month_from is not None else '') + " - " + str(transaction.billing_month_to if transaction.billing_month_to is not None else ''),
            transaction.settled_by,
            str(transaction.total_amount_due),
            transaction.remarks,
        ])

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
