from bson.objectid import ObjectId
from flask import jsonify, request
from flask_login import current_user
from prime_admin import bp_lms
from prime_admin.models import Accommodation
from prime_admin.utils import currency, date



@bp_lms.route('/datatables/cash-on-hand/accommodations', methods=['GET'])
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
    elif current_user.role.name == "Manager":
        accommodations = Accommodation.objects(branch__in=current_user.branches).filter(deposited="Pre Deposit")

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