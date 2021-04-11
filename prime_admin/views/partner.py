from prime_admin.forms import PartnerForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Partner
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/partners')
@login_required
def partners():
    form = PartnerForm()

    _table_data = []

    return admin_table(Partner, fields=[], form=form, table_data=_table_data)
