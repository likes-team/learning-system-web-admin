import pymongo
from bson import ObjectId
from mongoengine.queryset.visitor import Q
from flask import abort, jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import format_utc_to_local
from prime_admin.utils.currency import format_to_str_php



@bp_lms.route('/datatables/student-records/payments')
def fetch_payments_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    match = {}

    if current_user.role.name == "Admin":
        pass
    elif current_user.role.name == "Manager":
        match['branch'] = {"$in": [ObjectId(branch_id) for branch_id in current_user.branches]}
    elif current_user.role.name == "Partner":
        match['branch'] = {"$in": [ObjectId(branch_id) for branch_id in current_user.branches]}
    elif current_user.role.name == "Secretary":
        match['branch'] = current_user.branch.id
        
    aggregate_query = list(mongo.db.lms_registration_payments.aggregate([
        {'$match': match},
        {'$lookup': {
            'from': 'lms_registrations',
            'localField': 'payment_by',
            'foreignField': '_id',
            'as': 'student'
        }},
        {'$lookup': {
            'from': 'lms_branches',
            'localField': 'branch',
            'foreignField': '_id',
            'as': 'branch_obj'
        }},
        {'$unwind': {
            'path': '$student'
        }},
        {'$unwind': {
            'path': '$branch_obj'
        }},
        {"$sort": {
            'date': pymongo.DESCENDING
        }},
        {"$skip": start},
        {"$limit": length},

    ]))

    total_records = mongo.db.lms_registration_payments.find(match).count()
    filtered_records = len(aggregate_query)
    table_data = []
    
    for doc in aggregate_query:
        print(str(doc.get('date')))
        table_data.append([
            format_utc_to_local(doc.get('date')),
            str(doc['student']['fname']),
            str(doc['branch_obj']['name']),
            format_to_str_php(doc.get('amount')),
            doc.get('payment_mode', '').upper()
        ])
        print(table_data)
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }
    return jsonify(response)
