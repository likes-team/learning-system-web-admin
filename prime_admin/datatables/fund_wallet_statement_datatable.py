import pytz
import pymongo
import decimal
from bson.objectid import ObjectId
from datetime import datetime
from config import TIMEZONE
from flask import jsonify, request
from flask_login import current_user
from app import mongo
from app.auth.models import User
from prime_admin.globals import convert_to_utc
from prime_admin import bp_lms
from prime_admin.models import Registration


@bp_lms.route('/branches/<string:branch_id>/fund-wallet-statements/dt', methods=['GET'])
def fetch_branch_fund_wallet_statements_dt(branch_id):
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    category = request.args.get('category', '')
    description = request.args.get('description', '')
    total_records: int
    filtered_records: int
    match = {}
    
    if branch_id == 'all':
        total_fund_wallet = 0.00

        if current_user.role.name == "Admin":
            pass
        elif current_user.role.name == "Manager":
            match = {'branch': {"$in": current_user.branches}}
        elif current_user.role.name == "Partner":
            match = {'branch': {"$in": current_user.branches}}
        elif current_user.role.name == "Secretary":
            match = {'branch': current_user.branch.id}
            accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id})
            total_fund_wallet = decimal.Decimal(str(accounting.get('total_fund_wallet', "0.00")))
    else:
        if current_user.role.name == "Admin":
            match = {'branch': ObjectId(branch_id)}
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})
        elif current_user.role.name == "Manager":
            match = {'branch': ObjectId(branch_id)}
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})            
        elif current_user.role.name == "Partner":
            match = {'branch': ObjectId(branch_id)}
            accounting = mongo.db.lms_accounting.find_one({"branch": ObjectId(branch_id)})            
        elif current_user.role.name == "Secretary":
            match = {'branch': current_user.branch.id}
            accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id})

        total_fund_wallet = decimal.Decimal(str(accounting.get('total_fund_wallet', "0.00")))

    if date_from != "":
        match['date'] = {"$gt": convert_to_utc(date_from, 'date_from')}
    
    if date_to != "":
        if 'date' in match:
            match['date']['$lt'] = convert_to_utc(date_to, 'date_to')
        else:
            match['date'] = {'$lt': convert_to_utc(date_to, 'date_to')}
    
    if category != "":
        match['category'] = category
        
    if description != "":
        match['description'] = description    
    
    statements_query =  mongo.db.lms_fund_wallet_transactions.find(match).sort('date', pymongo.DESCENDING).skip(start).limit(length)

    total_records = mongo.db.lms_fund_wallet_transactions.find(match).count()
    filtered_records = statements_query.count()

    table_data = []
    
    for statement in statements_query:
        transaction_id = statement.get('_id', None)
        date = statement.get('date', None)
        description = statement.get('description', '')
        category = statement.get('category', '')
        amount_received = statement.get('amount_received', 0.00)
        total_amount_due = statement.get('total_amount_due', 0.00)
        statement_type = statement.get('type', '')
        running_balance = decimal.Decimal(str(statement.get('running_balance', 0.00)))
        created_by = statement.get('created_by', 0.00)
        remarks = statement.get('remarks', '')
        is_deleted = statement.get('is_deleted', False)

        if type(date == datetime):
            local_datetime = date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(date == str):
            to_date = datetime.strptime(date, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''
        
        if category == "salary_and_rebates" \
            or category == "salary" \
                or category == "rebates" \
                    or category == "Bookeeper":
            contact_person : User = User.objects.get(id=description)
            description = contact_person.full_name
        
        if category == "office_supply":
            supplier = statement.get('account_no', '')
        elif category == "refund":
            student = Registration.objects.get(id=description)
            description = student.full_name
            supplier = ""
        else:
            supplier = ""

        table_data.append([
            str(transaction_id),
            local_datetime,
            category.upper(),
            description,
            supplier,
            str(amount_received) if statement_type == "add_fund" else '',
            str(total_amount_due) if statement_type == "expenses" else '',
            str(round(running_balance, 2)),
            created_by,
            remarks,
            is_deleted
        ])

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
        'totalFundWallet': str(total_fund_wallet)
    }

    return jsonify(response)