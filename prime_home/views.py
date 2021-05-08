import decimal

from flask.templating import render_template
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_home import bp_prime_home
from prime_admin.models import Branch, ContactPerson, Registration
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime
from bson.decimal128 import Decimal128



@bp_prime_home.route('/')
def index():
    return render_template('prime_home/index.html')
