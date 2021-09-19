import decimal
import uuid
from bson.objectid import ObjectId
from prime_admin.globals import SECRETARYREFERENCE, convert_to_utc, get_date_now
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, BuyItems, Payment, Registration
from app.auth.models import Earning, Role, User
from flask import redirect, url_for, request, current_app, flash, jsonify, abort
from app import db, mongo
from datetime import datetime
from bson.decimal128 import Decimal128
from mongoengine.queryset.visitor import Q
from config import TIMEZONE



@bp_lms.route('/store/buy-items', methods=['GET', 'POST'])
@login_required
def buy_items():
    if request.method == "GET":
        _modals = [
            'lms/search_client_last_name_modal.html',
        ]

        return admin_render_template(
            BuyItems,
            'lms/buy_items.html',
            'learning_management',
            modals=_modals,
            title="Buy Items"
            )

    return redirect(url_for('lms.members'))
