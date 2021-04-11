from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Registration, TrainingCenter, Teacher, Student
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    registration_generated_number = ""
    
    last_registration_number = Registration.objects().order_by('-registration_number').first()

    date_now = datetime.now()

    if last_registration_number:
        registration_generated_number = generate_number(date_now, last_registration_number)
    else:
        registration_generated_number = str(date_now.year) + '%02d' % date_now.month + "0001"

    form = RegistrationForm()

    if request.method == "GET":

        data = {
            'registration_generated_number': registration_generated_number,
        }

        return admin_render_template(
            Registration,
            'lms/registration.html',
            'learning_management',
            form=form,
            data=data
            )
