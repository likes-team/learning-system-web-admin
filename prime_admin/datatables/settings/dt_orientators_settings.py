from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms



@bp_lms.route('/datatables/settings/orientators')
def datatables_settings_orientators():
    orientators = mongo.db.lms_orientators.find()
    table_data = []

    for orientator in orientators:
        table_data.append([
            str(orientator['_id']),
            orientator['fname'],
            orientator.get('is_active', False),
            ''
        ])

    response = {
        'data': table_data,
    }
    return jsonify(response)