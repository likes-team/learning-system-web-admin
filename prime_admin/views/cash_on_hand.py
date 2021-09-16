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
from prime_admin.models import Accounting, Branch, CashFlow, CashOnHand, OrientationAttendance, Registration, Batch, Orientator
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

    # if current_user.role.name == "Secretary":
    #     branches = Branch.objects(id=current_user.branch.id)
    # elif current_user.role.name == "Partner":
    #     branches = Branch.objects(id__in=current_user.branches)
    # else:
    #     branches = Branch.objects

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
        modals=modals
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

    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                for selected_payment in payments_selected:
                    mongo.db.lms_registrations.update_one({
                        "full_registration_number": selected_payment['full_registration_number'],
                        "payments._id": ObjectId(selected_payment['payment_id'])
                    },
                    {"$set": {
                        "payments.$.deposited": "Pre Deposit"
                    }}, session=session)
        response = {'result': True}
    except Exception:
        response = {'result': False}

    return jsonify(response)


@bp_lms.route('/api/dtbl/student-payments', methods=['GET'])
def get_dtbl_student_payments():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(status="registered")
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
    else:
        return jsonify({'data': []})

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
    response = {
        'data': _data,
        'totalStudentPayments': str(total_student_payments)
        }

    return jsonify(response)
