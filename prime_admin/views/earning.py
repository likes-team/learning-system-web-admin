from bson.objectid import ObjectId
from flask_mongoengine import json
from prime_admin.globals import SECRETARYREFERENCE, convert_to_local, get_date_now
from app.auth.models import User
from app.auth.models import Earning as auth_user_earning
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, Earning, Payment, Registration, Batch
from flask import redirect, url_for, request, current_app, flash, jsonify
from app import mongo
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

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
        marketers = User.objects(Q(branches__in=[str(current_user.branch.id)]) & Q(role__ne=SECRETARYREFERENCE))
        template = 'lms/earnings_admin.html'
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
        marketers = User.objects(id=current_user.id)
        template = 'lms/earnings.html'
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
        marketers = User.objects(id=current_user.id)
        template = 'lms/earnings_admin.html'
    else:
        branches = Branch.objects()
        batch_numbers = Batch.objects()
        marketers = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))
        template = 'lms/earnings_admin.html'
        
    return admin_table(
        Earning,
        fields=[],
        table_data=[],
        table_columns=_table_columns,
        heading="",
        subheading='',
        title='Earnings',
        table_template=template,
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
    filter_status = request.args.get('status')
    
    print(start, length)

    total_earnings = 0
    total_savings = 0
    total_earnings_claimed = 0
    total_savings_claimed = 0
    branches_total_earnings = []
    
    if contact_person_id == 'all':
        registrations = Registration.objects(status="registered").order_by("-registration_date").order_by("registration_number").skip(start).limit(length)
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
                    if earning.payment_mode == "profit_sharing":
                        continue

                    # if earning.status is not None and earning.status == "for_approval":
                    if earning.status is None or earning.status == "for_approval":
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
        registrations = Registration.objects(contact_person=contact_person_id).order_by("-registration_date").order_by("registration_number").filter(status="registered").skip(start).limit(length)
        contact_person = User.objects.get(id=contact_person_id)

        with decimal.localcontext(D128_CTX):
            total_earnings = Decimal128('0.00')
            total_savings = Decimal128('0.00')
            total_earnings_claimed = Decimal128('0.00')
            total_savings_claimed = Decimal128('0.00')

            for earning in contact_person.earnings:
                # if earning.status is not None and earning.status == "for_approval":
                if earning.payment_mode == "profit_sharing":
                    continue

                if earning.status is None or earning.status == "for_approval":
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

    total_records = registrations.count()

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
            # total_records += 1
            actions = ''
            status = ''

            if filter_status != 'all':
                if filter_status == "none":
                    filter_status = None 
                if payment.status != filter_status:
                    continue

            if current_user.role.name == "Secretary" or current_user.role.name == "Admin":
                if payment.status == "for_approval":
                    actions = """
                        <button style="margin-bottom: 8px;" type="button" 
                            class="mr-2 btn-icon btn-icon-only btn btn-outline-info 
                            btn-approve-claim">Approve Claim</button>""" if not contact_person_id == 'all' else ''
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-info">FOR APPROVAL</div>"""
                elif payment.status is None:
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NO REQUEST YET</div>"""
                elif payment.status == "approved":
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-success">RELEASED</div>"""
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
                                btn-icon-only btn btn-outline-warning btn-claim">Request for Claim</button>""" if not contact_person_id == 'all' else ''
                            status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-warning">FOR CLAIM</div>"""
                        else:
                            status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NO REQUEST YET</div>"""
                    elif payment.status == "approved":
                        status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-success">RELEASED</div>"""

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

    filtered_records = len(_table_data)

    print("total_records: ", total_records)
    print("filtered_records: ", filtered_records)

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': _table_data,
        'totalEarnings': str(total_earnings),
        'totalSavings': str(total_savings),
        'totalEarningsClaimed': str(total_earnings_claimed),
        'totalSavingsClaimed': str(total_savings_claimed),
        'branchesTotalEarnings': branches_total_earnings
    }

    return jsonify(response)


