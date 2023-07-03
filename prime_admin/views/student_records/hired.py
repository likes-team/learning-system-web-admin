from bson import ObjectId
from flask import request, render_template, jsonify
from flask_login import login_required
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import get_utc_date_now, convert_date_input_to_utc



@bp_lms.route('/hired')
@login_required
def hired():
    exam_venues = mongo.db.lms_configurations.find_one({'name': "exam_venues"})['values']
    industries = mongo.db.lms_configurations.find_one({'name': "industries"})['values']
    batch_numbers = mongo.db.lms_examination_batch_numbers.find()
    sessions = mongo.db.lms_examination_sessions.find()
    klts = mongo.db.lms_klts.find()
    return render_template(
        'lms/student_records/hired/hired_page.html',
        exam_venues=exam_venues,
        industries=industries,
        batch_numbers=batch_numbers,
        sessions=sessions,
        klts=klts
    )


@bp_lms.route('/hired/add', methods=['POST'])
def add_to_hired():
    form = request.form
    
    student_id = ObjectId(form.get('student_id'))
    employer_name = form.get('employer_name')
    company_name = form.get('company_name')
    employer_contact_no = form.get('employer_contact_no')
    address_in_korea = form.get('address_in_korea')
    title_of_work = form.get('title_of_work')

    mongo.db.lms_registrations.update_one({
        '_id': student_id
    },{'$set':
       {
            'employer_information': {
               'employer_name': employer_name,
               'company_name': company_name,
               'employer_contact_no': employer_contact_no,
               'address_in_korea': address_in_korea,
               'title_of_work': title_of_work,
               'added_to_hired_date': get_utc_date_now()
            },
            'is_hired': True,
            'is_passed': False,
            'is_examinee': False
       }
    })
    
    response = {
        'status': 'success',
        'message': "Added successfully!"
    }
    return jsonify(response)


@bp_lms.route('/hired/<string:student_id>/edit', methods=["POST"])
def edit_hired(student_id):
    form = request.form
    student_id = ObjectId(form['edit_student_id'])
    eps_topik = form.get('edit_eps_topik')
    eps_topik_date = convert_date_input_to_utc(form.get('edit_eps_topik_date'))
    jsr_forwarding = form.get('edit_jsr_forwarding')
    jsr_forwarding_date = convert_date_input_to_utc(form.get('edit_jsr_forwarding_date'))
    jsr_approval = form.get('edit_jsr_approval')
    jsr_approval_date = convert_date_input_to_utc(form.get('edit_jsr_approval_date'))
    job_search_progress = form.get('edit_job_search_progress')
    job_search_progress_date = convert_date_input_to_utc(form.get('edit_job_search_progress_date'))
    employment_permit_assuance = form.get('edit_employment_permit_assuance')
    employment_permit_assuance_date = convert_date_input_to_utc(form.get('edit_employment_permit_assuance_date'))
    slc_forwarding = form.get('edit_slc_forwarding')
    slc_forwarding_date = convert_date_input_to_utc(form.get('edit_slc_forwarding_date'))
    slc_signing = form.get('edit_slc_signing')
    slc_signing_date = convert_date_input_to_utc(form.get('edit_slc_signing_date'))
    ccvi_issuance = form.get('edit_ccvi_issuance')
    ccvi_issuance_date = convert_date_input_to_utc(form.get('edit_ccvi_issuance_date'))
    tentative_entry = form.get('edit_tentative_entry')
    tentative_entry_date = convert_date_input_to_utc(form.get('edit_tentative_entry_date'))

    current_status = None
    if eps_topik != '':
        current_status = "eps_topik"
    if jsr_forwarding != "":
        current_status = "jsr_forwarding"
    if jsr_approval != "":
        current_status = "jsr_approval"
    if job_search_progress != "":
        current_status = "job_search_progress"
    if employment_permit_assuance != "":
        current_status = "employment_permit_assuance"
    if slc_forwarding != "":
        current_status = "slc_forwarding"
    if slc_signing != "":
        current_status = "slc_signing"
    if ccvi_issuance != "":
        current_status = "ccvi_issuance"
    if tentative_entry != "":
        current_status = "tentative_entry"
    
    mongo.db.lms_registrations.update_one({
        '_id': student_id
    },{'$set':
       {
            'hired_information': {
               'current_status': current_status,
               'eps_topik': {'current_progress': eps_topik, 'date': eps_topik_date},
               'jsr_forwarding': {'current_progress': jsr_forwarding, 'date': jsr_forwarding_date},
               'jsr_approval': {'current_progress': jsr_approval, 'date': jsr_approval_date},
               'job_search_progress': {'current_progress': job_search_progress, 'date': job_search_progress_date},
               'employment_permit_assuance': {'current_progress': employment_permit_assuance, 'date': employment_permit_assuance_date},
               'slc_forwarding': {'current_progress': slc_forwarding, 'date': slc_forwarding_date},
               'slc_signing': {'current_progress': slc_signing, 'date': slc_signing_date},
               'ccvi_issuance': {'current_progress': ccvi_issuance, 'date': ccvi_issuance_date},
               'tentative_entry': {'current_progress': tentative_entry, 'date': tentative_entry_date},
            }
       }
    })
    response = {
        'status': 'success',
        'message': "Saved successfully!"
    }
    return jsonify(response)
