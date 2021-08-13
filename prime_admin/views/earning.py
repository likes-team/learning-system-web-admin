from flask_mongoengine import json
from prime_admin.globals import SECRETARYREFERENCE, get_date_now
from app.auth.models import User
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, Earning, Registration, Batch
from flask import redirect, url_for, request, current_app, flash, jsonify
from app import db
from datetime import datetime, timedelta
from bson.decimal128 import Decimal128, create_decimal128_context
import decimal
from mongoengine.queryset.visitor import Q



D128_CTX = create_decimal128_context()


@bp_lms.route('/earnings', methods=['GET'])
@login_required
def earnings():
    _table_columns = [
        'student_id','payment_id','Branch', 'Full Name', 'batch no.','fle', 'sle', 'schedule', 'remark', 'status','actions'
    ]

    _scripts = [
        {'lms.static': 'js/earnings.js'}
    ]

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
        marketers = User.objects(Q(branches__in=[str(current_user.branch.id)]) & Q(role__ne=SECRETARYREFERENCE))
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
        marketers = User.objects(id=current_user.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
        marketers = User.objects(id=current_user.id)
    else:
        branches = Branch.objects()
        batch_numbers = Batch.objects()
        marketers = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))

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
    print(contact_person_id)
    branch_id = request.args.get('branch')
    batch_no = request.args.get('batch_no')

    total_earnings = 0
    total_savings = 0
    total_earnings_claimed = 0
    total_savings_claimed = 0
    branches_total_earnings = []

    if contact_person_id == 'all':
        registrations = Registration.objects(status="registered").skip(start).limit(length)
        if current_user.role.name == "Secretary":
            contact_persons = User.objects(branches__in=[str(current_user.branch.id)])
        else:
            contact_persons = User.objects()

        with decimal.localcontext(D128_CTX):
            total_earnings = Decimal128('0.00')
            total_savings = Decimal128('0.00')
            total_earnings_claimed = Decimal128('0.00')
            total_savings_claimed = Decimal128('0.00')
            
            for contact_person in contact_persons:
                for earning in contact_person.earnings:
                    if earning.status is not None and earning.status == "for_approval":
                        total_earnings = Decimal128(total_earnings.to_decimal() + earning.earnings)
                        total_savings = Decimal128(total_savings.to_decimal() + earning.savings)
                        
                        if not any(d['id'] == str(earning.branch.id) for d in branches_total_earnings):
                            branches_total_earnings.append(
                                {
                                    'id': str(earning.branch.id),
                                    'name': earning.branch.name,
                                    'totalEarnings': earning.earnings
                                }
                            )
                        else:
                            for x in branches_total_earnings:
                                if x['id'] == str(earning['branch'].id):
                                    if type(x['totalEarnings']) == decimal.Decimal:
                                        x['totalEarnings'] = Decimal128(x['totalEarnings'] + earning.earnings)
                                    else:
                                        x['totalEarnings'] = Decimal128(x['totalEarnings'].to_decimal() + earning.earnings)
                    elif earning.status == "approved":
                        total_earnings_claimed = Decimal128(total_earnings_claimed.to_decimal() + earning.earnings)
                        total_savings_claimed = Decimal128(total_savings_claimed.to_decimal() + earning.savings)
    else:
        registrations = Registration.objects(contact_person=contact_person_id).filter(status="registered").skip(start).limit(length)
        contact_person = User.objects.get(id=contact_person_id)

        with decimal.localcontext(D128_CTX):
            total_earnings = Decimal128('0.00')
            total_savings = Decimal128('0.00')
            total_earnings_claimed = Decimal128('0.00')
            total_savings_claimed = Decimal128('0.00')

            for earning in contact_person.earnings:
                if earning.status is not None and earning.status == "for_approval":
                    total_earnings = Decimal128(total_earnings.to_decimal() + earning.earnings)
                    total_savings = Decimal128(total_savings.to_decimal() + earning.savings)
                    
                    if not any(d['id'] == str(earning.branch.id) for d in branches_total_earnings):
                        branches_total_earnings.append(
                            {
                                'id': str(earning.branch.id),
                                'name': earning.branch.name,
                                'totalEarnings': earning.earnings
                            }
                        )
                    else:
                        for x in branches_total_earnings:
                            if x['id'] == str(earning['branch'].id):
                                    if type(x['totalEarnings']) == decimal.Decimal:
                                        x['totalEarnings'] = Decimal128(x['totalEarnings'] + earning.earnings)
                                    else:
                                        x['totalEarnings'] = Decimal128(x['totalEarnings'].to_decimal() + earning.earnings)
                elif earning.status == "approved":
                    total_earnings_claimed = Decimal128(total_earnings_claimed.to_decimal() + earning.earnings)
                    total_savings_claimed = Decimal128(total_savings_claimed.to_decimal() + earning.savings)

    if branch_id != 'all':
        registrations = registrations.filter(branch=branch_id)

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)

    _table_data = []

    for registration in registrations:
        if registration.payment_mode == "full_payment":
            remarks = "Full Payment"
        elif registration.payment_mode == "premium":
            remarks = "Premium"
        elif registration.payment_mode == "installment":
            remarks = "Installment"
        elif registration.payment_mode == "full_payment_promo":
            remarks = "Full Payment - Promo"
        elif registration.payment_mode == "installment_promo":
            remarks = "Installment - Promo"
        elif registration.payment_mode == "premium_promo":
            remarks = "Premium - Promo"

        for payment in registration.payments:
            actions = ''
            status = ''

            if current_user.role.name == "Secretary" or current_user.role.name == "Admin":
                if payment.status == "for_approval":
                    actions = """
                        <button style="margin-bottom: 8px;" type="button" 
                            class="mr-2 btn-icon btn-icon-only btn btn-outline-info 
                            btn-approve-claim">Approve Claim</button>""" if not contact_person_id == 'all' else ''
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-info">FOR APPROVAL</div>"""
                elif payment.status is None:
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NOT YET CLAIM</div>"""
                elif payment.status == "approved":
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-success">CLAIMED/APPROVED</div>"""
            else:
                if registration.batch_number.start_date is None:
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NOT YET STARTED</div>"""
                else:
                    start_date = registration.batch_number.start_date + timedelta(days=3)
                    if payment.status == "for_approval":
                        status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-info">FOR APPROVAL</div>"""
                    elif payment.status is None:
                        if start_date.date() <= get_date_now().date():
                            actions = """<button style="margin-bottom: 8px;" type="button" class="mr-2 btn-icon 
                                btn-icon-only btn btn-outline-warning btn-claim">Claim</button>""" if not contact_person_id == 'all' else ''
                            status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-warning">FOR CLAIM</div>"""
                        else:
                            status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NOT YET CLAIM</div>"""
                    elif payment.status == "approved":
                        status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-success">CLAIMED/APPROVED</div>"""

            _table_data.append([
                str(registration.id),
                str(payment.id),
                registration.branch.name if registration.branch is not None else '',
                registration.full_name,
                registration.batch_number.number if registration.batch_number is not None else '',
                str(payment.earnings) if registration.fle is not None and not registration.fle == 0 else '',
                str(payment.earnings) if registration.sle is not None and not registration.sle == 0 else '',
                registration.schedule,
                remarks,
                status,
                actions
            ])

    for branch in branches_total_earnings:
        branch['totalEarnings'] = str(branch['totalEarnings'])

    response = {
        'draw': draw,
        'recordsTotal': registrations.count(),
        'recordsFiltered': registrations.count(),
        'data': _table_data,
        'totalEarnings': str(total_earnings),
        'totalSavings': str(total_savings),
        'totalEarningsClaimed': str(total_earnings_claimed),
        'totalSavingsClaimed': str(total_savings_claimed),
        'branchesTotalEarnings': branches_total_earnings
    }

    return jsonify(response)