@bp_lms.route('/branches/<string:branch_id>/earnings/total')
def get_branch_total_earnings(branch_id):
    total_earnings = 0
    total_savings = 0
    total_earnings_claimed = 0
    total_savings_claimed = 0
    total_nyc = 0
    branches_total_earnings = []
    
    if current_user.role.name == "Secretary":
        contact_persons = User.objects(branches__in=[str(current_user.branch.id)])
    else:
        if branch_id == "all":
            contact_persons = User.objects()
        else:
            contact_persons = User.objects(branches__in=[branch_id])

    with decimal.localcontext(D128_CTX):
        total_earnings = Decimal128('0.00')
        total_savings = Decimal128('0.00')
        total_earnings_claimed = Decimal128('0.00')
        total_savings_claimed = Decimal128('0.00')
        total_nyc = Decimal128('0.00')
        
        contact_person: User
        for contact_person in contact_persons:
            earning: Payment
            for earning in contact_person.earnings:
                try:
                    print("TESTESTSET")
                    if current_user.role.name == "Secretary" and str(earning.client.branch.id) != str(current_user.branch.id):
                        continue
                    

                    if earning.payment_mode == "profit_sharing":
                        continue

                    # if earning.status is not None and earning.status == "for_approval":
                    if earning.status == "for_approval":
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
                    elif earning.status is None:
                        total_nyc = Decimal128(total_nyc.to_decimal() + earning.earnings)
                    
                    elif earning.status == "approved":
                        total_earnings_claimed = Decimal128(total_earnings_claimed.to_decimal() + earning.earnings)
                        total_savings_claimed = Decimal128(total_savings_claimed.to_decimal() + earning.savings)
                except Exception as err:
                    continue

    for branch in branches_total_earnings:
        branch['totalEarnings'] = str(branch['totalEarnings'])

    response = {
        'totalEarnings': str(total_earnings),
        'totalSavings': str(total_savings),
        'totalEarningsClaimed': str(total_earnings_claimed),
        'totalSavingsClaimed': str(total_savings_claimed),
        'totalNYC': str(total_nyc),
        'branchesTotalEarnings': branches_total_earnings
    }

    return jsonify(response)

@bp_lms.route('/marketers/<string:marketer_id>/earnings/total')
def get_marketer_total_earnings(marketer_id):
    total_earnings = 0
    total_savings = 0
    total_earnings_claimed = 0
    total_savings_claimed = 0
    total_nyc = 0
    branches_total_earnings = []
    
    marketer = User.objects.get(id=marketer_id)

    with decimal.localcontext(D128_CTX):
        total_earnings = Decimal128('0.00')
        total_savings = Decimal128('0.00')
        total_earnings_claimed = Decimal128('0.00')
        total_savings_claimed = Decimal128('0.00')
        total_nyc = Decimal128('0.00')
        
        marketer: User
        earning: Payment
        for earning in marketer.earnings:
            try:
                if current_user.role.name == "Secretary" and str(earning.client.branch.id) != str(current_user.branch.id):
                    continue
                
                if earning.payment_mode == "profit_sharing":
                    continue

                # if earning.status is not None and earning.status == "for_approval":
                if earning.status == "for_approval":
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
                elif earning.status is None:
                    total_nyc = Decimal128(total_nyc.to_decimal() + earning.earnings)
                
                elif earning.status == "approved":
                    total_earnings_claimed = Decimal128(total_earnings_claimed.to_decimal() + earning.earnings)
                    total_savings_claimed = Decimal128(total_savings_claimed.to_decimal() + earning.savings)
            except Exception as err:
                continue

    for branch in branches_total_earnings:
        branch['totalEarnings'] = str(branch['totalEarnings'])

    response = {
        'totalEarnings': str(total_earnings),
        'totalSavings': str(total_savings),
        'totalEarningsClaimed': str(total_earnings_claimed),
        'totalSavingsClaimed': str(total_savings_claimed),
        'totalNYC': str(total_nyc),
        'branchesTotalEarnings': branches_total_earnings
    }

    return jsonify(response)


