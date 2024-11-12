from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms
from prime_admin.models_v2 import OrganizationChartV2

@bp_lms.route('/datatables/pages/organization_chart', methods=['GET'])
def fetch_organization_chart():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))

    query = list(mongo.db.lms_organization_chart.aggregate([
        {"$skip": start},
        {"$limit": length},
    ]))
    total_records = mongo.db.lms_organization_chart.count()
    filtered_records = len(query)
    table_data = []
    
    for doc in query:
        organization_chart = OrganizationChartV2(doc)
        table_data.append([
            str(organization_chart.get_id()),
            organization_chart.get_name(),
            organization_chart.get_position(),
            organization_chart.get_branch(),
            organization_chart.get_is_active(),
            'actions'
        ])
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)
