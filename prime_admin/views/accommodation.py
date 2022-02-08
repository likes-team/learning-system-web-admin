from bson.objectid import ObjectId
from flask_mongoengine import json
import pymongo
from prime_admin.globals import SECRETARYREFERENCE, convert_to_local, get_date_now
from app.auth.models import User
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Accommodation, Branch, Earning, Registration, Batch, StoreRecords
from flask import redirect, url_for, request, current_app, flash, jsonify
from app import mongo
from datetime import datetime, timedelta
from bson.decimal128 import Decimal128, create_decimal128_context
import decimal
from mongoengine.queryset.visitor import Q



D128_CTX = create_decimal128_context()


@bp_lms.route('/acommodation', methods=['GET'])
@login_required
def accommodation():
    _table_columns = [
        'id', 'date', 'Registration No.', 'Full Name', 'branch','batch no.', 'schedule', 'date_from', 'date_to', 'days', 'total amount', 'remarks'
    ]

    _modals = [
        'lms/search_client_last_name_modal.html',
    ]

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
    else:
        branches = Branch.objects()
        batch_numbers = Batch.objects()

    return admin_table(
        Accommodation,
        fields=[],
        table_data=[],
        table_columns=_table_columns,
        heading="",
        subheading='',
        title='Accommodation',
        table_template='lms/accommodation.html',
        branches=branches,
        batch_numbers=batch_numbers,
        scripts=[],
        modals=_modals
    )


@bp_lms.route("/accomodate", methods=["POST"])
@login_required
def accomodate():
    # try:
    client_id = request.form['client_id']
    branch_id = request.form['branch_id']
    date_from = request.form['date_from']
    date_to = request.form['date_to']
    price_per_day = request.form['price_per_day']
    remarks = request.form['remarks']

    d1 = datetime.strptime(date_from, "%Y-%m-%d")
    d2 = datetime.strptime(date_to, "%Y-%m-%d")
    days =  abs((d2 - d1).days)
    total = decimal.Decimal(price_per_day) * days

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            client = mongo.db.lms_registrations.find_one({"_id": ObjectId(client_id)})

            mongo.db.lms_accommodations.insert_one({
                'client_id': ObjectId(client_id),
                'created_at': get_date_now(),
                'branch': ObjectId(branch_id),
                'date_from': date_from,
                'date_to': date_to,
                'days': days,
                'total_amount': Decimal128(str(total)),
                'remarks': remarks,
                'deposited': "Pre Deposit"
            })

    flash("Process successfully!", 'success')
    # except Exception as err:
    #     flash("Error occured:" + str(err), 'error')

    return redirect(url_for('lms.accommodation'))

@bp_lms.route('/dtbl/accommodations')
def get_dtbl_accommodations():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        query = mongo.db.lms_accommodations.find().skip(start).limit(length).sort('created_at', pymongo.DESCENDING)
    else:
        query = mongo.db.lms_accommodations.find({"branch": ObjectId(branch_id)}).skip(start).limit(length).sort('created_at', pymongo.DESCENDING)

    table_data = []

    for doc in query:
        try:
            student = Registration.objects(id=doc['client_id']).get()

            table_data.append([
                str(doc['_id']),
                convert_to_local(doc['created_at']),
                student.full_registration_number,
                student.full_name,
                student.branch.name,
                student.batch_number.number,
                student.schedule,
                doc['date_from'],
                doc['date_to'],
                doc['days'],
                str(doc['total_amount']),
                doc['remarks']
            ])
        except Exception:
            continue

    response = {
        'draw': draw,
        'recordsTotal': query.count(),
        'recordsFiltered': query.count(),
        'data': table_data,
    }

    return jsonify(response)
