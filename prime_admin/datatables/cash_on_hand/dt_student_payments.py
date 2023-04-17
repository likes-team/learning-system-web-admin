import decimal
from bson.objectid import ObjectId
from flask import jsonify, request
from flask_login import current_user
from app import mongo
from prime_admin import bp_lms
from prime_admin.models import Accommodation, Registration, StoreRecords
from prime_admin.utils import currency, date



@bp_lms.route('/datatables/cash-on-hand/student-payments', methods=['GET'])
def fetch_cash_on_hand_student_payments_dt():
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        response = {
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
    elif current_user.role.name == "Manager":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
        store_records = StoreRecords.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")
        accommodations = Accommodation.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")

    _data = []
    total_student_payments = 0

    for client in clients:
        student_payments = mongo.db.lms_registration_payments.find({"payment_by": ObjectId(client.id)})
        for payment in student_payments:
            payment_deposited = payment.get('deposited')
            if payment_deposited == "Pre Deposit":
                total_student_payments += currency.convert_decimal128_to_decimal(payment['amount'])

                _data.append([
                    date.format_utc_to_local(payment['date']),
                    str(client.full_registration_number),
                    client.full_name,
                    client.batch_number.number,
                    client.schedule,
                    client.payment_mode,
                    str(payment['amount']),
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
        'data': _data,
        'totalStudentPayments': str(total_student_payments),
        'totalCashOnHand': str(total_cash_on_hand),
        'totalItemsSold': str(total_items_sold),
        'totalAccommodations': str(total_accommodations)
        }
    return jsonify(response)
