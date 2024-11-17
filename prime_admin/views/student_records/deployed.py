from bson import ObjectId
from flask import request, render_template, jsonify
from flask_login import login_required
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import get_utc_date_now
from prime_admin.utils.upload import allowed_file
from prime_admin.services.s3 import upload_file


@bp_lms.route('/deployed')
@login_required
def deployed():
    exam_venues = mongo.db.lms_configurations.find_one({'name': "exam_venues"})['values']
    industries = mongo.db.lms_configurations.find_one({'name': "industries"})['values']
    batch_numbers = mongo.db.lms_examination_batch_numbers.find()
    sessions = mongo.db.lms_examination_sessions.find()
    klts = mongo.db.lms_klts.find()
    return render_template(
        'lms/student_records/deployed/deployed_page.html',
        exam_venues=exam_venues,
        industries=industries,
        batch_numbers=batch_numbers,
        sessions=sessions,
        klts=klts
    )


@bp_lms.route('/deployed/add', methods=['POST'])
def add_to_deployed():
    form = request.form
    student_id = form.get('student_id')
    student_message = request.form['student_message']
    tarp_photo = request.files['tarp_photo']
    message_photo = request.files['message_photo']
    
    if student_id == '':
        response = {
            'status': "error",
            'message': "Please select student"
        }
        return jsonify(response), 400

    student_id = ObjectId(student_id)

    if tarp_photo.filename == '' or message_photo.filename == '':
        response = {
            'status': "error",
            'message': "Please upload the 2 photos"
        }
        return jsonify(response), 400

    # check whether the file extension is allowed (eg. png,jpeg,jpg,gif)
    if not allowed_file(tarp_photo.filename, file_type="video") or not allowed_file(message_photo.filename):
        response = {
            'status': "error",
            'message': "File is not allowed"
        }
        return jsonify(response), 400
    
    if tarp_photo != '' and message_photo != '':
        tarp_photo_output = upload_file(tarp_photo, tarp_photo.filename, folder_name="landing_page/student_testimonies_img/")
        message_photo_output = upload_file(message_photo, message_photo.filename, folder_name="landing_page/student_testimonies_img/")
    else:
        tarp_photo_output = None
        message_photo_output = None

    mongo.db.lms_registrations.update_one({
        '_id': student_id
    },{'$set':
       {
            'deployment_information': {
               'student_message': student_message,
               'tarp_photo': tarp_photo_output,
               'message_photo': message_photo_output,
               'deployment_date': get_utc_date_now(),
               'is_active': True
            },
            'is_deployed': True
       }
    })
    
    response = {
        'status': 'success',
        'message': "Deployed successfully!"
    }
    return jsonify(response)


@bp_lms.route('/deployed/toggle-status', methods=['POST'])
def toggle_deployed_status():
    student_id = request.json['student_id']

    mongo.db.lms_registrations.update_one({
        '_id': ObjectId(student_id)
    }, [{'$set': {
        "deployment_information.is_active": {
            "$eq": [False,"$deployment_information.is_active"]
        }}}])
    return jsonify({'result': True})