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
from prime_admin.models import Accomodation, Branch, Earning, Registration, Batch, StoreRecords
from flask import redirect, url_for, request, current_app, flash, jsonify
from app import mongo
from datetime import datetime, timedelta
from bson.decimal128 import Decimal128, create_decimal128_context
import decimal
from mongoengine.queryset.visitor import Q



D128_CTX = create_decimal128_context()


@bp_lms.route('/acommodation', methods=['GET'])
@login_required
def accomodation():
    _table_columns = [
        'id', 'date','Registration No.', 'Full Name', 'branch','batch no.', 'schedule', 'uniform', 'id lace', 'id card','module 1'
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
        Accomodation,
        fields=[],
        table_data=[],
        table_columns=_table_columns,
        heading="",
        subheading='',
        title='Accomodation',
        table_template='lms/accomodation.html',
        branches=branches,
        batch_numbers=batch_numbers,
        scripts=[]
    )


# @bp_lms.route('/dtbl/store-records')
# def get_dtbl_store_records():
#     draw = request.args.get('draw')
#     start, length = int(request.args.get('start')), int(request.args.get('length'))
#     branch_id = request.args.get('branch')
#     batch_no = request.args.get('batch_no')

#     if branch_id == 'all':
#         _store_records = mongo.db.lms_store_buyed_items.find().skip(start).limit(length).sort('created_at', pymongo.DESCENDING)
#     else:
#         _store_records = mongo.db.lms_store_buyed_items.find({"branch": ObjectId(branch_id)}).skip(start).limit(length).sort('created_at', pymongo.DESCENDING)

#     table_data = []

#     for record in _store_records:
#         student = Registration.objects(id=record['client_id']).get()

#         table_data.append([
#             str(record['_id']),
#             convert_to_local(record['created_at']),
#             student.full_registration_number,
#             student.full_name,
#             student.branch.name,
#             student.batch_number.number,
#             student.schedule,
#             record['uniforms'],
#             record['id_lace'],
#             record['id_card'],
#             record['module_1'],
#             record['module_2'],
#             record['reviewer_l'],
#             record['reviewer_r'],
#         ])

#     response = {
#         'draw': draw,
#         'recordsTotal': _store_records.count(),
#         'recordsFiltered': _store_records.count(),
#         'data': table_data,
#     }

#     return jsonify(response)
