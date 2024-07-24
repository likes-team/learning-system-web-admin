import decimal
import pytz
import pymongo
from datetime import datetime
from bson.decimal128 import create_decimal128_context
from bson.objectid import ObjectId
from bson import Decimal128
from config import TIMEZONE
from flask import jsonify, request, redirect
from flask.helpers import flash, url_for
from flask_login import login_required, current_user
from app import mongo
from app.auth.models import User
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import Accommodation, Accounting, Branch, CashFlow, Registration, Orientator, StoreRecords
from prime_admin.forms import CashFlowAdminForm, CashFlowSecretaryForm, DepositForm, WithdrawForm
from prime_admin.globals import PARTNERREFERENCE, convert_to_utc, get_date_now
from prime_admin.utils import currency
from prime_admin.services.fund_wallet import add_fund
from prime_admin.utils.upload import allowed_file
from prime_admin.services.s3 import upload_file


D128_CTX = create_decimal128_context()


@bp_lms.route('/cash-flow')
@login_required
def cash_flow():
    if current_user.role.name == "Secretary":
        form = CashFlowSecretaryForm()
    else:
        form = CashFlowAdminForm()
    
    _table_data = []

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Manager":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Admin":
        branches = Branch.objects

    orientators = Orientator.objects()
    modals = [
        'lms/deposit_modal.html',
        'lms/withdraw_modal.html',
        'lms/profit_modal.html',
        'lms/pre_deposit_modal.html',
    ]

    return admin_table(
        CashFlow,
        fields=[],
        form=form,
        table_data=_table_data,
        heading="Cash Flow",
        subheading="Bank Transfer",
        title="Cash Flow",
        table_template="lms/cash_flow.html",
        modals=modals,
        branches=branches,
        orientators=orientators
        )


