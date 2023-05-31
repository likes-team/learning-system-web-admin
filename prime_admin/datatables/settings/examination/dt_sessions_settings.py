from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms



@bp_lms.route('/datatables/settings/examination/sessions')
def fetch_sessions_settings_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    query = mongo.db.lms_examination_sessions.find().skip(start).limit(length)
    table_data = []

    for row in query:
        table_data.append([
            str(row["_id"]),
            row["description"],
            ''
        ])

    response = {
        'draw': draw,
        'recordsTotal': query.count(),
        'recordsFiltered': query.count(),
        'data': table_data,
    }
    return jsonify(response)