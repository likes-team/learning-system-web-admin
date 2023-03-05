from bson.objectid import ObjectId
import pymongo
from prime_admin.globals import convert_to_local
from flask_login import login_required, current_user
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import Branch, Registration, Batch, StoreRecords
from flask import request, jsonify
from app import mongo
from bson.decimal128 import create_decimal128_context



D128_CTX = create_decimal128_context()


@bp_lms.route('/store-records', methods=['GET'])
@login_required
def store_records():
    _table_columns = [
        'id', 'date','Registration No.', 'Full Name', 'branch','batch no.', 
        'schedule', 'uniform', 'id lace', 'id card', 'book 1', 'book 2',
        'listening', 'reading' 
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
        StoreRecords,
        fields=[],
        table_data=[],
        table_columns=_table_columns,
        heading="",
        subheading='',
        title='Store Records',
        table_template='lms/store_records.html',
        branches=branches,
        batch_numbers=batch_numbers,
        scripts=[]
    )


@bp_lms.route('/dtbl/store-records')
def get_dtbl_store_records():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        _store_records = mongo.db.lms_store_buyed_items.find().skip(start).limit(length).sort('created_at', pymongo.DESCENDING)
    else:
        _store_records = mongo.db.lms_store_buyed_items.find({"branch": ObjectId(branch_id)}).skip(start).limit(length).sort('created_at', pymongo.DESCENDING)

    table_data = []

    for record in _store_records:
        student = Registration.objects(id=record['client_id']).get()
        items_purchased = {
            'UNIFORM': 0,
            'ID LACE': 0,
            'ID CARD': 0,
            'BOOK 1': 0,
            'BOOK 2': 0,
            'REVIEWER READING': 0,
            'REVIEWER LISTENING': 0
        }

        for item in record.get('items'):
            supply = mongo.db.lms_student_supplies.find_one({'_id': ObjectId(item['item'])})
            if supply is None:
                continue

            qty = int(str(item.get('qty')))
            if qty <= 0:
                continue
            
            items_purchased[supply['description']] += qty
         
        table_data.append([
            str(record['_id']),
            convert_to_local(record['created_at']),
            student.full_registration_number,
            student.full_name,
            student.branch.name,
            student.batch_number.number,
            student.schedule,
            items_purchased['UNIFORM'],
            items_purchased['ID LACE'],
            items_purchased['ID CARD'],
            items_purchased['BOOK 1'],
            items_purchased['BOOK 2'],
            items_purchased['REVIEWER LISTENING'],
            items_purchased['REVIEWER READING'],
        ])

    response = {
        'draw': draw,
        'recordsTotal': _store_records.count(),
        'recordsFiltered': _store_records.count(),
        'data': table_data,
    }
    return jsonify(response)