@bp_lms.route('/deposit', methods=['POST'])
@login_required
def deposit():
    form = request.form
    new_deposit = CashFlow()
    new_deposit.bank_name = form.get('bank_name')
    new_deposit.account_no = form.get('account_no')
    new_deposit.account_name = form.get('account_name')
    new_deposit.amount = form.get('amount')
    new_deposit.from_what = form.get('from_what')
    new_deposit.by_who = form.get('by_who')
    new_deposit.created_by = "{} {}".format(current_user.fname,current_user.lname)
    
    if form.get('deposit_branch'):
        new_deposit.branch = Branch.objects.get(id=form.get('deposit_branch'))
    else:    
        new_deposit.branch = current_user.branch
    new_deposit.type = "deposit"
    new_deposit.remarks = form.get('remarks')
    new_deposit.set_created_at()
    new_deposit.date_deposit = new_deposit.created_at
    payments = []

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            with decimal.localcontext(D128_CTX):
                accounting = mongo.db.lms_accounting.find_one({"branch": new_deposit.branch.id}, session=session)

                if accounting:
                    new_deposit.group = accounting['active_group']

                    if new_deposit.from_what in ["Sales"]:
                        new_deposit.balance = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() + Decimal128(str(new_deposit.amount)).to_decimal())
                        accounting["total_gross_sale"] = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() + Decimal128(str(new_deposit.amount)).to_decimal())

                        # TODO: Refactor
                        clients = mongo.db.lms_registrations.find({
                            "status": "registered",
                            "branch": new_deposit.branch.id
                            }, session=session)

                        for client in clients:
                            has_payment_updated = False
                            student_payments = mongo.db.lms_registration_payments.find({"payment_by": ObjectId(client['_id'])})
                            for payment in student_payments:
                                if "deposited" in payment and payment["deposited"] == "Pre Deposit":
                                    mongo.db.lms_registration_payments.update_one({
                                        "_id": payment['_id']
                                    },
                                    {"$set": {
                                        "deposited": "Yes"
                                    }},session=session)

                                    if 'amount_deposit' in client:
                                        client['amount_deposit'] = Decimal128(Decimal128(str(client['amount_deposit'])).to_decimal() + Decimal128(str(payment['amount'])).to_decimal())
                                    else:
                                        client['amount_deposit'] = payment['amount']
                                    has_payment_updated = True
                                    payments.append(payment)

                            if has_payment_updated:
                                mongo.db.lms_registrations.update_one(
                                    {"_id": client["_id"]},
                                    {"$set": {
                                        "amount_deposit": client['amount_deposit']
                                    }}, session=session)

                        mongo.db.lms_store_buyed_items.update_many(
                            {"deposited": "Pre Deposit","branch": new_deposit.branch.id}, 
                            {'$set': {'deposited': "Yes"}},session=session)

                        mongo.db.lms_accommodations.update_many(
                            {"deposited": "Pre Deposit","branch": new_deposit.branch.id},
                            {'$set': {'deposited': "Yes"}},session=session)

                        mongo.db.lms_accounting.update_one({
                            "_id": accounting["_id"]},
                            {"$set": {
                                "total_gross_sale": accounting["total_gross_sale"],
                            }}, session=session)
                    elif new_deposit.from_what == "Student Loan Payment":
                        if accounting["final_fund1"]:
                            accounting["final_fund1"] = Decimal128(Decimal128(str(accounting["final_fund1"])).to_decimal() + Decimal128(str(new_deposit.amount)).to_decimal())
                        else:
                            accounting["final_fund1"] = Decimal128(str(new_deposit.amount))

                        new_deposit.balance = accounting["final_fund1"]

                        mongo.db.lms_accounting.update_one({
                            "_id": accounting["_id"]},
                            {"$set": {
                                "final_fund1": accounting["final_fund1"],
                            }}, session=session)

                    elif new_deposit.from_what == "Emergency Fund" or new_deposit.from_what == "Refund":
                        if accounting["final_fund2"]:
                            accounting["final_fund2"] = Decimal128(Decimal128(str(accounting["final_fund2"])).to_decimal() + Decimal128(str(new_deposit.amount)).to_decimal())
                        else:
                            accounting["final_fund2"] = Decimal128(str(new_deposit.amount))

                        new_deposit.balance = accounting["final_fund2"]

                        mongo.db.lms_accounting.update_one({
                            "_id": accounting["_id"]},
                            {"$set": {
                                "final_fund2": accounting["final_fund2"],
                            }}, session=session)
                else:
                    accounting = Accounting()
                    accounting.branch = new_deposit.branch
                    accounting.active_group = 1
                    
                    if new_deposit.from_what == "Sales":
                        accounting.total_gross_sale = new_deposit.amount

                        clients = mongo.db.lms_registrations.find({"status": "registered", "branch": new_deposit.branch.id}, session=session)

                        for client in clients:
                            has_payment_updated = False
                            student_payments = mongo.db.lms_registration_payments.find({"payment_by": ObjectId(client['_id'])})

                            for payment in student_payments:
                                if "deposited" in payment and payment["deposited"] == "Pre Deposit":
                                    if 'amount_deposit' in client:
                                        client['amount_deposit'] = Decimal128(Decimal128(str(client['amount_deposit'])).to_decimal() + Decimal128(str(payment['amount'])).to_decimal())
                                    else:
                                        client['amount_deposit'] = payment['amount']
                                    has_payment_updated = True
                                    payments.append(payment)

                                    mongo.db.lms_registration_payments.update_one(
                                        {"_id": payment["_id"]},
                                        {"$set": {"deposited": "Yes"}},
                                        session=session)

                            if has_payment_updated:
                                mongo.db.lms_registrations.update_one(
                                    {"_id": client["_id"]},
                                    {"$set": {
                                        "amount_deposit": client['amount_deposit']
                                    }}, session=session)

                        mongo.db.lms_store_buyed_items.update_many(
                            {"deposited": "Pre Deposit","branch": new_deposit.branch.id}, 
                            {'$set': {'deposited': "Yes"}},session=session)

                        mongo.db.lms_accommodations.update_many(
                            {"deposited": "Pre Deposit","branch": new_deposit.branch.id},
                            {'$set': {'deposited': "Yes"}},session=session)
                            
                    elif new_deposit.from_what == "Student Loan Payment":
                        accounting.final_fund1 = new_deposit.amount
                    elif new_deposit.from_what == "Emergency Fund" or new_deposit.from_what == "Refund":
                        accounting.final_fund2 = new_deposit.amount

                    new_deposit.balance = new_deposit.amount
                    new_deposit.group = accounting.active_group

                    mongo.db.lms_accounting.insert_one({
                        "_id": ObjectId(),
                        "branch": accounting.branch.id,
                        "active_group": accounting.active_group,
                        "total_gross_sale": Decimal128(str(accounting.total_gross_sale)) if accounting.total_gross_sale is not None else Decimal128("0.00"),
                        "final_fund1": Decimal128(str(accounting.final_fund1)) if accounting.final_fund1 is not None else Decimal128("0.00"),
                        "final_fund2": Decimal128(str(accounting.final_fund2)) if accounting.final_fund2 is not None else Decimal128("0.00"),
                    }, session=session)
                    
                # new_deposit.payments = payments

                mongo.db.lms_bank_statements.insert_one({
                    "_id": ObjectId(),
                    "date_deposit": new_deposit.date_deposit,
                    "bank_name": new_deposit.bank_name,
                    "account_no": new_deposit.account_no,
                    "account_name": new_deposit.account_name,
                    "amount": Decimal128(str(new_deposit.amount)),
                    "from_what": new_deposit.from_what,
                    "by_who": new_deposit.by_who,
                    "created_by": new_deposit.created_by,
                    "branch": new_deposit.branch.id,
                    "type": new_deposit.type,
                    "remarks": new_deposit.remarks,
                    "payments": payments,
                    "balance": Decimal128(str(new_deposit.balance)),
                    "group": new_deposit.group,
                    "created_at": new_deposit.created_at,
                }, session=session)
    response = {
        'status': 'success',
        'message': "Processed successfully!"
    }
    return jsonify(response), 201


