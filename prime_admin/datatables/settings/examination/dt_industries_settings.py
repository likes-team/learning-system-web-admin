from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms



@bp_lms.route('/datatables/settings/examination/industries')
def fetch_industries_settings_dt():
    industries = mongo.db.lms_configurations.find_one({'name': 'industries'})['values']
    table_data = []

    print(industries)
    for industry in industries:
        table_data.append([
            industry,
            ''
        ])

    response = {
        'data': table_data,
    }
    return jsonify(response)