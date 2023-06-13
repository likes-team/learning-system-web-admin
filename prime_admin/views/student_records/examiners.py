from bson import ObjectId
from flask import request, render_template, jsonify
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import get_utc_date_now, convert_date_input_to_utc



@bp_lms.route('/examiners')
def examiners():
    exam_venues = mongo.db.lms_configurations.find_one({'name': "exam_venues"})['values']
    industries = mongo.db.lms_configurations.find_one({'name': "industries"})['values']
    batch_numbers = mongo.db.lms_examination_batch_numbers.find()
    sessions = mongo.db.lms_examination_sessions.find()
    return render_template(
        'lms/student_records/examiners/examiners_page.html',
        exam_venues=exam_venues,
        industries=industries,
        batch_numbers=batch_numbers,
        sessions=sessions
    )


@bp_lms.route('/examiners/add', methods=['POST'])
def add_to_examiners():
    form = request.form
    
    student_id = ObjectId(form.get('student_id'))
    industry = form.get('industry')
    sub_category = form.get('sub_category')
    application_no = form.get('application_no')
    room = form.get('room')
    exam_venue = form.get('exam_venue')
    no_of_klt = form.get('no_of_klt')
    session = form.get('session')
    test_date = convert_date_input_to_utc(form.get('test_date'), date_format="%Y-%m-%dT%H:%M")

    mongo.db.lms_registrations.update_one({
        '_id': student_id
    },{'$set':
       {
           'industry': industry,
           'sub_category': sub_category,
           'application_no': application_no,
           'room': room,
           'exam_venue': exam_venue,
           'no_of_klt': no_of_klt,
           'session': session,
           'test_date': test_date,
           'is_examinee': True,
           'added_to_examinees_date': get_utc_date_now()
       }
    })
    
    response = {
        'status': 'success',
        'message': "Added successfully!"
    }
    return jsonify(response)
