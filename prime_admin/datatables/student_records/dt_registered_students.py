from flask import request, jsonify
from flask_login import current_user
from prime_admin import bp_lms
from prime_admin.helpers.query_filter import StudentQueryFilter
from prime_admin.services.student import StudentService
from prime_admin.models import Student



@bp_lms.route('/datatables/student-records/registered-students')
def fetch_registered_students_dt():
    draw = request.args.get('draw')
    query_filter = StudentQueryFilter.from_request(request)
    service = StudentService.find_students(query_filter)
    students = service.get_data()
    _table_data = []

    student: Student
    for student in students:
        # TODO Move this to JS
        actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#editModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-success btn-edit"><i class="pe-7s-wallet btn-icon-wrapper"> </i></button>
            <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
        
        if current_user.role.name in ['Secretary', 'Admin', 'Partner']:
            if student.payment_mode == "premium" or student.payment_mode == "premium_promo":
                actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
        else: # Marketers
            actions = ""
            
        _table_data.append([
            str(student.get_id()),
            student.get_registration_date(),
            student.full_registration_number,
            student.get_full_name(),
            student.get_batch_no(),
            student.get_branch_name(),
            student.schedule,
            student.get_payment_mode(),
            student.get_amount(currency=True),
            student.get_balance(currency=True),
            student.get_payment_status(),
            student.get_is_deposited(),
            student.get_contact_person_name(),
            student.data.get('orientator', {}).get('fname', ''),
            student.get_session(),
            student.contact_number,
            student.created_by,
            actions
        ])
    response = {
        'draw': draw,
        'recordsTotal': service.total_filtered(),
        'recordsFiltered': service.total_filtered(),
        'data': _table_data,
    }
    return jsonify(response)