@bp_lms.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    form = WithdrawForm()
    
    new_withdraw = CashFlow()
    # new_withdraw.date_deposit = convert_to_utc(str(form.date_deposit.data), "date_from")
    new_withdraw.bank_name = form.bank_name.data
    new_withdraw.account_no = form.account_no.data
    new_withdraw.account_name = form.account_name.data
    new_withdraw.amount = form.amount.data
    new_withdraw.from_what = form.from_what.data
    new_withdraw.by_who = form.by_who.data
    new_withdraw.created_by = "{} {}".format(current_user.fname,current_user.lname)
    new_withdraw.branch = Branch.objects.get(id=form.branch.data)
    new_withdraw.type = "withdraw"
    new_withdraw.remarks = form.remarks.data
    new_withdraw.set_created_at()
    new_withdraw.date_deposit = new_withdraw.created_at
    to_what = form.to_what.data

    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                accounting = Accounting.objects(branch=form.branch.data).first()

                if not accounting:
                    flash("No transaction in this branch yet!",'error')
                    return redirect(url_for('lms.cash_flow'))

                if new_withdraw.from_what == "Sales":
                    if new_withdraw.amount > accounting.total_gross_sale:
                        flash("Withdraw amount is greater than the total gross sale",'error')
                        return redirect(url_for('lms.cash_flow'))

                    accounting.total_gross_sale = accounting.total_gross_sale - new_withdraw.amount
                    new_withdraw.balance = accounting.total_gross_sale
                    mongo.db.lms_accounting.update_one({
                        "_id": accounting.id},
                        {"$set": {
                            "total_gross_sale": Decimal128(str(accounting.total_gross_sale)),
                        }}, session=session)

                elif new_withdraw.from_what == "Fund 1":
                    if new_withdraw.amount > accounting.final_fund1:
                        flash("Withdraw amount is greater than the fund",'error')
                        return redirect(url_for('lms.cash_flow'))
                    accounting.final_fund1 = accounting.final_fund1 - new_withdraw.amount
                    new_withdraw.balance = accounting.final_fund1
                    mongo.db.lms_accounting.update_one({
                        "_id": accounting.id},
                        {"$set": {
                            "final_fund1": Decimal128(str(accounting.final_fund1)),
                        }}, session=session)
                    
                elif new_withdraw.from_what == "Fund 2":
                    if new_withdraw.amount > accounting.final_fund2:
                        flash("Withdraw amount is greater than the fund",'error')
                        return redirect(url_for('lms.cash_flow'))

                    accounting.final_fund2 = accounting.final_fund2 - new_withdraw.amount
                    new_withdraw.balance = accounting.final_fund2
                    mongo.db.lms_accounting.update_one({
                        "_id": accounting.id},
                        {"$set": {
                            "final_fund2": Decimal128(str(accounting.final_fund2)),
                        }}, session=session)
                        
                new_withdraw.group = accounting.active_group
                
                mongo.db.lms_bank_statements.insert_one({
                    "_id": ObjectId(),
                    "date_deposit": new_withdraw.date_deposit,
                    "bank_name": new_withdraw.bank_name,
                    "account_no": new_withdraw.account_no,
                    "account_name": new_withdraw.account_name,
                    "amount": Decimal128(str(new_withdraw.amount)),
                    "from_what": new_withdraw.from_what,
                    "to_what": to_what,
                    "by_who": new_withdraw.by_who,
                    "created_by": new_withdraw.created_by,
                    "branch": new_withdraw.branch.id,
                    "type": new_withdraw.type,
                    "remarks": new_withdraw.remarks,
                    "balance": Decimal128(str(new_withdraw.balance)),
                    "group": new_withdraw.group,
                    "created_at": new_withdraw.created_at,
                }, session=session)

                if to_what == 'FUND WALLET':
                    add_fund(
                        branch_id=new_withdraw.branch.id,
                        thru="CASH FLOW",
                        bank_name=new_withdraw.bank_name,
                        remittance='',
                        account_name=new_withdraw.account_name,
                        account_no=new_withdraw.account_no,
                        transaction_no='',
                        amount_received=new_withdraw.amount,
                        sender='',
                        receiver='',
                        session=session
                    )

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": "Withdrawal - account_no: {}, by_who: {}, amount: {}".format(new_withdraw.account_no, new_withdraw.by_who, str(new_withdraw.amount)),
                    "from_module": "Cash Flow"
                }, session=session)

        flash('Withdraw Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.cash_flow'))



