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
from prime_admin.models import Accounting, Branch, CashFlow, OrientationAttendance, Registration, Batch, Orientator
from flask import jsonify, request
from datetime import date, datetime
from mongoengine.queryset.visitor import Q
from bson import Decimal128
from app import mongo



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
    else:
        branches = Branch.objects

    orientators = Orientator.objects()

    # scripts = [
    #     {'lms.static': 'js/cash_flow.js'},
    # ]

    modals = [
        'lms/deposit_modal.html',
        'lms/withdraw_modal.html',
        'lms/profit_modal.html',
        'lms/pre_deposit_modal.html',
        'lms/cash_flow_view_modal.html',
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
        # scripts=scripts,
        modals=modals,
        branches=branches,
        orientators=orientators
        )


@bp_lms.route('/deposit', methods=['POST'])
@login_required
def deposit():
    form = DepositForm()
    
    try:
        new_deposit = CashFlow()
        new_deposit.date_deposit = convert_to_utc(str(form.date_deposit.data), "date_to")
        new_deposit.bank_name = form.bank_name.data
        new_deposit.account_no = form.account_no.data
        new_deposit.account_name = form.account_name.data
        new_deposit.amount = form.amount.data
        new_deposit.from_what = form.from_what.data
        new_deposit.by_who = form.by_who.data
        new_deposit.created_by = "{} {}".format(current_user.fname,current_user.lname)
        new_deposit.branch = current_user.branch
        new_deposit.type = "deposit"
        new_deposit.remarks = form.remarks.data
        new_deposit.set_created_at()

        payments = []

        with mongo.cx.start_session() as session:
            with session.start_transaction():
                with decimal.localcontext(D128_CTX):
                    accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id}, session=session)

                    if accounting:
                        new_deposit.group = accounting['active_group']

                        if form.from_what.data == "Sales":
                            new_deposit.balance = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() + Decimal128(str(new_deposit.amount)).to_decimal())
                            accounting["total_gross_sale"] = Decimal128(Decimal128(str(accounting["total_gross_sale"])).to_decimal() + Decimal128(str(new_deposit.amount)).to_decimal())

                            clients = mongo.db.lms_registrations.find({
                                "status": "registered",
                                "branch": current_user.branch.id
                                }, session=session)

                            for client in clients:
                                has_payment_updated = False

                                for payment in client['payments']:
                                    if "deposited" in payment and payment["deposited"] == "Pre Deposit":
                                        mongo.db.lms_registrations.update_one({
                                            "_id": client['_id'],
                                            "payments._id": payment['_id'],
                                        },
                                        {"$set": {
                                            "payments.$.deposited": "Yes"
                                        }},session=session)

                                        if 'amount_deposit' in client:
                                            client['amount_deposit'] = Decimal128(Decimal128(str(client['amount_deposit'])).to_decimal() + Decimal128(str(payment['amount'])).to_decimal())
                                        else:
                                            client['amount_deposit'] = payment['amount']
                                        print("Payment updated", client['amount_deposit'])

                                        has_payment_updated = True
                                        payments.append(payment)

                                if has_payment_updated:
                                    print(str(client["_id"]))
                                    mongo.db.lms_registrations.update_one(
                                        {"_id": client["_id"]},
                                        {"$set": {
                                            "amount_deposit": client['amount_deposit']
                                        }}, session=session)

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

                        elif new_deposit.from_what == "Emergency Fund":
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
                        accounting.branch = current_user.branch
                        accounting.active_group = 1
                        
                        if new_deposit.from_what == "Sales":
                            accounting.total_gross_sale = new_deposit.amount

                            clients = mongo.db.lms_registrations.find({"status": "registered", "branch": current_user.branch.id}, session=session)

                            for client in clients:
                                has_payment_updated = False

                                for payment in client['payments']:
                                    if "deposited" in payment and payment["deposited"] == "Pre Deposit":
                                        if 'amount_deposit' in client:
                                            client['amount_deposit'] = Decimal128(Decimal128(str(client['amount_deposit'])).to_decimal() + Decimal128(str(payment['amount'])).to_decimal())
                                        else:
                                            client['amount_deposit'] = payment['amount']

                                        print("Payment updated", client['amount_deposit'])
                                        has_payment_updated = True
                                        payments.append(payment)

                                        mongo.db.lms_registrations.update_one(
                                            {"_id": client['_id'], "payments._id": payment["_id"]},
                                            {"$set": {"payments.$.deposited": "Yes"}},
                                            session=session)

                                if has_payment_updated:
                                    print(str(client["_id"]))
                                    mongo.db.lms_registrations.update_one(
                                        {"_id": client["_id"]},
                                        {"$set": {
                                            "amount_deposit": client['amount_deposit']
                                        }}, session=session)

                        elif new_deposit.from_what == "Student Loan Payment":
                            accounting.final_fund1 = new_deposit.amount
                        elif new_deposit.from_what == "Emergency Fund":
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

        flash('Deposit Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.cash_flow'))


