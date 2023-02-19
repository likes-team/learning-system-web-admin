import decimal
import pytz
import pymongo
from datetime import timedelta
from xml.dom.minidom import getDOMImplementation
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128, create_decimal128_context
from mongoengine.queryset.visitor import Q
from flask import request, jsonify, render_template
from flask_login import login_required, current_user
from flask_weasyprint import HTML, render_pdf
from app import mongo
from app.auth.models import User
from app.auth.models import Earning as auth_user_earning
from app.admin.templating import admin_render_template
from config import TIMEZONE
from prime_admin import bp_lms
from prime_admin.models import Branch, Earning, Payment, Registration, Batch
from prime_admin.globals import SECRETARYREFERENCE, convert_to_local, get_date_now
from prime_admin.helpers import Earning as earning_helper
from prime_admin.services.payment import PaymentService
from prime_admin.services.earning import EarningService
from prime_admin.services.saving import SavingService
from prime_admin.helpers.query_filter import PaymentQueryFilter
from prime_admin.models_v2 import PaymentV2



D128_CTX = create_decimal128_context()


@bp_lms.route('/earnings', methods=['GET'])
@login_required
def earnings():
    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
        marketers = User.objects(Q(branches__in=[str(current_user.branch.id)]) & Q(role__ne=SECRETARYREFERENCE)).order_by('fname')
        template = 'lms/earnings/admin.html'
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
        marketers = User.objects(id=current_user.id).order_by('fname')
        template = 'lms/earnings/marketer.html'
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
        marketers = User.objects(id=current_user.id).order_by('fname')
        template = 'lms/earnings/marketer.html'
    elif current_user.role.name == "Admin":
        branches = Branch.objects()
        batch_numbers = Batch.objects()
        marketers = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False)).order_by('fname')
        template = 'lms/earnings/admin.html'
    return admin_render_template(
        Earning,
        template,
        'learning_management',
        title='Earnings',
        marketers=marketers,
        branches=branches,
        batch_numbers=batch_numbers,
    )


@bp_lms.route('/dtbl/earnings/members')
def get_dtbl_earnings_members():
    draw = request.args.get('draw')
    contact_person_id = request.args.get('contact_person')
    query_filter = PaymentQueryFilter.from_request(request)
    service = PaymentService.find_payments(query_filter)
    payments = service.get_data()
    _table_data = []
    
    for payment in payments:
        payment: PaymentV2
        status = ''
        actions = ''
        payment_status = payment.get_status()
        if current_user.role.name == "Secretary" or current_user.role.name == "Admin":
            if payment_status == "for_approval":
                actions = """
                    <button style="margin-bottom: 8px;" type="button" 
                        class="mr-2 btn-icon btn-icon-only btn btn-outline-info 
                        btn-approve-claim">Approve Claim</button>""" if not contact_person_id == 'all' else ''
                status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-info">FOR APPROVAL</div>"""
            elif payment_status is None:
                status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NO REQUEST YET</div>"""
            elif payment_status == "approved":
                status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-success">RELEASED</div>"""
        else:
            if payment.student.batch_no.get_start_date() is None:
                status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NOT YET STARTED</div>"""
            else:
                start_date = payment.student.batch_no.get_start_date() + timedelta(days=3)
                if payment_status == "for_approval":
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-info">FOR APPROVAL</div>"""
                elif payment_status is None:
                    if start_date.date() <= get_date_now().date():
                        actions = """<button style="margin-bottom: 8px;" type="button" class="mr-2 btn-icon 
                            btn-icon-only btn btn-outline-warning btn-claim">Request for Claim</button>""" if not contact_person_id == 'all' else ''
                        status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-warning">FOR CLAIM</div>"""
                    else:
                        status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-secondary">NO REQUEST YET</div>"""
                elif payment_status == "approved":
                    status = """<div class="text-center mb-2 mr-2 badge badge-pill badge-success">RELEASED</div>"""
        _table_data.append([
            str(payment.student.get_id()),
            str(payment.get_id()),
            payment.branch.get_name(),
            payment.student.get_full_name(),
            payment.student.batch_no.get_no(),
            payment.get_earnings(currency=True) if payment.student.get_fle() is not None and not payment.student.get_fle() <= 0 else '',
            payment.get_earnings(currency=True) if payment.student.get_sle() is not None and not payment.student.get_sle() <= 0 else '',
            payment.student.schedule,
            payment.student.get_payment_mode(),
            status,
            actions
        ])

    filtered_records = service.total_filtered()
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': filtered_records,
        'data': _table_data
    }
    return jsonify(response)


