from bson import ObjectId
from flask import request, render_template, jsonify
from flask_login import login_required
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import get_utc_date_now, convert_date_input_to_utc



@bp_lms.route('/passers')
@login_required
def passers():
    exam_venues = mongo.db.lms_configurations.find_one({'name': "exam_venues"})['values']
    industries = mongo.db.lms_configurations.find_one({'name': "industries"})['values']
    batch_numbers = mongo.db.lms_examination_batch_numbers.find()
    sessions = mongo.db.lms_examination_sessions.find()
    return render_template(
        'lms/student_records/passers/passers_page.html',
        exam_venues=exam_venues,
        industries=industries,
        batch_numbers=batch_numbers,
        sessions=sessions
    )


@bp_lms.route('/passers/add', methods=['POST'])
def add_to_passers():
    form = request.form
    
    student_id = ObjectId(form.get('student_id'))
    score = float(form.get('score'))
    primary_key = form.get('primary_key')

    mongo.db.lms_registrations.update_one({
        '_id': student_id
    },{'$set':
       {
           'remark': "PASSED",
           'score': score,
           'primary_key': primary_key,
           'is_examinee': False,
           'is_passer': True,
           'added_to_passers_date': get_utc_date_now()
       }
    })
    
    response = {
        'status': 'success',
        'message': "Added successfully!"
    }
    return jsonify(response)
