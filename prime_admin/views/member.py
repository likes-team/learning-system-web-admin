from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Registration, Member
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/members', methods=['GET', 'POST'])
@login_required
def members():
    _table_columns = [
        'date', 'registration','name of student', 'batch no.', 'branch', 'schedule', 'remark',
        'amount','balance', 'paid/not paid', 'contact person', 'book 1', 'book 2', 'cashier'
        ]

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
        Member,
        fields=fields,
        table_data=_table_data,
        table_columns=_table_columns,
        heading='Members',
        subheading="",
        title='Members',
        table_template="lms/members_table.html"
        )

