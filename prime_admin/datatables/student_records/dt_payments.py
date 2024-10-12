import pymongo
from bson import ObjectId
from mongoengine.queryset.visitor import Q
from flask import abort, jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import format_utc_to_local
from prime_admin.utils.currency import format_to_str_php
from prime_admin.utils.date import convert_date_input_to_utc


@bp_lms.route('/datatables/student-records/payments')
def fetch_payments_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch = request.args.get('branch')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_value = request.args.get("search[value]")
    match = {}

    if search_value and search_value != '':
        match['student.lname'] = {'$regex': search_value, '$options' : 'i'}

    if branch and branch != 'all':
        match['branch'] = ObjectId(branch)
    else:
        if current_user.role.name in ["Marketer", 'Partner', 'Manager']:
            match['branch'] = {'$in': [ObjectId(branch) for branch in current_user.branches]}

    if date_from and date_from != "":
        match['date'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from')}
    
    if date_to and date_to != '':
        match['date'] = {'$lte': convert_date_input_to_utc(date_to, 'date_to')}

    if date_from and date_from != '' and date_to and date_to != '':
        match['date'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from'), '$lte': convert_date_input_to_utc(date_to, 'date_to')}

    aggregate_query = list(mongo.db.lms_registration_payments.aggregate([
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
        {'$match': match},
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
        table_data.append([
            format_utc_to_local(doc.get('date')),
            (doc['student']['fname'] + ' ' + doc['student']['lname']).upper(),
            str(doc['branch_obj']['name']),
            format_to_str_php(doc.get('amount')),
            doc.get('payment_mode', '').upper()
        ])
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }
    return jsonify(response)
