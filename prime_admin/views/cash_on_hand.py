from bson.decimal128 import create_decimal128_context
from bson.objectid import ObjectId
from flask_mongoengine import json
import pytz
from config import TIMEZONE
import decimal
from prime_admin.globals import PARTNERREFERENCE, SECRETARYREFERENCE, convert_to_utc, get_date_now
from app.auth.models import Earning, User
from prime_admin.forms import CashFlowAdminForm, CashFlowSecretaryForm, DepositForm, OrientationAttendanceForm, WithdrawForm
from flask.helpers import flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import redirect
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Accommodation, Accounting, Branch, CashFlow, CashOnHand, OrientationAttendance, Registration, Batch, Orientator, StoreRecords
from flask import jsonify, request
from datetime import date, datetime
from mongoengine.queryset.visitor import Q
from bson import Decimal128
from app import mongo



D128_CTX = create_decimal128_context()


@bp_lms.route('/cash-on-hand')
@login_required
def cash_on_hand():

    # if current_user.role.name == "Secretary":
    #     form = CashFlowSecretaryForm()

    # else:
    #     form = CashFlowAdminForm()
    
    _table_data = []

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    else:
        branches = Branch.objects

    # orientators = Orientator.objects()

    modals = [
        'lms/pre_deposit_modal.html',
    ]

    return admin_table(
        CashOnHand,
        fields=[],
        # form=form,
        table_data=_table_data,
        table_columns=['id'],
        heading="Cash On Hand",
        subheading="Cash In / Cash Out",
        title="Cash On Hand",
        table_template="lms/cash_on_hand.html",
        modals=modals,
        branches=branches
        )


@bp_lms.route('/api/dtbl/mdl-pre-deposit', methods=['GET'])
def get_mdl_pre_deposit():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(status="registered")
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
    else:
        return jsonify({'data': []})

    _data = []

    for client in clients:
        if client.amount != client.amount_deposit:
            for payment in client.payments:
                if payment.deposited is None or payment.deposited == "No":
                    if type(payment.date) == datetime:
                        local_datetime = payment.date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
                    elif type(payment.date == str):
                        to_date = datetime.strptime(payment.date, "%Y-%m-%d")
                        local_datetime = to_date.strftime("%B %d, %Y")
                    else: 
                        local_datetime = ''

                    _data.append([
                        payment.id,
                        str(client.full_registration_number),
                        client.lname,
                        client.fname,
                        client.mname,
                        client.suffix,
                        str(payment.amount),
                        local_datetime
                        # str(payment['current_balance']),
                        # str(payment['deposited']) if 'deposit' in payment else 'No'
                    ])
    response = {
        'data': _data
        }

    return jsonify(response)