@bp_lms.route('/branches/<string:branch_id>/marketers/<string:marketer_id>/earnings')
def get_marketer_earnings(branch_id, marketer_id):
    print(marketer_id)
    total_earnings = 0
    total_savings = 0
    
    data = []
    
    marketer: User = User.objects.get(id=marketer_id)

    with decimal.localcontext(D128_CTX):
        total_earnings = Decimal128('0.00')
        total_savings = Decimal128('0.00')
        
        earning: auth_user_earning
        for earning in marketer.earnings:
            try:
                if earning.payment_mode == "profit_sharing":
                    continue

                if earning.status == "for_approval":
                    total_earnings = Decimal128(total_earnings.to_decimal() + earning.earnings)
                    total_savings = Decimal128(total_savings.to_decimal() + earning.savings)
                    student: Registration = Registration.objects.get(id=earning.client.id)
                    
                    if str(student.branch.id) != branch_id:
                        continue
                    
                    if earning.payment_mode == "full_payment":
                            remarks = "Full Payment"
                    elif earning.payment_mode == "premium":
                        remarks = "Premium"
                    elif earning.payment_mode == "installment":
                        remarks = "Installment"
                    elif earning.payment_mode == "full_payment_promo":
                        remarks = "Full Payment - Promo"
                    elif earning.payment_mode == "installment_promo":
                        remarks = "Installment - Promo"
                    elif earning.payment_mode == "premium_promo":
                        remarks = "Premium - Promo"
                        
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-info">FOR APPROVAL</div>"""
                        
                    data.append([
                        str(earning.client.id),
                        str(earning.payment_id),
                        marketer.full_name,
                        student.full_name,
                        student.batch_number.number if student.batch_number is not None else '',
                        str(earning.earnings),
                        student.schedule,
                        remarks,
                        status,
                    ])
            except Exception as err:
                continue
                
    response = {
        'data': data,
        'totalEarnings': str(total_earnings),
        'totalSavings': str(total_savings),
    }

    return jsonify(response)


@bp_lms.route('/api/claim-earning', methods=['POST'])
@login_required
def claim_earning():
    student_id = request.json['student_id']
    payment_id = request.json['payment_id']

    print("student id: ", student_id)
    print('payment_id: ', payment_id)

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            mongo.db.lms_registrations.update_one(
                {"_id": ObjectId(student_id),
                "payments._id": ObjectId(payment_id)},
                {"$set": {
                    "payments.$.status": "for_approval"
                }}, session=session)

            mongo.db.auth_users.update_one(
                {"_id": current_user.id,
                "earnings.payment_id": payment_id
                },
                {"$set": {
                    "earnings.$.payment_id": ObjectId(payment_id),
                    "earnings.$.status": "for_approval"
                }}, session=session)

            mongo.db.auth_users.update_one(
                {"_id": current_user.id,
                "earnings.payment_id": ObjectId(payment_id)
                },
                {"$set": {
                    "earnings.$.payment_id": ObjectId(payment_id),
                    "earnings.$.status": "for_approval"
                }}, session=session)

            mongo.db.auth_users.update_one(
                {"_id": current_user.id,
                "earnings.payment": ObjectId(payment_id)
                },
                {"$set": {
                    "earnings.$.payment_id": ObjectId(payment_id),
                    "earnings.$.status": "for_approval"
                }}, session=session)
            
            current_user_details =  mongo.db.auth_users.find_one({"_id": current_user.id})

            mongo.db.lms_system_transactions.insert_one({
                "_id": ObjectId(),
                "date": get_date_now(),
                "current_user": current_user.id,
                "description": current_user_details['fname'] + "- Request for claim",
                "from_module": "Earnings"
            }, session=session)

            response = {
                'result': True
            }

    return jsonify(response)


