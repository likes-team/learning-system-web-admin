from prime_admin.forms import PartnerForm, SecretaryForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Secretary
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/secretaries')
@login_required
def secretaries():
    form = SecretaryForm()

    _table_data = []

    return admin_table(Secretary, fields=[], form=form, table_data=_table_data)
