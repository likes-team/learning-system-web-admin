import pytz
import pymongo
import decimal
from bson import Decimal128
from bson.objectid import ObjectId
from datetime import datetime
from config import TIMEZONE
from flask import jsonify, request
from flask_login import login_required, current_user
from app import mongo
from app.auth.models import User
from app.admin.templating import admin_render_template
from prime_admin.globals import D128_CTX, get_date_now
from prime_admin import bp_lms
from prime_admin.models import Branch, FundWallet



@bp_lms.route('/fund-wallet')
@login_required
def fund_wallet():
    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    else:
        branches = Branch.objects

    return admin_render_template(
        FundWallet,
        "lms/fund_wallet.html",
        'learning_management',
        title="Fund Wallet",
        branches=branches
    )
    

@bp_lms.route('/branches/<string:branch_id>/fund-wallet-statements/dt', methods=['GET'])
def fetch_branch_fund_wallet_statements_dt(branch_id):
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    
    total_records: int
    filtered_records: int
    filter: dict
    
    if branch_id == 'all':
        total_fund_wallet = 0.00

        if current_user.role.name == "Admin":
            filter = {}
        elif current_user.role.name == "Partner":
            filter = {
                'branch': {"$in": current_user.branches}
            }
        elif current_user.role.name == "Secretary":
            filter = {'branch': current_user.branch.id}
    else:
        if current_user.role.name == "Secretary":
            filter = {'branch': current_user.branch.id}
            accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id})
        elif current_user.role.name == "Admin":
            filter = {'branch': ObjectId(branch_id)}
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
        elif current_user.role.name == "Partner":
            filter = {'branch': ObjectId(branch_id)}
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
            
        total_fund_wallet = accounting.get('total_fund_wallet', 0.00)

        total_fund_wallet = total_fund_wallet if 'total_fund_wallet' in accounting else '0.00' 

    statements_query =  mongo.db.lms_fund_wallet_transactions.find(filter).sort('date', pymongo.DESCENDING).skip(start).limit(length)

    total_records = mongo.db.lms_fund_wallet_transactions.find(filter).count()
    filtered_records = statements_query.count()

    table_data = []
    
    for statement in statements_query:
        date = statement.get('date', None)
        description = statement.get('description', '')
        category = statement.get('category', '')
        amount_received = statement.get('amount_received', 0.00)
        total_amount_due = statement.get('total_amount_due', 0.00)
        statement_type = statement.get('type', '')
        running_balance = statement.get('running_balance', 0.00)
        created_by = statement.get('created_by', 0.00)
        remarks = statement.get('remarks', 0.00)
        
        if type(date == datetime):
            local_datetime = date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(date == str):
            to_date = datetime.strptime(date, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''
        
        if category == "salary_and_rebates":
            contact_person : User = User.objects.get(id=description)
            description = contact_person.full_name
            
        table_data.append([
            local_datetime,
            description,
            str(amount_received) if statement_type == "add_fund" else '',
            str(total_amount_due) if statement_type == "expenses" else '',
            str(running_balance),
            created_by,
            remarks
        ])

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
        'totalFundWallet': str(total_fund_wallet)
    }

    return jsonify(response)


