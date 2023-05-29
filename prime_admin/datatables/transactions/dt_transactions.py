import pymongo
from flask import request, jsonify
from flask_login import current_user
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import convert_utc_to_local



@bp_lms.route('/datatables/transactions')
def fetch_transactions_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))

    query = list(mongo.db.lms_fund_wallet_transactions.aggregate([
        {"$match": {
            'type': 'expenses',
            'category': 'rebates',
            'description': str(current_user.id),
        }},
        {'$lookup': {
            'from': 'lms_branches',
            'localField': 'branch',
            'foreignField': '_id',
            'as': 'branch'
        }},
        {"$unwind": {
            'path': '$branch'
        }},
        {"$skip": start},
        {"$limit": length},
        {"$sort": {
            'created_at': pymongo.DESCENDING
        }}
    ]))

    filtered_records = len(query)
    total_records = len(list(mongo.db.lms_fund_wallet_transactions.aggregate([
        {"$match": {
            'type': 'expenses',
            'category': 'rebates',
            'description': current_user.id,
        }},
        {"$sort": {
            'created_at': pymongo.DESCENDING
        }}
    ])))
    data = []

    for record in query:
        data.append([
            str(record['_id']),
            convert_utc_to_local(record['date']),
            record.get('branch', {}).get('name', ''),
            record.get('remittance', ''),
            record.get('reference_no'),
            record.get('sender'),
            record.get('contact_no'),
            record.get('address'),
            str(record['total_amount_due']),
            record.get('status', '').upper(),
        ])
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': data
    }
    return jsonify(response)