@bp_lms.route('/cash-flow/totals')
def get_totals():
    branch_id = request.args.get('branch')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    if branch_id == "all":
        return jsonify({})
    
    if current_user.role.name == "Secretary":
        branch = current_user.branch.id
    else:
        branch = branch_id

    accounting = mongo.db.lms_accounting.find_one({'branch': ObjectId(branch)})
    total_gross_sales = currency.convert_decimal128_to_decimal(accounting.get('total_gross_sale', 0.00))
    remaining = total_gross_sales * decimal.Decimal(.05)
    net = total_gross_sales * decimal.Decimal(.55)
    fund1 = total_gross_sales * decimal.Decimal(.20)
    fund2 = total_gross_sales * decimal.Decimal(.20)
    final_fund1 = currency.convert_decimal128_to_decimal(accounting.get('final_fund1', 0.00))
    final_fund2 = currency.convert_decimal128_to_decimal(accounting.get('final_fund2', 0.00))
    total_deposit = 0
    total_withdrawal = 0
    total_current_balance = 0
    
    query = list(mongo.db.lms_bank_statements.aggregate([
        {'$match': {
            'branch': ObjectId(branch),
            'from_what': "Sales",
            'group': accounting['active_group']
        }},
        {'$group': {
            '_id': {'type': '$type'},
            'total': {
                '$sum': '$amount'
            }
        }}
    ]))

    if len(query) > 0:
        for item in query:
            if item['_id']['type'] == "deposit":
                total_deposit = currency.convert_decimal128_to_decimal(item['total'])
            elif item['_id']['type'] == 'withdraw':
                total_withdrawal = currency.convert_decimal128_to_decimal(item['total'])
                
    total_current_balance = total_deposit - total_withdrawal
    response = {
        'totalGrossSales': currency.format_to_str_php(total_gross_sales),
        'remaining': currency.format_to_str_php(remaining),
        'net': currency.format_to_str_php(net),
        'fund1': currency.format_to_str_php(fund1),
        'fund2': currency.format_to_str_php(fund2),
        'finalFund1': currency.format_to_str_php(final_fund1),
        'finalFund2': currency.format_to_str_php(final_fund2),
        'totalDeposit': currency.format_to_str_php(total_deposit),
        'totalWithdrawal': currency.format_to_str_php(total_withdrawal),
        'totalCurrentBalance': currency.format_to_str_php(total_current_balance)
    }
    return jsonify(response)


