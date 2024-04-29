import pymongo
from bson import ObjectId
from mongoengine.queryset.visitor import Q
from flask import abort, jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin import bp_lms
from prime_admin.models import Registration
from prime_admin.models_v2 import StudentV2
from prime_admin.utils.date import format_utc_to_local
from prime_admin.helpers.query_filter import StudentQueryFilter
from prime_admin.services.student import StudentService



@bp_lms.route('/datatables/student-records/examiners')
def fetch_examiners_dt():
    draw = request.args.get('draw')
    query_filter = StudentQueryFilter.from_request(request)
    query_filter.set_sort({'added_to_examinees_date': pymongo.DESCENDING})
    service = StudentService.find_students(query_filter)
    students = service.get_data()
 
    table_data = []
    ctr = query_filter.get_start()
    
    for student in students:
        ctr = ctr + 1
        
        table_data.append([
            str(student.get_id()),
            ctr,
            student.data.get('application_no', ''),
            student.get_full_name(),
            student.data.get('gender', ''),
            student.data.get('industry', ''),
            student.data.get('room', ''),
            format_utc_to_local(student.data.get('test_date'), with_time=True),
            student.data.get('session', ''),
            '',
        ])

    response = {
        'draw': draw,
        'recordsTotal': service.total_filtered(),
        'recordsFiltered': service.total_filtered(),
        'data': table_data,
    }
    return jsonify(response)


@bp_lms.route('/datatables/student-records/examiners/mdl-students', methods=['GET'])
def fetch_mdl_students_dt():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(Q(status="registered") & Q(is_examinee__ne=True)).filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(Q(status="registered") & Q(is_examinee__ne=True))
    elif current_user.role.name == "Partner":
        clients = Registration.objects(Q(status="registered") & Q(is_examinee__ne=True)).filter(branch__in=current_user.branches)
    elif current_user.role.name == "Manager":
        clients = Registration.objects(Q(status="registered") & Q(is_examinee__ne=True)).filter(branch__in=current_user.branches)
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