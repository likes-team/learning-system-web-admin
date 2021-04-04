from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Registration, TrainingCenter, Teacher, Student
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/members', methods=['GET', 'POST'])
@login_required
def members():
    fields = []

    _registrations = Registration.objects

    _table_data = []

    for registration in _registrations:
        _table_data.append((
            registration.id,
            registration.created_at,
            registration.registration_number,
            registration.full_name,
            registration.batch_number,
            registration.branch,
            registration.schedule,
            "",
            registration.amount,
            registration.amount,
            
        ))

    return admin_table(
        Registration,
        fields=fields,
        table_data=_table_data,
        )