@bp_lms.route('/marketers/<string:marketer_id>/payment-records/dt')
def fetch_marketer_payment_records_dt(marketer_id):
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    
    if marketer_id == '':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
        }
        return jsonify(response)
    
    query = list(mongo.db.lms_fund_wallet_transactions.aggregate([
        {"$match": {
            'type': 'expenses',
            'category': 'salary_and_rebates',
            'description': marketer_id,
        }},
        {"$skip": start},
        {"$limit": length},
        {"$sort": {
            'created_at': pymongo.DESCENDING
        }}
    ]))
    
    filtered_records = len(query)
    
    total_records = len(list(mongo.db.lms_fund_wallet_transactions.aggregate([
        {"$match": {
            'type': 'expenses',
            'category': 'salary_and_rebates',
            'description': marketer_id,
        }},
        {"$sort": {
            'created_at': pymongo.DESCENDING
        }}
    ])))

    data = []

    for record in query:
        data.append([
            str(record['_id']),
            convert_to_local(record['date']),
            record['account_no'],
            '',
            '',
            str(record['total_amount_due']),
            'PAID',
            '',
        ])
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': data
    }
    return jsonify(response)


@bp_lms.route('/marketers/<string:marketer_id>/earnings/total')
def get_marketer_total_earnings(marketer_id):
    earning_service = EarningService.find_earnings(marketer_id)
    saving_service = SavingService.find_savings(marketer_id)
    total_earnings = earning_service.get_total_earnings(currency=True)
    total_savings = saving_service.get_total_savings(currency=True)
    total_earnings_claimed = earning_service.get_total_earnings_approved(currency=True)
    total_savings_claimed = saving_service.get_total_savings_approved(currency=True)
    total_nyc = earning_service.get_total_nyc(currency=True)
    branches_total_earnings = earning_service.get_branch_total_earnings()
    response = {
        'totalEarnings': total_earnings,
        'totalSavings': total_savings,
        'totalEarningsClaimed': total_earnings_claimed,
        'totalSavingsClaimed': total_savings_claimed,
        'totalNYC': total_nyc,
        'branchesTotalEarnings': branches_total_earnings
    }
    return jsonify(response)


@bp_lms.route('/branches/<string:branch_id>/marketers/<string:marketer_id>/earnings')
def get_marketer_earnings(branch_id, marketer_id):
    total_earnings = 0
    total_savings = 0
    
    data = []
    
    marketer: User = User.objects.get(id=marketer_id)

    with decimal.localcontext(D128_CTX):
        total_earnings = Decimal128('0.00')
        total_savings = Decimal128('0.00')
        
        earning: auth_user_earning
        for earning in marketer.earnings:
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
    response = {
        'data': data,
        'totalEarnings': str(total_earnings),
        'totalSavings': str(total_savings),
    }
    return jsonify(response)


@bp_lms.route('/api/claim-earning', methods=['POST'])
@login_required
def claim_earning():
    payment_id = request.json['payment_id']
    earning_helper.request_for_claim(payment_id)
    response = {
        'result': True
    }
    return jsonify(response)


@bp_lms.route('/branches/<string:branch_id>/marketers/<string:marketer_id>/earnings/approve-earnings', methods=['POST'])
def approve_marketer_earnings(branch_id, marketer_id):
    password = request.json['password']
    if not current_user.check_password(password):
        return jsonify({
            'status': 'error',
            'message': "Invalid password!"
        }), 500
    
    earning_helper.approve_marketer_requests(marketer_id, branch_id)
    response = {
        'status': 'success',
        'message': ""
    }
    return jsonify(response), 200


