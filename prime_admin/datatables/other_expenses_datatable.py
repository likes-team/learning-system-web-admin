from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms



@bp_lms.route('/dtbl/other-expenses-settings')
def fetch_dtbl_other_expenses_settings():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    query = mongo.db.lms_other_expenses_items.find().skip(start).limit(length)

    _table_data = []

    for row in query:
        _table_data.append([
            str(row["_id"]),
            row["description"],
            ''
        ])

    response = {
        'draw': draw,
        'recordsTotal': query.count(),
        'recordsFiltered': query.count(),
        'data': _table_data,
    }

    return jsonify(response)