@bp_lms.route('/branches/<string:branch_id>/add-funds-transactions/dt', methods=['GET'])
def fetch_add_funds_transactions_dt(branch_id):
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))

    total_records: int
    filtered_records: int
    filter: dict

    if branch_id == 'all':
        total_fund_wallet = 0.00
        
        if current_user.role.name == "Admin":
            filter = {'type': 'add_fund'}
        elif current_user.role.name == "Partner":
            filter = {'type': 'add_fund', 'branch': {"$in": current_user.branches}}
        elif current_user.role.name == "Secretary":
            filter = {'branch': current_user.branch.id}
    else:
        if current_user.role.name == "Secretary":
            filter = {'type': 'add_fund', 'branch': current_user.branch.id}
            accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id})
        elif current_user.role.name == "Admin":
            filter = {'type': 'add_fund', 'branch': ObjectId(branch_id)}
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
        elif current_user.role.name == "Partner":
            filter = {'type': 'add_fund', 'branch': ObjectId(branch_id)}
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
        total_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else '0.00'

    query = mongo.db.lms_fund_wallet_transactions.find(filter).sort('date', pymongo.DESCENDING).skip(start).limit(length)
    total_records = mongo.db.lms_fund_wallet_transactions.find(filter).count()
    filtered_records = query.count()
    
    table_data = []
    
    for transaction in query:
        date = transaction.get('date', None)
        thru = transaction.get('thru', '')
        remittance = transaction.get('remittance', '')
        account_name = transaction.get('account_name', '')
        account_no = transaction.get('account_no', '')
        bank_name = transaction.get('bank_name', '')
        transaction_no = transaction.get('transaction_no', '')
        sender = transaction.get('sender', '')
        receiver = transaction.get('receiver', '')
        amount_received = transaction.get('amount_received', 0.00)
        remarks = transaction.get('remarks', 0.00)
        
        if type(date == datetime):
            local_datetime = date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(date == str):
            to_date = datetime.strptime(date, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''

        table_data.append([
            local_datetime,
            thru,
            bank_name,
            account_name,
            account_no,
            remittance,
            transaction_no,
            sender,
            receiver,
            str(amount_received),
            remarks,
        ])

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
        'totalFundWallet': str(total_fund_wallet)
    }

    return jsonify(response)


@bp_lms.route('/branches/<string:branch_id>/expenses-transactions/dt', methods=['GET'])
def fetch_expenses_transactions_dt(branch_id):
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))

    total_records: int
    filtered_records: int
    filter: dict
    
    if branch_id == 'all':
        if current_user.role.name == "Admin":
            filter = {'type': 'expenses'}
        elif current_user.role.name == "Partner":
            filter = {'type': 'expenses', 'branch': {"$in": current_user.branches}}
        elif current_user.role.name == "Secretary":
            filter = {'branch': current_user.branch.id}
    else:
        if current_user.role.name == "Secretary":
            filter = {'type': 'expenses', 'branch': current_user.branch.id}
        elif current_user.role.name == "Admin":
            filter = {'type': 'expenses', 'branch': ObjectId(branch_id)}
        elif current_user.role.name == "Partner":
            filter = {'type': 'expenses', 'branch': ObjectId(branch_id)}
            
    query = mongo.db.lms_fund_wallet_transactions.find(filter).sort('date', pymongo.DESCENDING).skip(start).limit(length)
    total_records = mongo.db.lms_fund_wallet_transactions.find(filter).count()
    filtered_records = query.count()
    
    table_data = []
    total_utilities = decimal.Decimal(0)
    total_office_supplies = decimal.Decimal(0)
    total_salaries_and_rebates = decimal.Decimal(0)
    total_other_expenses = decimal.Decimal(0)
    
    with decimal.localcontext(D128_CTX):
        for transaction in query:
            try:
                date = transaction.get('date', None)
                description = transaction.get('description', '')
                category = transaction.get('category', '')
                account_no = transaction.get('account_no', '')
                unit_price = transaction.get('unit_price', '')
                qty = transaction.get('qty', 0)
                billing_month_from = transaction.get('billing_month_from', '')
                billing_month_to = transaction.get('billing_month_to', '')
                settled_by = transaction.get('settled_by', '')
                total_amount_due = transaction.get('total_amount_due', 0.00)
                remarks = transaction.get('remarks', 0.00)
                
                if type(date == datetime):
                    local_datetime = date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
                elif type(date == str):
                    to_date = datetime.strptime(date, "%Y-%m-%d")
                    local_datetime = to_date.strftime("%B %d, %Y")
                else:
                    local_datetime = ''

                if category == "utilities":
                    total_utilities = total_utilities + total_amount_due.to_decimal()
                elif category == "office_supply":
                    total_office_supplies = total_office_supplies + total_amount_due.to_decimal()
                elif category == "salary_and_rebates":
                    total_salaries_and_rebates = total_salaries_and_rebates + total_amount_due.to_decimal()
                    contact_person : User = User.objects.get(id=description)
                    description = contact_person.full_name
                elif category == "other_expenses":
                    total_other_expenses = total_other_expenses + total_amount_due.to_decimal()

                table_data.append([
                    local_datetime,
                    category,
                    description,
                    account_no,
                    str(unit_price),
                    str(qty),
                    str(billing_month_from if billing_month_from is not None else '') + " - " + str(billing_month_to if billing_month_to is not None else ''),
                    settled_by,
                    str(total_amount_due),
                    remarks,
                ])
            except Exception as e:
                print(str(e))
                continue

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
        'totalUtilities': str(total_utilities),
        'totalOfficeSupplies': str(total_office_supplies),
        'totalSalariesAndRebates': str(total_salaries_and_rebates),
        'totalOtherExpenses': str(total_other_expenses)
        }

    return jsonify(response)