@bp_lms.route('/dtbl/get-cash-flow')
def get_cash_flow():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')
    from_what = request.args.get('from_what')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    transaction_type = request.args.get('transaction_type', '')

    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
        }

        return jsonify(response)
    
    if current_user.role.name == "Secretary":
        accounting = Accounting.objects(branch=current_user.branch.id).first()
    else:
        accounting = Accounting.objects(branch=branch_id).first()

    if accounting:
        filter: dict = {}

        if current_user.role.name == "Secretary":
            if from_what == "sales":
                filter = {
                    'branch': current_user.branch.id, 
                    'group': accounting.active_group, 
                    'from_what': 'Sales',
                    'type': 'deposit'
                }
            else: # fund
                filter = {'branch': current_user.branch.id, 'group': accounting.active_group, 'from_what': {'$ne': 'Sales'}}
        else:
            if from_what == "sales":
                filter = {'branch': ObjectId(branch_id), 'group': accounting.active_group, 'from_what': 'Sales'}
            else: # fund
                filter = {'branch': ObjectId(branch_id), 'group': accounting.active_group, 'from_what': {'$ne': 'Sales'}}
        
        if date_from != "":
            filter['date_deposit'] = {"$gt": convert_to_utc(date_from, 'date_from')}
        
        if date_to != "":
            if 'date_deposit' in filter:
                filter['date_deposit']['$lt'] = convert_to_utc(date_to, 'date_to')
            else:
                filter['date_deposit'] = {'$lt': convert_to_utc(date_to, 'date_to')}
        
        if transaction_type != "":
            filter['type'] = transaction_type

        bank_statements = mongo.db.lms_bank_statements.find(filter).sort('date_deposit', pymongo.DESCENDING).skip(start).limit(length)
        recordsTotal = bank_statements.count(),
        recordsFiltered = bank_statements.count(),
    else:
        recordsTotal = 0,
        recordsFiltered = 0,
        bank_statements = []

    _table_data = []
    if current_user.role.name == "Secretary":
        with decimal.localcontext(D128_CTX):
            for statement in bank_statements:
                _id = statement.get('_id', '')
                date_deposit = statement.get('date_deposit', None)
                bank_name = statement.get('bank_name', '')
                account_no = statement.get('account_no', '')
                account_name = statement.get('account_name', '')
                amount = statement.get('amount')
                if isinstance(amount, Decimal128):
                    amount = amount.to_decimal()
                else:
                    amount = decimal.Decimal(amount)
                from_what = statement.get('fron_what', '')
                by_who = statement.get('by_who', '')
                remarks = statement.get('remarks', '')
                group = statement.get('group')
                _type = statement.get('type')
                
                _table_data.append((
                    str(_id),
                    date_deposit,
                    bank_name,
                    account_no,
                    account_name,
                    str(amount),
                    from_what,
                    by_who,
                    remarks,
                    group,
                    ''
                ))
    else:
        with decimal.localcontext(D128_CTX):
            for statement in bank_statements:
                _id = statement.get('_id', '')
                date_deposit = statement.get('date_deposit', None)
                bank_name = statement.get('bank_name', '')
                account_no = statement.get('account_no', '')
                account_name = statement.get('account_name', '')
                amount = statement.get('amount')
                if isinstance(amount, Decimal128):
                    amount = amount.to_decimal()
                else:
                    amount = decimal.Decimal(amount)
                from_what = statement.get('fron_what', '')
                to_what = statement.get('to_what', '')
                by_who = statement.get('by_who', '')
                remarks = statement.get('remarks', '')
                group = statement.get('group')
                balance = statement.get('balance', 0.00)
                _type = statement.get('type')
        
                _table_data.append((
                    str(_id),
                    date_deposit,
                    '' if _type == 'withdraw' else str(amount),
                    '' if _type == 'withdraw' else from_what,
                    '' if _type == "deposit" else str(amount),
                    str(balance) if balance is not None else '',
                    to_what,
                    '' if _type == "deposit" else from_what,
                    bank_name,
                    account_no,
                    account_name,
                    by_who,
                    remarks,
                    group,
                    ''
                ))
    response = {
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': _table_data,
    }
    return jsonify(response)


