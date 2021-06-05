from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, Earning, Registration, ContactPerson, Batch
from flask import redirect, url_for, request, current_app, flash, jsonify
from app import db
from datetime import datetime
from bson.decimal128 import Decimal128, create_decimal128_context
import decimal



D128_CTX = create_decimal128_context()


@bp_lms.route('/earnings', methods=['GET'])
@login_required
def earnings():
    _table_columns = [
        'Branch', 'Full Name', 'batch no.', 'schedule', 'remark'
    ]

    _scripts = [
        {'lms.static': 'js/earnings.js'}
    ]

    if current_user.role_name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
        marketers = ContactPerson.objects(branches__in=[str(current_user.branch.id)])
    else:
        branches = Branch.objects()
        batch_numbers = Batch.objects()
        marketers = ContactPerson.objects()

    return admin_table(
        Earning,
        fields=[],
        table_data=[],
        table_columns=_table_columns,
        heading="",
        subheading='',
        title='Earnings',
        table_template='lms/earnings.html',
        scripts=_scripts,
        marketers=marketers,
        branches=branches,
        batch_numbers=batch_numbers,
    )


@bp_lms.route('/dtbl/earnings/members')
def get_dtbl_earnings_members():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    # search_value = "%" + request.args.get("search[value]") + "%"
    # column_order = request.args.get('column_order')
    contact_person_id = request.args.get('contact_person')
    branch_id = request.args.get('branch')
    batch_no = request.args.get('batch_no')

    total_earnings = 0
    total_savings = 0
    branches_total_earnings = []

    if contact_person_id == 'all':
        registrations = Registration.objects.skip(start).limit(length)
        if current_user.role_name == "Secretary":
            contact_persons = ContactPerson.objects(branches__in=[str(current_user.branch.id)])
        else:
            contact_persons = ContactPerson.objects()

        with decimal.localcontext(D128_CTX):
            total_earnings = Decimal128('0.00')
            total_savings = Decimal128('0.00')
            
            for contact_person in contact_persons:
                for earning in contact_person.earnings:
                    total_earnings = Decimal128(total_earnings.to_decimal() + earning['earnings'].to_decimal())
                    total_savings = Decimal128(total_savings.to_decimal() + earning['savings'].to_decimal())
                    
                    print(total_earnings)
                    if not any(d['id'] == str(earning['branch'].id) for d in branches_total_earnings):
                        branches_total_earnings.append(
                            {
                                'id': str(earning['branch'].id),
                                'name': earning['branch'].name,
                                'totalEarnings': earning['earnings']
                            }
                        )
                    else:
                        for x in branches_total_earnings:
                            if x['id'] == str(earning['branch'].id):
                                x['totalEarnings'] = Decimal128(x['totalEarnings'].to_decimal() + earning['earnings'].to_decimal())
    else:
        registrations = Registration.objects(contact_person=contact_person_id).skip(start).limit(length)
        contact_person = ContactPerson.objects.get(id=contact_person_id)

        with decimal.localcontext(D128_CTX):
            total_earnings = Decimal128('0.00')
            total_savings = Decimal128('0.00')

            for earning in contact_person.earnings:
                total_earnings = Decimal128(total_earnings.to_decimal() + earning['earnings'].to_decimal())
                total_savings = Decimal128(total_savings.to_decimal() + earning['savings'].to_decimal())
                
                if not any(d['id'] == str(earning['branch'].id) for d in branches_total_earnings):
                    branches_total_earnings.append(
                        {
                            'id': str(earning['branch'].id),
                            'name': earning['branch'].name,
                            'totalEarnings': earning['earnings']
                        }
                    )
                else:
                    for x in branches_total_earnings:
                        if x['id'] == str(earning['branch'].id):
                            x['totalEarnings'] = Decimal128(x['totalEarnings'].to_decimal() + earning['earnings'].to_decimal())

    if branch_id != 'all':
        registrations = registrations.filter(branch=branch_id)

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)

    _table_data = []

    for registration in registrations:
        _table_data.append([
            registration.branch.name if registration.branch is not None else '',
            registration.full_name,
            registration.batch_number.number if registration.batch_number is not None else '',
            registration.schedule,
            "Full Payment" if registration.payment_mode == "full_payment" else "Installment",
        ])

    print(branches_total_earnings)

    for branch in branches_total_earnings:
        branch['totalEarnings'] = str(branch['totalEarnings'])

    response = {
        'draw': draw,
        'recordsTotal': registrations.count(),
        'recordsFiltered': registrations.count(),
        'data': _table_data,
        'totalEarnings': str(total_earnings),
        'totalSavings': str(total_savings),
        'branchesTotalEarnings': branches_total_earnings
    }

    return jsonify(response)