@bp_lms.route('/api/to-pre-deposit', methods=['POST'])
def to_pre_deposit():
    payments_selected = request.json['payments_selected']
    source = request.json['source']

    amount : Decimal128 = Decimal128('0.00')

    # try:
    with mongo.cx.start_session() as session:
        with session.start_transaction():
            with decimal.localcontext(D128_CTX):
                if source == "student_enrollees_payment":
                    for selected_payment in payments_selected:
                        mongo.db.lms_registrations.update_one({
                            "full_registration_number": selected_payment['full_registration_number'],
                            "payments._id": ObjectId(selected_payment['payment_id'])
                        },
                        {"$set": {
                            "payments.$.deposited": "Pre Deposit"
                        }}, session=session)

                        payment = mongo.db.lms_registrations.find_one({
                            "full_registration_number": selected_payment['full_registration_number'],
                            "payments._id": ObjectId(selected_payment['payment_id'])
                        },{
                            "payments": {"$elemMatch": {"_id": ObjectId(selected_payment['payment_id'])}}
                        }, session=session)

                        print(payment)
                        
                        amount = Decimal128(amount.to_decimal() + payment['payments'][0]['amount'].to_decimal())
                        print(amount)
                elif source == "store_items_sold":
                    for selected_payment in payments_selected:
                        mongo.db.lms_store_buyed_items.update_one({
                            "_id": ObjectId(selected_payment['payment_id']),
                        },
                        {"$set": {
                            "deposited": "Pre Deposit"
                        }}, session=session)

                        payment = mongo.db.lms_store_buyed_items.find_one({
                            "_id": ObjectId(selected_payment['payment_id']),
                        }, session=session)

                        print(payment)
                        
                        amount = Decimal128(amount.to_decimal() + payment['total_amount'].to_decimal())
                        print(amount)

                elif source == "accommodation":
                    for selected_payment in payments_selected:
                        mongo.db.lms_accommodations.update_one({
                            "_id": ObjectId(selected_payment['payment_id']),
                        },
                        {"$set": {
                            "deposited": "Pre Deposit"
                        }}, session=session)

                        payment = mongo.db.lms_accommodations.find_one({
                            "_id": ObjectId(selected_payment['payment_id']),
                        }, session=session)

                        print(payment)
                        
                        amount = Decimal128(amount.to_decimal() + payment['total_amount'].to_decimal())
                        print(amount)


                accounting = mongo.db.lms_accounting.find_one({"branch": current_user.branch.id}, session=session)

                if accounting:
                    mongo.db.lms_accounting.update_one({
                        "_id": accounting["_id"],
                    },
                    {"$inc": {
                        "total_cash_on_hand": amount
                    }}, session=session)
                else:
                    mongo.db.lms_accounting.insert_one({
                            "_id": ObjectId(),
                            "branch": current_user.branch.id,
                            "active_group": 1,
                            "total_cash_on_hand": amount,
                            "total_gross_sale": Decimal128("0.00"),
                            "final_fund1": Decimal128("0.00"),
                            "final_fund2": Decimal128("0.00"),
                        }, session=session)
        
    response = {'result': True}
    # except Exception:
    #     response = {'result': False}

    return jsonify(response)


@bp_lms.route('/api/dtbl/student-payments', methods=['GET'])
def get_dtbl_student_payments():
    draw = request.args.get('draw')
    # start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'totalStudentPayments': " 0.00",
            'totalCashOnHand': " 0.00",
            'totalItemsSold': " 0.00",
            'totalAccommodations': " 0.00",
            'data': [],
        }

        return jsonify(response)

    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)
        store_records = StoreRecords.objects(branch=current_user.branch).filter(deposited="Pre Deposit")
        accommodations = Accommodation.objects(branch=current_user.branch).filter(deposited="Pre Deposit")
    elif current_user.role.name == "Admin":
        clients = Registration.objects(status="registered").filter(branch=ObjectId(branch_id))
        store_records = StoreRecords.objects().filter(deposited="Pre Deposit").filter(branch=ObjectId(branch_id))
        accommodations = Accommodation.objects().filter(deposited="Pre Deposit").filter(branch=ObjectId(branch_id))
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
        store_records = StoreRecords.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")
        accommodations = Accommodation.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")
    else:
        raise Exception("Wrong User Role")

    _data = []
    total_student_payments = 0

    with decimal.localcontext(D128_CTX):
        for client in clients:
            for payment in client.payments:
                if payment.deposited == "Pre Deposit":
                    if type(payment.date) == datetime:
                        local_datetime = payment.date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
                    elif type(payment.date == str):
                        to_date = datetime.strptime(payment.date, "%Y-%m-%d")
                        local_datetime = to_date.strftime("%B %d, %Y")
                    else: 
                        local_datetime = ''

                    total_student_payments += payment.amount

                    _data.append([
                        local_datetime,
                        str(client.full_registration_number),
                        client.full_name,
                        client.batch_number.number,
                        client.schedule,
                        client.payment_mode,
                        str(payment.amount),
                    ])

    total_items_sold : decimal.Decimal = 0
    record : StoreRecords
    for record in store_records:
        total_items_sold += record.total_amount

    total_accommodations : decimal.Decimal = 0
    record : Accommodation
    for record in accommodations:
        total_accommodations += record.total_amount

    total_cash_on_hand = total_student_payments + total_items_sold + total_accommodations

    response = {
        'draw': draw,
        'recordsTotal': 0,
        'recordsFiltered': 0,
        'data': _data,
        'totalStudentPayments': str(total_student_payments),
        'totalCashOnHand': str(total_cash_on_hand),
        'totalItemsSold': str(total_items_sold),
        'totalAccommodations': str(total_accommodations)
        }
    return jsonify(response)