@bp_lms.route('/dtbl/get-profits-history')
def get_profits_history():
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        return jsonify({'data': []})
        
    if current_user.role.name == "Secretary":
        accounting = Accounting.objects(branch=current_user.branch.id).first()
    else:
        accounting = Accounting.objects(branch=branch_id).first()

    if accounting is None:
        return jsonify({'data': []})

    data = []

    for x in accounting.profits:
        data.append((
            x['date'],
            str(round(x['new_total_gross_sale'].to_decimal(), 2)),
            str(round(x['previous_total_gross_sale'].to_decimal(), 2)),
            str(round(x['net'].to_decimal(), 2)),
            str(round(x['remaining'].to_decimal(), 2)),
            str(round(x['new_final_fund1'].to_decimal(), 2)),
            str(round(x['previous_final_fund1'].to_decimal(), 2)),
            str(round(x['new_final_fund2'].to_decimal(), 2)),
            str(round(x['previous_final_fund2'].to_decimal(), 2))
        ))

    response = {
        'data': data
    }

    return jsonify(response)

@bp_lms.route('/profit', methods=['POST'])
@login_required
def profit():
    password = request.json['password']
    branch = request.json['branch']
    partners_percent_list = request.json['partners_percent']

    if not current_user.check_password(password):
        return jsonify({"result": "invalid_password"})

    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                with decimal.localcontext(D128_CTX):

                    accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch)},session=session)
                    
                    if accounting is None:
                        return jsonify({"result": "no_transaction"})
                
                    remaining = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() * Decimal128(".05").to_decimal())
                    net = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() * Decimal128(".55").to_decimal())
                    fund1 = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() * Decimal128(".20").to_decimal())
                    fund2 = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() * Decimal128(".20").to_decimal())
                    previous_final_fund1 = accounting["final_fund1"] if accounting["final_fund1"] is not None else Decimal128('0.00')
                    previous_final_fund2 = accounting["final_fund2"] if accounting["final_fund2"] is not None else Decimal128('0.00')
                    previous_total_gross_sale = accounting["total_gross_sale"]
                    
                    accounting["total_gross_sale"] = remaining

                    if accounting["final_fund1"]:
                        accounting["final_fund1"] = Decimal128(Decimal128(str(accounting["final_fund1"])).to_decimal() + fund1.to_decimal())
                    else: 
                        accounting["final_fund1"] = fund1

                    if accounting["final_fund2"]:
                        accounting["final_fund2"] = Decimal128(Decimal128(str(accounting['final_fund2'])).to_decimal() + fund2.to_decimal())
                    else:
                        accounting["final_fund2"] = fund2
                    
                    profit_history = {
                        'date': get_date_now(),
                        'previous_total_gross_sale': previous_total_gross_sale,
                        'new_total_gross_sale': accounting["total_gross_sale"],
                        'net': net,
                        'remaining': remaining,
                        'fund1': fund1,
                        'fund2': fund2,
                        'previous_final_fund1': previous_final_fund1,
                        'previous_final_fund2': previous_final_fund2,
                        'new_final_fund1': accounting['final_fund1'],
                        'new_final_fund2': accounting["final_fund2"],
                        'partners_percent': partners_percent_list
                    }

                    for _partner in partners_percent_list:
                        partner = mongo.db.auth_users.find_one({"_id": ObjectId(_partner['partner_id'])})

                        earnings = Decimal128((net.to_decimal() * Decimal128(_partner['percent']).to_decimal()) / Decimal128("100").to_decimal())

                        contact_person_earning = {
                            "_id": ObjectId(),
                            "payment_mode": "profit_sharing",
                            "earnings": earnings,
                            "branch": ObjectId(branch),
                            "date": get_date_now(),
                            "registered_by": current_user.id,
                            }

                        mongo.db.auth_users.update_one({
                            "_id": partner["_id"]
                            },
                            {"$push": {
                                "earnings": contact_person_earning
                            }},session=session)

                    mongo.db.lms_accounting.update_one({
                        "_id": accounting['_id'],
                    },
                    {"$set": {
                        "total_gross_sale": accounting["total_gross_sale"],
                        "final_fund1": accounting["final_fund1"],
                        "final_fund2": accounting["final_fund2"]
                    },
                    "$push": {
                        "profits": profit_history
                    },
                    "$inc": {
                        "active_group": 1
                    }},session=session)

    except Exception as exc:
        return jsonify({"result": "error"})

    return jsonify({"result": "success"})


