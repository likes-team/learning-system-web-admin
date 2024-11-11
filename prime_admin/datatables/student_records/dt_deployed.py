import pymongo
from bson import ObjectId
from mongoengine.queryset.visitor import Q
from flask import abort, jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin import bp_lms
from prime_admin.models import Registration, Student
from prime_admin.models_v2 import StudentV2
from prime_admin.utils.date import format_utc_to_local



@bp_lms.route('/datatables/student-records/deployed')
def datatables_student_records_deployed():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    match = {'is_deployed': True}
    
    if current_user.role.name == "Admin":
        pass
    elif current_user.role.name == "Manager":
        match['branch'] = {"$in": [ObjectId(branch_id) for branch_id in current_user.branches]}
    elif current_user.role.name == "Partner":
        match['branch'] = {"$in": [ObjectId(branch_id) for branch_id in current_user.branches]}
    elif current_user.role.name == "Secretary":
        match['branch'] = current_user.branch.id

    aggregate_query = [
        {'$match': match},
        {"$lookup": {
            'from': 'lms_branches',
            'localField': 'branch',
            'foreignField': '_id',
            'as': 'branch'
        }},
        {'$sort': {'added_to_hired_date': pymongo.DESCENDING}}
    ]
    if start:
        aggregate_query.append({'$skip': start})

    if length:
        aggregate_query.append({'$limit': length})

    query = list(mongo.db.lms_registrations.aggregate(aggregate_query))
    total_records = mongo.db.lms_registrations.find(match).count()
    filtered_records = len(query)
    table_data = []
    
    for doc in query:
        student = Student(doc)
        deployment_information = student.data.get('deployment_information', {})
        
        table_data.append([
            str(student.get_id()),
            student.get_full_name(),
            format_utc_to_local(deployment_information.get('deployment_date')),
            student.get_branch_name(),
            deployment_information.get('is_active', 'false'),
            ''
        ])
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }
    return jsonify(response)


@bp_lms.route('/datatables/student-records/deployed/mdl-students', methods=['GET'])
def datatables_student_records_deployed_mdl_students():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(Q(status="registered") & Q(is_hired=True) & Q(is_deployed__ne=True)).filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(Q(status="registered") & Q(is_hired=True) & Q(is_deployed__ne=True))
    elif current_user.role.name == "Partner":
        clients = Registration.objects(Q(status="registered") & Q(is_hired=True) & Q(is_deployed__ne=True)).filter(branch__in=current_user.branches)
    elif current_user.role.name == "Manager":
        clients = Registration.objects(Q(status="registered") & Q(is_hired=True) & Q(is_deployed__ne=True)).filter(branch__in=current_user.branches)
    else:
        return abort(404)

    table_data = []
    for client in clients:
        table_data.append([
            str(client.id),
            client.lname,
            client.fname,
            client.mname,
            client.suffix,
            client.contact_number,
            client.status.upper()
        ])
    response = {
        'data': table_data
    }
    return jsonify(response)