@bp_lms.route('/fund-wallet/add-fund', methods=['POST'])
@login_required
def fund_wallet_add_fund():
    form = request.form
    
    try:
        branch_id = form.get('branch')
        thru = form.get('thru', '')
        bank_name = form.get('bank', '')
        remittance = form.get('remittance', '')
        account_name = form.get('account_name', '')
        account_no = form.get('account_no', '')
        transaction_no = form.get('transaction_no', '')
        amount_received = format(float(form.get('amount_received')), '.2f')
        sender = form.get('sender', '')
        receiver = form.get('receiver', '')
        remarks = form.get('remarks')
        
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                accounting = mongo.db.lms_accounting.find_one({
                    "branch": ObjectId(branch_id),
                })

                if accounting:
                    with decimal.localcontext(D128_CTX):
                        previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')
                        new_total_fund_wallet = previous_fund_wallet.to_decimal() + decimal.Decimal(amount_received)
                        balance = Decimal128(Decimal128(
                            str(accounting["total_fund_wallet"] if 'total_fund_wallet' in accounting else 0.00)).to_decimal() + Decimal128(str(amount_received)).to_decimal())
                        
                        print("amount_received: ", amount_received)
                        print("previous_fund_wallet: ", previous_fund_wallet)
                        print("new_total_fund_wallet: ", new_total_fund_wallet)
                        print("balance: ", balance)                        
                        
                        mongo.db.lms_accounting.update_one({
                            "branch": ObjectId(branch_id)
                        },
                        {'$set': {
                            "total_fund_wallet": Decimal128(new_total_fund_wallet)
                        }},session=session)
                else:
                    previous_fund_wallet = Decimal128('0.00')
                    new_total_fund_wallet = decimal.Decimal(amount_received)
                    balance = Decimal128(str(amount_received))

                    mongo.db.lms_accounting.insert_one({
                        "_id": ObjectId(),
                        "branch": ObjectId(branch_id),
                        "active_group": 1,
                        "total_gross_sale": Decimal128("0.00"),
                        "final_fund1": Decimal128("0.00"),
                        "final_fund2": Decimal128("0.00"),
                        "total_fund_wallet": Decimal128(str(amount_received))
                    }, session=session)

                mongo.db.lms_fund_wallet_transactions.insert_one({
                    'type': 'add_fund',
                    'thru': thru,
                    'remittance': remittance,
                    'account_name': account_name,
                    'account_no': account_no,
                    'running_balance': balance,
                    'branch': ObjectId(branch_id),
                    'date': get_date_now(),
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
                
        response = {
            'status': 'success',
            'message': "Fund added successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_lms.route('/fund-wallet/add-expenses', methods=['POST'])
@login_required
def fund_wallet_add_expenses():
    form = request.form

    try:
        category = form.get('category', '')
        description = form.get('description', '')
        account_no = form.get('account_no', None)
        billing_month_from = form.get('billing_month_from', None)
        billing_month_to = form.get('billing_month_to', None)
        qty = form.get('qty', None)
        unit_price = format(float(form.get('unit_price', '0.00')), '.2f')
        settled_by = form.get('settled_by', '')
        total_amount_due = format(float(form.get('total_amount_due', '0.00')), '.2f')
        remarks = form.get('remarks', '')
        branch_id = form.get('branch', None)
        
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                accounting = mongo.db.lms_accounting.find_one({
                    "branch": ObjectId(branch_id),
                })

                if accounting:
                    with decimal.localcontext(D128_CTX):
                        previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')
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

                mongo.db.lms_fund_wallet_transactions.insert_one({
                    'type': 'expenses',
                    'running_balance': balance,
                    'branch': ObjectId(branch_id),
                    'date': get_date_now(),
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
        response = {
            'status': 'success',
            'message': "Expenses added successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500
