from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, ContactPerson, OrientationAttendance
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/orientation-attendance')
@login_required
def orientation_attendance():

    _table_columns = [
        'Branch',
        'full name',
        'contact no',
        'contact person',
        'orientator'
    ]

    contact_persons = ContactPerson.objects
    branches = Branch.objects

    return admin_table(
        OrientationAttendance,
        fields=[],
        table_data=[],
        table_columns=_table_columns,
        heading="Orientation Attendance",
        title="Orientation attendance",
        table_template="lms/orientation_attendance.html",
        contact_persons=contact_persons,
        branches=branches
        )