@bp_lms.route('/api/approve-claim-earning', methods=['POST'])
@login_required
def approve_claim_earning():
    """(DEPRECATED)

    Returns:
        _type_: _description_
    """
    pass
    # student_id = request.json['student_id']
    # payment_id = request.json['payment_id']
    # marketer_id = request.json['marketer_id']

    # with mongo.cx.start_session() as session:
    #     with session.start_transaction():
    #         with decimal.localcontext(D128_CTX):
    #             mongo.db.lms_registrations.update_one(
    #             {"_id": ObjectId(student_id),
    #             "payments._id": ObjectId(payment_id)},
    #             {"$set": {
    #                 "payments.$.status": "approved"
    #             }}, session=session)

    #             mongo.db.auth_users.update_one(
    #                 {"_id": ObjectId(marketer_id),
    #                 "earnings.payment_id": payment_id
    #                 },
    #                 {"$set": {
    #                     "earnings.$.status": "approved"
    #                 }}, session=session)

    #             mongo.db.auth_users.update_one(
    #                 {"_id": ObjectId(marketer_id),
    #                 "earnings.payment_id": ObjectId(payment_id)
    #                 },
    #                 {"$set": {
    #                     "earnings.$.status": "approved"
    #                 }}, session=session)

    #             mongo.db.auth_users.update_one(
    #                 {"_id": ObjectId(marketer_id),
    #                 "earnings.payment": ObjectId(payment_id)
    #                 },
    #                 {"$set": {
    #                     "earnings.$.status": "approved"
    #                 }}, session=session)

    #             marketer_details =  mongo.db.auth_users.find_one({"_id": ObjectId(marketer_id)})

    #             payment_details = mongo.db.auth_users.find_one(
    #                 {"_id": ObjectId(marketer_id),
    #                 "earnings.payment": ObjectId(payment_id)
    #                 }, session=session)

    #             mongo.db.lms_system_transactions.insert_one({
    #                 "_id": ObjectId(),
    #                 "date": get_date_now(),
    #                 "current_user": current_user.id,
    #                 "description": "Approve claim -" + marketer_details['fname'],
    #                 "from_module": "Earnings"
    #             }, session=session)
                
    #             response = {
    #                 'result': True
    #             }

    # return jsonify(response)


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


@bp_lms.route('/payslip.pdf')
def print_payslip():
    marketer_id = request.args.get('marketer_id')

    marketer: User = User.objects.get(id=marketer_id)

    total_earnings = 0
    branches_earnings = []

    with decimal.localcontext(D128_CTX):
        total_earnings = Decimal128('0.00')
        total_savings = Decimal128('0.00')

        for earning in marketer.earnings:
            if earning.payment_mode == "profit_sharing":
                continue

            if earning.status != "for_approval":
                continue

            total_earnings = Decimal128(total_earnings.to_decimal() + earning.earnings)
            total_savings = Decimal128(total_savings.to_decimal() + earning.savings)
            
            if not any(d['id'] == str(earning.branch.id) for d in branches_earnings):
                branches_earnings.append(
                    {
                        'id': str(earning.branch.id),
                        'name': earning.branch.name,
                        'totalEarnings': earning.earnings,
                        'students': []
                    } 
                )
            else:
                for x in branches_earnings:
                    if x['id'] == str(earning['branch'].id):
                            if type(x['totalEarnings']) == decimal.Decimal:
                                x['totalEarnings'] = Decimal128(x['totalEarnings'] + earning.earnings)
                            else:
                                x['totalEarnings'] = Decimal128(x['totalEarnings'].to_decimal() + earning.earnings)

            for x in branches_earnings:
                if x['id'] != str(earning['branch'].id):
                    continue
                
                x['students'].append({
                    'name': earning.client.full_name,
                    'earning': earning.earnings
                })

    
    local_datetime = get_date_now().replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    date_now = local_datetime.strftime("%B %d, %Y")
    
    html = render_template(
            'lms/earnings/pdf_payslip.html',
            branches_earnings=branches_earnings,
            marketer=marketer,
            date_now=date_now,
            total_earnings=total_earnings
            )

    return render_pdf(HTML(string=html))


@bp_lms.route('/available-earnings.pdf')
def print_available_earnings():
    marketers = User.objects()

    total_earnings = 0
    marketer_earnings = []

    with decimal.localcontext(D128_CTX):
        total_earnings = Decimal128('0.00')
        total_savings = Decimal128('0.00')

        marketer: User
        for marketer in marketers:
            for earning in marketer.earnings:
                if earning.payment_mode == "profit_sharing":
                    continue

                if earning.status != "for_approval":
                    continue

                total_earnings = Decimal128(total_earnings.to_decimal() + earning.earnings)
                total_savings = Decimal128(total_savings.to_decimal() + earning.savings)
                
                if not any(d['id'] == str(marketer.id) for d in marketer_earnings):
                    marketer_earnings.append(
                        {
                            'id': str(marketer.id),
                            'name': marketer.full_name,
                            'totalEarnings': earning.earnings,
                        }
                    )
                else:
                    for x in marketer_earnings:
                        if x['id'] == str(marketer.id):
                                if type(x['totalEarnings']) == decimal.Decimal:
                                    x['totalEarnings'] = Decimal128(x['totalEarnings'] + earning.earnings)
                                else:
                                    x['totalEarnings'] = Decimal128(x['totalEarnings'].to_decimal() + earning.earnings)
    
    local_datetime = get_date_now().replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    date_now = local_datetime.strftime("%B %d, %Y")
    
    html = render_template(
            'lms/earnings/pdf_available_earnings.html',
            marketer_earnings=marketer_earnings,
            date_now=date_now,
            total_earnings=total_earnings
            )

    return render_pdf(HTML(string=html))