@bp_lms.route('/api/claim-earning', methods=['POST'])
@login_required
def claim_earning():
    student_id = request.json['student_id']
    payment_id = request.json['payment_id']

    print("student id: ", student_id)
    print('payment_id: ', payment_id)
    student = Registration.objects.get(id=student_id)

    if student is None:
        return jsonify({'result': False})

    _payment_earning = 0

    for student_payment in student.payments:
        if student_payment.id == payment_id:
            student_payment.status = "for_approval"
            _payment_earning = student_payment.earnings

    contact_person = User.objects.get(id=current_user.id)

    try:
        for earning in contact_person.earnings:
            print(earning.payment_mode, earning.client)

            if earning.payment_mode == "profit_sharing":
                continue

            if earning.client.id == student.id:
                if earning.earnings == _payment_earning:
                    earning.status = "for_approval"
    
    except Exception as exc:
        pass
    
    student.save()
    contact_person.save()

    response = {
        'result': True
    }

    return jsonify(response)


@bp_lms.route('/api/approve-claim-earning', methods=['POST'])
@login_required
def approve_claim_earning():
    student_id = request.json['student_id']
    payment_id = request.json['payment_id']
    marketer_id = request.json['marketer_id']

    print("student id: ", student_id)
    print('payment_id: ', payment_id)
    print('contact person id: ', marketer_id)

    student = Registration.objects.get(id=student_id)

    if student is None:
        return jsonify({'result': False})

    _payment_earning = 0

    for student_payment in student.payments:
        if student_payment.id == payment_id:
            student_payment.status = "approved"
            _payment_earning = student_payment.earnings

    contact_person = User.objects.get(id=marketer_id)

    for earning in contact_person.earnings:
        if earning.client.id == student.id:
            if earning.earnings == _payment_earning:
                earning.status = "approved"

    student.save()
    contact_person.save()

    response = {
        'result': True
    }

    return jsonify(response)


@bp_lms.route('/api/get-profit-sharing-earnings/<string:partner_id>', methods=['GET'])
def get_profit_sharing(partner_id):
    if partner_id == 'all' or partner_id == '':
        return jsonify({'result': False})

    partner = User.objects.get(id=partner_id)

    total_earnings = 0
    branches_total_earnings = []

    with decimal.localcontext(D128_CTX):
        total_earnings = Decimal128('0.00')

        for earning in partner.earnings:
            if earning.payment_mode != "profit_sharing":
                continue

            total_earnings = Decimal128(total_earnings.to_decimal() + earning.earnings)
            
            if not any(d['id'] == str(earning.branch.id) for d in branches_total_earnings):
                branches_total_earnings.append(
                    {
                        'id': str(earning.branch.id),
                        'name': earning.branch.name,
                        'totalEarnings': earning.earnings
                    }
                )
            else:
                for x in branches_total_earnings:
                    if x['id'] == str(earning['branch'].id):
                            if type(x['totalEarnings']) == decimal.Decimal:
                                x['totalEarnings'] = Decimal128(x['totalEarnings'] + earning.earnings)
                            else:
                                x['totalEarnings'] = Decimal128(x['totalEarnings'].to_decimal() + earning.earnings)


    for branch in branches_total_earnings:
        branch['totalEarnings'] = str(branch['totalEarnings'])

    print(branches_total_earnings)

    response = {
        'result': True,
        'totalEarningsProfit': str(total_earnings),
        'branchesTotalEarningsProfit': branches_total_earnings
    }

    return jsonify(response)