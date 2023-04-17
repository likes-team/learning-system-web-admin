import decimal
import pytz
from datetime import datetime
from bson.objectid import ObjectId
from bson import Decimal128
from bson.decimal128 import create_decimal128_context
from flask import jsonify, request
from flask_login import login_required, current_user
from config import TIMEZONE
from app import mongo
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import Accommodation, CashOnHand, Registration, StoreRecords
from prime_admin.helpers import access



D128_CTX = create_decimal128_context()


@bp_lms.route('/cash-on-hand')
@login_required
def cash_on_hand():
    branches = access.get_current_user_branches()
    modals = [
        'lms/pre_deposit_modal.html',
    ]
    return admin_table(
        CashOnHand,
        fields=[],
        table_data=[],
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
            student_payments = mongo.db.lms_registration_payments.find({"payment_by": ObjectId(client.id)})
            for payment in student_payments:
                payment_deposited = payment.get('deposited')
                if payment_deposited is None or payment_deposited == "No":
                    if type(payment['date']) == datetime:
                        local_datetime = payment['date'].replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
                    elif type(payment['date'] == str):
                        to_date = datetime.strptime(payment['date'], "%Y-%m-%d")
                        local_datetime = to_date.strftime("%B %d, %Y")
                    else: 
                        local_datetime = ''

                    _data.append([
                        str(payment['_id']),
                        str(client.full_registration_number),
                        client.lname,
                        client.fname,
                        client.mname,
                        client.suffix,
                        str(payment['amount']),
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
    """(DEPRECATED)

    Returns:
        _type_: _description_
    """
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
                        amount = Decimal128(amount.to_decimal() + decimal.Decimal(str(payment['payments'][0]['amount'])))

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
                        amount = Decimal128(amount.to_decimal() + payment['total_amount'].to_decimal())

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

                        amount = Decimal128(amount.to_decimal() + payment['total_amount'].to_decimal())

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


@bp_lms.route('/api/dtbl/mdl-store-items-sold', methods=['GET'])
def get_mdl_store_items_sold():
    if current_user.role.name == "Secretary":
        store_records = StoreRecords.objects(branch=current_user.branch).filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")
    elif current_user.role.name == "Admin":
        store_records = StoreRecords.objects().filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")
    elif current_user.role.name == "Partner":
        store_records = StoreRecords.objects(branch__in=current_user.branches).filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")
    elif current_user.role.name == "Manager":
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
    elif current_user.role.name == "Manager":
        accomodations = Accommodation.objects(branch__in=current_user.branches).filter(deposited__ne="Pre Deposit").filter(deposited__ne="Deposited")

    data = []

    record : Accommodation
    for record in accomodations:
        try:
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
        except Exception:
            continue

    response = {
        'data': data
        }

    return jsonify(response)