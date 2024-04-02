from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms



@bp_lms.route('/datatables/settings/examination/venues')
def fetch_venues_settings_dt():
    venues = mongo.db.lms_configurations.find_one({'name': 'exam_venues'})['values']
    table_data = []

    for venue in venues:
        table_data.append([
            venue,
            ''
        ])

    response = {
        'data': table_data,
    }
    return jsonify(response)
