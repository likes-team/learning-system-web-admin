import decimal
import pymongo
from bson.objectid import ObjectId
from bson import Decimal128
from flask_login import current_user
from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms
from prime_admin.globals import convert_to_utc



@bp_lms.route('/datatables/cash-flow/statement')
def fetch_fund_statement_dt():
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
            'data': []
        }
        return jsonify(response)

    if current_user.role.name == "Secretary":
        accounting = mongo.db.lms_accounting.find_one({'branch': ObjectId(current_user.branch.id)})
    else:
        accounting = mongo.db.lms_accounting.find_one({'branch': ObjectId(branch_id)})

    if from_what == "Fund 1":
        from_what = {'$in': ['Fund 1', 'Student Loan Payment']}
    elif from_what == "Fund 2":
        from_what = {'$in': ['Fund 2', 'Emergency Fund']}
    
    match = {'group': accounting['active_group'], 'from_what': from_what}

    if current_user.role.name == "Secretary":
        match['branch'] = current_user.branch.id
    else:
        match['branch'] = ObjectId(branch_id)

    if date_from != "":
        match['date_deposit'] = {"$gt": convert_to_utc(date_from, 'date_from')}
    if date_to != "":
        if 'date_deposit' in match:
            match['date_deposit']['$lt'] = convert_to_utc(date_to, 'date_to')
        else:
            match['date_deposit'] = {'$lt': convert_to_utc(date_to, 'date_to')}
    if transaction_type != "":
        match['type'] = transaction_type

    bank_statements = mongo.db.lms_bank_statements.find(match).sort('date_deposit', pymongo.DESCENDING).skip(start).limit(length)
    records_total = bank_statements.count()
    records_filtered = bank_statements.count()
    table_data = []
    
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
        balance = statement.get('balance', 0.00)
        _type = statement.get('type')

        if current_user.role.name == "Secretary":
            table_data.append((
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
            table_data.append((
                str(_id),
                date_deposit,
                '' if _type == 'withdraw' else str(amount),
                '' if _type == 'withdraw' else from_what,
                '' if _type == "deposit" else str(amount),
                str(balance) if balance is not None else '',
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
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': table_data
    }
    return jsonify(response)