@bp_lms.route('/archive', methods=['POST'])
@login_required
def archive():
    password = request.json['password']
    branch = request.json['branch']

    if not current_user.check_password(password):
        return jsonify({"result": "invalid_password"})

    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                with decimal.localcontext(D128_CTX):

                    accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch)},session=session)
                    
                    if accounting is None:
                        return jsonify({"result": "no_transaction"})

                    mongo.db.lms_accounting.update_one({
                        "_id": accounting['_id'],
                    },
                    {"$inc": {
                        "active_group": 1
                    }},session=session)

    except Exception as exc:
        return jsonify({"result": "error"})

    return jsonify({"result": "success"})


@bp_lms.route('/api/dtbl/mdl-deposit', methods=['GET'])
def get_mdl_deposit():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)
        store_records = StoreRecords.objects(branch=current_user.branch).filter(deposited="Pre Deposit")
        accommodations = Accommodation.objects(branch=current_user.branch).filter(deposited="Pre Deposit")
    elif current_user.role.name == "Admin":
        branch_id = request.args.get('branch')
        if branch_id != "all":
            clients = Registration.objects(status="registered").filter(branch=ObjectId(branch_id))
            store_records = StoreRecords.objects().filter(deposited="Pre Deposit").filter(branch=ObjectId(branch_id))
            accommodations = Accommodation.objects().filter(deposited="Pre Deposit").filter(branch=ObjectId(branch_id))
        else:
            clients = Registration.objects(status="registered")
            store_records = StoreRecords.objects().filter(deposited="Pre Deposit").filter(branch=current_user.branch)
            accommodations = Accommodation.objects().filter(deposited="Pre Deposit").filter(branch=current_user.branch)
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
        store_records = StoreRecords.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")
        accommodations = Accommodation.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")
    else:
        return jsonify({'data': []})

    _data = []
    deposit_amount = 0

    for client in clients:
        if client.amount != client.amount_deposit:
            student_payments = mongo.db.lms_registration_payments.find({"payment_by": ObjectId(client.id)})

            for payment in student_payments:
                payment_deposited = payment.get('deposited')
                if payment_deposited == "Pre Deposit":
                    if type(payment['date']) == datetime:
                        local_datetime = payment['date'].replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
                    elif type(payment['date'] == str):
                        to_date = datetime.strptime(payment['date'], "%Y-%m-%d")
                        local_datetime = to_date.strftime("%B %d, %Y")
                    else: 
                        local_datetime = ''
                        
                    _data.append([
                        str(client.full_registration_number),
                        "Student Payment",
                        client.lname,
                        client.fname,
                        client.mname,
                        client.suffix,
                        str(payment['amount']),
                        local_datetime
                    ])

                    deposit_amount += payment['amount'].to_decimal()

    record : StoreRecords
    for record in store_records:
        _data.append([
            str(record.client_id.full_registration_number),
            "Buy Item",
            record.client_id.lname,
            record.client_id.fname,
            record.client_id.mname,
            record.client_id.suffix,
            str(record.total_amount),
            record.created_at_local
        ])
        deposit_amount += decimal.Decimal(record.total_amount)

    record : Accommodation
    for record in accommodations:
        _data.append([
            str(record.client_id.full_registration_number),
            "Accommodation",
            record.client_id.lname,
            record.client_id.fname,
            record.client_id.mname,
            record.client_id.suffix,
            str(record.total_amount),
            record.created_at_local
        ])
        deposit_amount += decimal.Decimal(record.total_amount)


    response = {
        'data': _data,
        'deposit_amount': str(deposit_amount)
        }

    return jsonify(response)


