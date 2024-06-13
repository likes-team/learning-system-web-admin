import pytz
import pymongo
import decimal
from bson.objectid import ObjectId
from datetime import datetime
from config import TIMEZONE
from flask import jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin.globals import convert_to_utc
from prime_admin import bp_lms
from prime_admin.globals import D128_CTX, convert_to_utc



@bp_lms.route('/datatables/fund-wallet/office-supplies', methods=['GET'])
def fetch_office_supply_dt():
    print("request.args", request.args)
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    description = request.args.get('description', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    branch_id = request.args.get('branch', 'all')

    total_records: int
    filtered_records: int
    filter: dict

    if branch_id == 'all':
        if current_user.role.name == "Admin":
            filter = {'category': 'office_supply'}
        elif current_user.role.name == "Partner":
            filter = {'category': 'office_supply', 'branch': {"$in": current_user.branches}}
        elif current_user.role.name == "Secretary":
            filter = {'category': 'office_supply' ,'branch': current_user.branch.id}
        elif current_user.role.name == "Manager":
            filter = {'category': 'office_supply', 'branch': {"$in": current_user.branches}}
    else:
        if current_user.role.name == "Secretary":
            filter = {'category': 'office_supply', 'branch': current_user.branch.id}
        elif current_user.role.name == "Admin":
            filter = {'category': 'office_supply', 'branch': ObjectId(branch_id)}
        elif current_user.role.name == "Partner":
            filter = {'category': 'office_supply', 'branch': ObjectId(branch_id)}
        elif current_user.role.name == "Manager":
            filter = {'category': 'office_supply', 'branch': ObjectId(branch_id)}

    if description != "":
        filter['description'] = description

    if date_from != "":
        filter['date'] = {"$gt": convert_to_utc(date_from, 'date_from')}
    
    if date_to != "":
        if 'date' in filter:
            filter['date']['$lt'] = convert_to_utc(date_to, 'date_to')
        else:
            filter['date'] = {'$lt': convert_to_utc(date_to, 'date_to')}
      
    query = mongo.db.lms_fund_wallet_transactions.find(filter).sort('date', pymongo.DESCENDING).skip(start).limit(length)
    total_records = mongo.db.lms_fund_wallet_transactions.find(filter).count()
    filtered_records = query.count()
    
    table_data = []
    
    total_ofice_supply = decimal.Decimal(0)
    
    with decimal.localcontext(D128_CTX):
        for transaction in query:
            transaction_date: datetime = transaction.get('date', None)
            description = transaction.get('description', '')
            unit_price = transaction.get('unit_price', '')
            qty = transaction.get('qty', '')
            settled_by = transaction.get('settled_by', '')
            total_amount_due = transaction.get('total_amount_due', 0.00)
        
            if type(transaction_date == datetime):
                local_datetime = transaction_date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
            elif type(transaction_date == str):
                to_date = datetime.strptime(transaction_date, "%Y-%m-%d")
                local_datetime = to_date.strftime("%B %d, %Y")
            else: 
                local_datetime = ''
                
            total_ofice_supply = total_ofice_supply + total_amount_due.to_decimal()

            table_data.append([
                local_datetime,
                description,
                transaction.get('account_no', ''),
                unit_price,
                qty,
                str(total_amount_due),
                settled_by,
            ])

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
        'totalOfficeSupply': str(total_ofice_supply)
    }

    return jsonify(response)