@bp_lms.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    form = WithdrawForm()
    
    try:
        new_withdraw = CashFlow()
        new_withdraw.date_deposit = convert_to_utc(str(form.date_deposit.data), "date_from")
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
                    "by_who": new_withdraw.by_who,
                    "created_by": new_withdraw.created_by,
                    "branch": new_withdraw.branch.id,
                    "type": new_withdraw.type,
                    "remarks": new_withdraw.remarks,
                    "balance": Decimal128(str(new_withdraw.balance)),
                    "group": new_withdraw.group,
                    "created_at": new_withdraw.created_at,
                }, session=session)

        flash('Withdraw Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.cash_flow'))


@bp_lms.route('/dtbl/get-cash-flow')
def get_cash_flow():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    # search_value = "%" + request.args.get("search[value]") + "%"
    # column_order = request.args.get('column_order')
    branch_id = request.args.get('branch')
    from_what = request.args.get('from_what')

    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'totalGrossSales': 0.00,
            'remaining': 0.00,
            'net': 0.00,
            'fund1': 0.00,
            'fund2': 0.00,
            'finalFund1': 0.00,
            'finalFund2': 0.00
        }

        return jsonify(response)
        # bank_statements = CashFlow.objects.skip(start).limit(length)
        
    if current_user.role.name == "Secretary":
        accounting = Accounting.objects(branch=current_user.branch.id).first()
    else:
        accounting = Accounting.objects(branch=branch_id).first()

    if accounting:
        total_gross_sales = accounting.total_gross_sale
        remaining = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.05)
        net = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.55)
        fund1 = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.20)
        fund2 = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.20)
        final_fund1 = accounting.final_fund1 if accounting.final_fund1 is not None else 0.00
        final_fund2 = accounting.final_fund2 if accounting.final_fund2 is not None else 0.00

        if current_user.role.name == "Secretary":
            if from_what == "sales":
                bank_statements = CashFlow.objects(branch=current_user.branch.id).filter(group=accounting.active_group).filter(from_what="Sales").skip(start).limit(length)
            else: # fund
                bank_statements = CashFlow.objects(branch=current_user.branch.id).filter(group=accounting.active_group).filter(from_what__ne="Sales").skip(start).limit(length)
        else:
            if from_what == "sales":
                bank_statements = CashFlow.objects(branch=branch_id).filter(group=accounting.active_group).filter(from_what="Sales").skip(start).limit(length)
            else: # fund
                bank_statements = CashFlow.objects(branch=branch_id).filter(group=accounting.active_group).filter(from_what__ne="Sales").skip(start).limit(length)
        recordsTotal = bank_statements.count(),
        recordsFiltered = bank_statements.count(),
    else:
        total_gross_sales = 0.00
        remaining = 0.00
        net = 0.00
        fund1 = 0.00
        fund2 = 0.00
        final_fund1 = 0.00
        final_fund2 = 0.00
        recordsTotal = 0,
        recordsFiltered = 0,
        bank_statements = []

    _table_data = []

    if current_user.role.name == "Secretary":
        for statement in bank_statements:
            _table_data.append((
                str(statement.id),
                statement.date_deposit,
                statement.bank_name,
                statement.account_no,
                statement.account_name,
                str(statement.amount),
                statement.from_what,
                statement.by_who,
                statement.remarks,
                statement.group,
                ''
            ))
    else:
        for statement in bank_statements:
            _table_data.append((
                str(statement.id),
                statement.date_deposit,
                '' if statement.type == 'withdraw' else str(statement.amount),
                '' if statement.type == 'withdraw' else statement.from_what,
                '' if statement.type == "deposit" else str(statement.amount),
                str(statement.balance) if statement.balance is not None else '',
                '' if statement.type == "deposit" else statement.from_what,
                statement.by_who,
                statement.remarks,
                statement.group,
                ''
            ))

    response = {
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': _table_data,
        'totalGrossSales': str(total_gross_sales),
        'remaining': str(remaining),
        'net': str(net),
        'fund1': str(fund1),
        'fund2': str(fund2),
        'finalFund1': str(final_fund1),
        'finalFund2': str(final_fund2)
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


@bp_lms.route('/api/dtbl/mdl-deposit', methods=['GET'])
def get_mdl_deposit():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(status="registered")
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
    else:
        return jsonify({'data': []})

    _data = []
    deposit_amount = 0

    for client in clients:
        if client.amount != client.amount_deposit:
            for payment in client.payments:
                if payment.deposited == "Pre Deposit":
                    if type(payment.date) == datetime:
                        local_datetime = payment.date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
                    elif type(payment.date == str):
                        to_date = datetime.strptime(payment.date, "%Y-%m-%d")
                        local_datetime = to_date.strftime("%B %d, %Y")
                    else: 
                        local_datetime = ''
                    
                    _data.append([
                        str(client.full_registration_number),
                        client.lname,
                        client.fname,
                        client.mname,
                        client.suffix,
                        str(payment.amount),
                        local_datetime
                        # str(payment['current_balance']),
                        # str(payment['deposited']) if 'deposit' in payment else 'No'
                    ])

                    deposit_amount += decimal.Decimal(payment.amount)

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
        
        print("TESTETS",payment.payment_by)
        payment_by = Registration.objects(id=payment.payment_by.id).get()

        payments.append({
            'date': local_datetime,
            'payment_by': payment_by.full_name,
            'amount': str(payment.amount),
            'payment_mode': payment.payment_mode,
        })

    data = {
        'id': str(bank_statement.id),
        'payments': payments,
    }

    response = {
        'data': data
        }

    return jsonify(response)