@bp_lms.route('/api/dtbl/store-items-sold', methods=['GET'])
def get_dtbl_store_items_sold():
    draw = request.args.get('draw')
    # start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')
    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
        }
        return jsonify(response)

    if current_user.role.name == "Secretary":
        store_records = StoreRecords.objects(branch=current_user.branch).filter(deposited="Pre Deposit")
    elif current_user.role.name == "Admin":
        store_records = StoreRecords.objects().filter(deposited="Pre Deposit").filter(branch=ObjectId(branch_id))
    elif current_user.role.name == "Partner":
        store_records = StoreRecords.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")
    else:
        raise Exception("Wrong User Role")

    _data = []
    record : StoreRecords
    for record in store_records:
        _data.append([
            record.local_datetime,
            record.client_id.full_registration_number,
            record.client_id.full_name,
            record.client_id.batch_number.number,
            record.client_id.schedule,
            str(record.total_amount),
        ])

    response = {
        'draw': draw,
        'recordsTotal': 0,
        'recordsFiltered': 0,
        'data': _data,
        }
    return jsonify(response)


@bp_lms.route('/api/dtbl/accommodations', methods=['GET'])
def get_dtbl_coh_accommodations():
    draw = request.args.get('draw')
    # start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
        }
        return jsonify(response)

    if current_user.role.name == "Secretary":
        accommodations = Accommodation.objects(branch=current_user.branch).filter(deposited="Pre Deposit")
    elif current_user.role.name == "Admin":
        accommodations = Accommodation.objects().filter(deposited="Pre Deposit").filter(branch=ObjectId(branch_id))
    elif current_user.role.name == "Partner":
        accommodations = Accommodation.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")
    else:
        raise Exception("Wrong User Role")

    _data = []
    record : Accommodation
    for record in accommodations:
        _data.append([
            record.local_datetime,
            record.client_id.full_registration_number,
            record.client_id.full_name,
            record.client_id.batch_number.number,
            record.date_from,
            record.date_to,
            record.days,
            str(record.total_amount),
        ])

    response = {
        'draw': draw,
        'recordsTotal': 0,
        'recordsFiltered': 0,
        'data': _data,
        }
    return jsonify(response)


@bp_lms.route('/api/dtbl/mdl-store-items-sold', methods=['GET'])
def get_mdl_store_items_sold():
    if current_user.role.name == "Secretary":
        store_records = StoreRecords.objects(branch=current_user.branch).filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")
    elif current_user.role.name == "Admin":
        store_records = StoreRecords.objects().filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")
    elif current_user.role.name == "Partner":
        store_records = StoreRecords.objects(branch__in=current_user.branches).filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")

    data = []

    record : StoreRecords
    for record in store_records:
        data.append([
            str(record.id),
            record.local_datetime,
            str(record.client_id.full_registration_number),
            record.client_id.full_name,
            record.branch.name,
            record.client_id.batch_number.number,
            str(record.total_amount)
        ])

    response = {
        'data': data
        }

    return jsonify(response)


@bp_lms.route('/api/dtbl/mdl-accommodations', methods=['GET'])
def get_mdl_accommmodations():
    if current_user.role.name == "Secretary":
        accomodations = Accommodation.objects(branch=current_user.branch).filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")
    elif current_user.role.name == "Admin":
        accomodations = Accommodation.objects().filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")
    elif current_user.role.name == "Partner":
        accomodations = Accommodation.objects(branch__in=current_user.branches).filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")

    data = []

    record : Accommodation
    for record in accomodations:
        data.append([
            str(record.id),
            record.local_datetime,
            str(record.client_id.full_registration_number),
            record.client_id.full_name,
            record.branch.name,
            record.client_id.batch_number.number,
            record.date_from,
            record.date_to,
            record.days,
            str(record.total_amount)
        ])

    response = {
        'data': data
        }

    return jsonify(response)