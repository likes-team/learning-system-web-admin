import pymongo
import decimal
from bson.objectid import ObjectId
from datetime import datetime
from flask import jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin.globals import D128_CTX, convert_to_utc
from prime_admin import bp_lms
from prime_admin.utils.date import format_utc_to_local



@bp_lms.route('/datatables/fund-wallet/utilities', methods=['GET'])
def fetch_utilities_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')
    description = request.args.get('description', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    match = {'category': 'utilities'}
    
    if branch_id == 'all':
        if current_user.role.name == "Admin":
            pass
        elif current_user.role.name == "Manager":
            match['branch'] = {"$in": current_user.branches}
        elif current_user.role.name == "Partner":
            match['branch'] = {"$in": current_user.branches}
        elif current_user.role.name == "Secretary":
            match['branch'] = current_user.branch.id
    else:
        if current_user.role.name == "Admin":
            match['branch'] = ObjectId(branch_id)
        elif current_user.role.name == "Manager":
            match['branch'] = ObjectId(branch_id)
        elif current_user.role.name == "Partner":
            match['branch'] = ObjectId(branch_id)
        elif current_user.role.name == "Secretary":
            match['branch'] = current_user.branch.id

    if description != "":
        match['description'] = description

    if date_from != "":
        match['date'] = {"$gt": convert_to_utc(date_from, 'date_from')}
    
    if date_to != "":
        if 'date' in match:
            match['date']['$lt'] = convert_to_utc(date_to, 'date_to')
        else:
            match['date'] = {'$lt': convert_to_utc(date_to, 'date_to')}
     
    query = mongo.db.lms_fund_wallet_transactions.find(match).sort('date', pymongo.DESCENDING).skip(start).limit(length)
    total_records = mongo.db.lms_fund_wallet_transactions.find(match).count()
    filtered_records = query.count()
    
    table_data = []
    
    total_utilities = decimal.Decimal(0)
    
    with decimal.localcontext(D128_CTX):
        for transaction in query:
            transaction_date: datetime = transaction.get('date', None)
            account_no = transaction.get('account_no', '')
            description = transaction.get('description', '')
            billing_month_from = transaction.get('billing_month_from', '')
            billing_month_to = transaction.get('billing_month_to', '')
            settled_by = transaction.get('settled_by', '')
            total_amount_due = transaction.get('total_amount_due', 0.00)

            billing_month = billing_month_from + " - " + billing_month_to
            total_utilities = total_utilities + total_amount_due.to_decimal()

            table_data.append([
                format_utc_to_local(transaction_date),
                description,
                account_no,
                billing_month,
                str(total_amount_due),
                settled_by,
            ])
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
        'totalUtilities': str(total_utilities)
    }
    return jsonify(response)