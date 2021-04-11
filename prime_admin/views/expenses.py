from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Expenses
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime


@bp_lms.route('/expenses')
@login_required
def expenses():
    _table_columns = [
        'date', 'description', 'quantity', 'subtotal'
    ]

    return admin_table(
        Expenses,
        fields=[],
        table_data=[],
        table_columns=_table_columns,
        heading="",
        subheading='',
        title='Expenses',
        table_template='lms/expenses.html'
    )