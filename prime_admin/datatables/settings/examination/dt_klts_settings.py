from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms



@bp_lms.route('/datatables/settings/examination/klts')
def datatables_settings_klts():
    query = mongo.db.lms_klts.find()
    table_data = []

    for row in query:
        table_data.append([
            str(row["_id"]),
            row["description"],
            ''
        ])

    response = {
        'data': table_data,
    }
    return jsonify(response)