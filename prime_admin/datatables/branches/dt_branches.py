import pymongo
from bson.objectid import ObjectId
from datetime import datetime
from flask import jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin.globals import convert_to_utc
from prime_admin import bp_lms
from prime_admin.utils.date import format_utc_to_local, format_date
from prime_admin.models_v2 import BranchV2



@bp_lms.route('/datatables/branches/branches', methods=['GET'])
def fetch_branches_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))

    query = list(mongo.db.lms_branches.aggregate([
        {'$sort': {
            'start_date': pymongo.DESCENDING
        }},
        {"$skip": start},
        {"$limit": length},
    ]))
    total_records = mongo.db.lms_branches.count()
    filtered_records = len(query)
    table_data = []
    
    for doc in query:
        branch = BranchV2(doc)
        table_data.append([
            str(branch.get_id()),
            branch.get_name(),
            branch.get_created_by(),
            branch.get_created_at(),
            branch.get_updated_by(),
            branch.get_updated_at(),
            'actions'
        ])
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)