@bp_lms.route('/branches/<string:branch_id>/marketers/<string:marketer_id>/earnings/approve-earnings', methods=['POST'])
def approve_marketer_earnings(branch_id, marketer_id):
    password = request.json['password']
    print("password: ", password)
    if not current_user.check_password(password):
        return jsonify({
            'status': 'error',
            'message': "Invalid password!"
        }), 500
    
    try:
        marketer: User = User.objects.get(id=marketer_id)

        with mongo.cx.start_session() as session:
            with session.start_transaction():
                with decimal.localcontext(D128_CTX):
                    earning: auth_user_earning
                    for earning in marketer.earnings:
                        if earning.payment_mode == "profit_sharing":
                            continue

                        if earning.status == "for_approval":
                            student: Registration = Registration.objects.get(id=earning.client.id)
                            
                            if str(student.branch.id) != branch_id:
                                continue
                            
                            mongo.db.lms_registrations.update_one(
                            {"_id": earning.client.id,
                            "payments._id": ObjectId(earning.payment_id)},
                            {"$set": {
                                "payments.$.status": "approved"
                            }}, session=session)

                            mongo.db.auth_users.update_one(
                                {"_id": marketer.id,
                                "earnings.payment_id": earning.payment_id
                                },
                                {"$set": {
                                    "earnings.$.status": "approved"
                                }}, session=session)

                            mongo.db.auth_users.update_one(
                                {"_id": marketer.id,
                                "earnings.payment_id": ObjectId(earning.payment_id)
                                },
                                {"$set": {
                                    "earnings.$.status": "approved"
                                }}, session=session)

                            mongo.db.auth_users.update_one(
                                {"_id": marketer.id,
                                "earnings.payment": ObjectId(earning.payment_id)
                                },
                                {"$set": {
                                    "earnings.$.status": "approved"
                                }}, session=session)

                            mongo.db.lms_system_transactions.insert_one({
                                "_id": ObjectId(),
                                "date": get_date_now(),
                                "current_user": current_user.id,
                                "description": "Approve claim -" + marketer.fname,
                                "from_module": "Earnings"
                            }, session=session)

        response = {
            'status': 'success',
            'message': ""
        }
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': "Please refresh the page then try again!"
        }), 500


@bp_lms.route('/api/approve-claim-earning', methods=['POST'])
@login_required
def approve_claim_earning():
    student_id = request.json['student_id']
    payment_id = request.json['payment_id']
    marketer_id = request.json['marketer_id']

    print("student id: ", student_id)
    print('payment_id: ', payment_id)
    print('contact person id: ', marketer_id)

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            with decimal.localcontext(D128_CTX):
                mongo.db.lms_registrations.update_one(
                {"_id": ObjectId(student_id),
                "payments._id": ObjectId(payment_id)},
                {"$set": {
                    "payments.$.status": "approved"
                }}, session=session)

                mongo.db.auth_users.update_one(
                    {"_id": ObjectId(marketer_id),
                    "earnings.payment_id": payment_id
                    },
                    {"$set": {
                        "earnings.$.status": "approved"
                    }}, session=session)

                mongo.db.auth_users.update_one(
                    {"_id": ObjectId(marketer_id),
                    "earnings.payment_id": ObjectId(payment_id)
                    },
                    {"$set": {
                        "earnings.$.status": "approved"
                    }}, session=session)

                mongo.db.auth_users.update_one(
                    {"_id": ObjectId(marketer_id),
                    "earnings.payment": ObjectId(payment_id)
                    },
                    {"$set": {
                        "earnings.$.status": "approved"
                    }}, session=session)

                marketer_details =  mongo.db.auth_users.find_one({"_id": ObjectId(marketer_id)})

                payment_details = mongo.db.auth_users.find_one(
                    {"_id": ObjectId(marketer_id),
                    "earnings.payment": ObjectId(payment_id)
                    }, session=session)

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": "Approve claim -" + marketer_details['fname'],
                    "from_module": "Earnings"
                }, session=session)
                
                response = {
                    'result': True
                }

    return jsonify(response)


@bp_lms.route('/api/get-earning-transaction-history', methods=['GET'])
def get_earning_transaction_history():
    _transaction_data = []

    transactions = mongo.db.lms_system_transactions.find({"from_module": "Earnings"})
    for trans in transactions:
        _transaction_data.append((
            convert_to_local(trans["date"]),
            trans['description']
        ))

    response = {
        'data': _transaction_data
    }
    return jsonify(response)