@bp_lms.route('/api/get-partners-percent', methods=['GET'])
def get_partners_percent():
    branch = request.args.get('branch')

    if branch == '':
        return jsonify({"data": []})

    partners = User.objects(branches__in=[branch]).filter(role=PARTNERREFERENCE)

    if len(partners) == 0:
        return jsonify({"data": []})

    data = []

    for partner in partners:
        data.append((
            str(partner.id),
            partner.full_name,
            ''
        ))

    response = jsonify({'data': data})

    return response



@bp_lms.route('/api/cash-flow/<string:cash_flow_id>', methods=['GET'])
def get_cash_flow_by_id(cash_flow_id):
    bank_statement = CashFlow.objects.get_or_404(id=cash_flow_id)
    payments = []
    for payment in bank_statement.payments:
        if type(payment.date) == datetime:
            local_datetime = payment.date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(payment.date == str):
            to_date = datetime.strptime(payment.date, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''
        payment_by = Registration.objects(id=payment.payment_by.id).get()
        payment_main = mongo.db.lms_registration_payments.find_one({"_id": ObjectId(payment.id)})

        payments.append({
            'payment_id': str(payment.id),
            'date': local_datetime,
            'payment_by': payment_by.full_name,
            'amount': str(payment.amount),
            'payment_mode': payment.payment_mode,
            'thru': payment.thru,
            'reference_no': payment.reference_no,
            'receipt_path': payment_main.get('receipt_path', '') 
        })

    data = {
        'id': str(bank_statement.id),
        'payments': payments,
    }

    response = {
        'data': data
        }

    return jsonify(response)


@bp_lms.route("/upload-receipt", methods=["POST"])
def upload_receipt():
    file = request.files['receipt_file']
    payment_id = request.form['receipt_payment_id']
    print(payment_id)

    # check whether a file is selected
    if file.filename == '':
        response = {
            'status': "error",
            'message': "No selected file"
        }
        return jsonify(response), 400

    # check whether the file extension is allowed (eg. png,jpeg,jpg,gif)
    if not (file and allowed_file(file.filename)):
        response = {
            'status': "error",
            'message': "File is not allowed"
        }
        return jsonify(response), 400

    output = upload_file(file, file.filename)
    print(output)
    response = {'status': None, 'message': None}
    if output:
        mongo.db.lms_registration_payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {
                "receipt_path": output
            }
        })
        response['status'] = "success"
        response['message'] = "Receipt uploaded successfully!"
        code = 200
    else:
        response['status'] = "error"
        response['message'] = "Error occured, please contact system administrator"
        code = 400
    return jsonify(response), code
