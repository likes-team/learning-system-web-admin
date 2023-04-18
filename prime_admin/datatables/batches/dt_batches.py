import pymongo
from bson.objectid import ObjectId
from datetime import datetime
from flask import jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin.globals import convert_to_utc
from prime_admin import bp_lms
from prime_admin.utils.date import format_utc_to_local, format_date
from prime_admin.models_v2 import BatchV2



@bp_lms.route('/datatables/batches/batches', methods=['GET'])
def fetch_batches_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')
    
    if branch_id == 'all':
        if current_user.role.name == "Admin":
            match = {}
        elif current_user.role.name == "Partner":
            match = {'branch': {"$in": current_user.branches}}
        elif current_user.role.name == "Secretary":
            match = {'branch': current_user.branch.id}
    else:
        if current_user.role.name == "Secretary":
            match = {'branch': current_user.branch.id}
        elif current_user.role.name == "Admin":
            match = {'branch': ObjectId(branch_id)}
        elif current_user.role.name == "Partner":
            match = {'branch': ObjectId(branch_id)}

    query = list(mongo.db.lms_batches.aggregate([
        {'$match': match},
        {'$lookup': {
            'from': 'lms_branches',
            'localField': 'branch',
            'foreignField': '_id',
            'as': 'branch'
        }},
        {'$unwind': {
            'path': '$branch'
        }},
        {'$sort': {
            'start_date': pymongo.DESCENDING
        }},
        {"$skip": start},
        {"$limit": length},
    ]))
    total_records = mongo.db.lms_batches.find(match).count()
    filtered_records = len(query)
    table_data = []
    
    for doc in query:
        batch = BatchV2(doc)
        table_data.append([
            str(batch.get_id()),
            batch.document['active'],
            batch.get_no(),
            batch.branch.get_name(),
            format_date(batch.get_start_date()),
            batch.document.get('created_by', ''),
            batch.document.get('update_by', ''),
            'actions'
        ])
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)