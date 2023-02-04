import decimal
import os
import glob
import io
from shutil import copyfile
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from bson.objectid import ObjectId
from mongoengine.queryset.visitor import Q
import pytz
from prime_admin.globals import convert_to_utc, get_date_now, get_sales_today_date
from random import uniform
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, Registration, Member
from flask import json, redirect, url_for, request, current_app, flash, jsonify, render_template, send_from_directory, send_file
from app import mongo
from datetime import datetime
from bson.decimal128 import Decimal128, create_decimal128_context
from app.auth.models import Earning, User
from flask_weasyprint import HTML, render_pdf
from config import TIMEZONE
from prime_admin.helpers import Payment



D128_CTX = create_decimal128_context()


@bp_lms.route('/members', methods=['GET'])
@login_required
def members():
    _table_columns = [
        'id', 'date', 'registration','name of student', 'batch no.', 'branch', 'schedule', 'remark',
        'amount','balance', 'paid/not paid', 'Deposit','contact person', 'book', 'Uniform', 'cashier', 'actions'
        ]

    fields = []

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
    elif current_user.role.name == "Admin":
        branches = Branch.objects
        batch_numbers = Batch.objects()
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects()
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects()        

    settings = mongo.db.lms_configurations.find_one({'name': 'agreement_form_pdf_setting'})['settings']
    payment_rules = settings.get('payment_rules')
    mode_of_payment = settings.get('mode_of_payment')
    refunds_and_withdrawals = settings.get('refunds_and_withdrawals')
    print(payment_rules)
    return admin_table(
        Member,
        fields=fields,
        table_data=[],
        table_columns=_table_columns,
        heading='Student Records',
        subheading="",
        title='Student Records',
        table_template="lms/student_records.html",
        branches=branches,
        batch_numbers=batch_numbers,
        schedules=['WDC', 'SDC'],
        payment_rules=payment_rules,
        mode_of_payment=mode_of_payment,
        refunds_and_withdrawals=refunds_and_withdrawals
        )


@bp_lms.route('/dtbl/members')
def get_dtbl_members():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    branch_id = request.args.get('branch')
    batch_no = request.args.get('batch_no')
    schedule = request.args.get('schedule')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    payment_status = request.args.get('payment_status')
    payment_mode = request.args.get('payment_mode')
    
    sales_today = 0
    # TODO: add promos
    installment_registrations = Registration.objects().filter(Q(payment_mode='installment') | Q(payment_mode="installment_promo")).filter(is_archived__ne=True)
    full_payment_registrations = Registration.objects().filter(Q(payment_mode='full_payment') | Q(payment_mode="full_payment_promo")).filter(is_archived__ne=True)
    premium_payment_registrations = Registration.objects().filter(Q(payment_mode='premium') | Q(payment_mode='premium_promo')).filter(is_archived__ne=True)

    print(get_sales_today_date())
    print(get_date_now())

    if branch_id != 'all':
        registrations = Registration.objects(branch=branch_id).filter(Q(status='registered') | Q(status='refunded')).filter(is_archived__ne=True).order_by("-registration_date").skip(start).limit(length)
        sales_today = registrations.filter(registration_date__gte=get_date_now().date()).sum('amount')

        installment_registrations = installment_registrations.filter(branch=branch_id)
        full_payment_registrations = full_payment_registrations.filter(branch=branch_id)
        premium_payment_registrations = premium_payment_registrations.filter(branch=branch_id)
    else:
        if current_user.role.name == "Marketer":
            registrations = Registration.objects(Q(status='registered') | Q(status='refunded')).filter(branch__in=current_user.branches).filter(is_archived__ne=True).order_by("-registration_date").skip(start).limit(length)
            sales_today = registrations.filter(registration_date__gte=get_date_now().date()).filter(branch__in=current_user.branches).sum('amount')
        elif current_user.role.name == "Partner":
            registrations = Registration.objects(Q(status='registered') | Q(status='refunded')).filter(branch__in=current_user.branches).filter(is_archived__ne=True).order_by("-registration_date").skip(start).limit(length)
        else:
            registrations = Registration.objects(Q(status='registered') | Q(status='refunded')).filter(is_archived__ne=True).order_by("-registration_date").skip(start).limit(length)
            query_sales_today = list(mongo.db.lms_registration_payments.aggregate([
                {"$match": {
                    "date": {"$gte": get_sales_today_date().replace(hour=0, minute=0), "$lte": get_sales_today_date().replace(hour=23, minute=59)}
                    }
                },
                {"$group": {
                    "_id": None,
                    'sales_today': {"$sum": "$amount"}
                }}
            ]))
            if len(query_sales_today) > 0:
                sales_today = query_sales_today[0].get('sales_today')
            else:
                sales_today = 0.00
            

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)
        installment_registrations = installment_registrations.filter(batch_number=batch_no)
        full_payment_registrations = full_payment_registrations.filter(batch_number=batch_no)
        premium_payment_registrations = premium_payment_registrations.filter(batch_number=batch_no)

    if schedule != 'all':
        registrations = registrations.filter(schedule=schedule)
        installment_registrations = installment_registrations.filter(schedule=schedule)
        full_payment_registrations = full_payment_registrations.filter(schedule=schedule)
        premium_payment_registrations = premium_payment_registrations.filter(schedule=schedule)

    if search_value != "":
        registrations = registrations.filter(lname__icontains=search_value)
        installment_registrations = installment_registrations.filter(lname__icontains=search_value)
        full_payment_registrations = full_payment_registrations.filter(lname__icontains=search_value)
        premium_payment_registrations = premium_payment_registrations.filter(lname__icontains=search_value)

    if date_from !="":
        registrations = registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))
        installment_registrations = installment_registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))
        full_payment_registrations = full_payment_registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))
        premium_payment_registrations = premium_payment_registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))

    if date_to != "":
        registrations = registrations.filter(registration_date__lte=convert_to_utc(date_to))
        installment_registrations = installment_registrations.filter(registration_date__lte=convert_to_utc(date_to))
        full_payment_registrations = full_payment_registrations.filter(registration_date__lte=convert_to_utc(date_to))
        premium_payment_registrations = premium_payment_registrations.filter(registration_date__lte=convert_to_utc(date_to))

    if payment_status == 'PAID':
        registrations = registrations.filter(balance__lte=0)
        installment_registrations = installment_registrations.filter(balance__lte=0)
        full_payment_registrations = full_payment_registrations.filter(balance__lte=0)
        premium_payment_registrations = premium_payment_registrations.filter(balance__lte=0)
    elif payment_status == "NOT PAID":
        registrations = registrations.filter(balance__gt=0)
        installment_registrations = installment_registrations.filter(balance__gt=0)
        full_payment_registrations = full_payment_registrations.filter(balance__gt=0)
        premium_payment_registrations = premium_payment_registrations.filter(balance__gt=0)
    elif payment_status == "REFUNDED":
        registrations = registrations.filter(payment_mode='refund')
        installment_registrations = installment_registrations.filter(payment_mode='refund')
        full_payment_registrations = full_payment_registrations.filter(payment_mode='refund')
        premium_payment_registrations = premium_payment_registrations.filter(payment_mode='refund')
    
    if payment_mode != "all":
        registrations = registrations.filter(payment_mode=payment_mode)
        installment_registrations = installment_registrations.filter(payment_mode=payment_mode)
        full_payment_registrations = full_payment_registrations.filter(payment_mode=payment_mode)
        premium_payment_registrations = premium_payment_registrations.filter(payment_mode=payment_mode)

    _table_data = []

    for registration in registrations:
        books = ""
        uniforms = ""

        actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#editModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-success btn-edit"><i class="pe-7s-wallet btn-icon-wrapper"> </i></button>
            <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""

        paid = 'NOT PAID'

        if registration.balance <= 0.00:
            paid = 'PAID'
        
        if current_user.role.name in ['Secretary', 'Admin', 'Partner']:
            if registration.payment_mode == "premium" or registration.payment_mode == "premium_promo":
                actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
            elif registration.payment_mode == "full_payment" or registration.payment_mode == "full_payment_promo":
                actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#upgradeModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-warning btn-upgrade"><i class="pe-7s-upload btn-icon-wrapper"> </i></button>
                <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
            elif (registration.payment_mode == "installment" or registration.payment_mode == "installment_promo") and registration.balance <= 0.00:
                actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#upgradeModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-warning btn-upgrade"><i class="pe-7s-upload btn-icon-wrapper"> </i></button>
                    <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
        else: # Marketers
            actions = ""

        branch = registration.branch
        contact_person = registration.contact_person

        if registration.books:
            books = "None"

            if registration.books['volume1']:
                books = "Vol. 1"
            if registration.books['volume2']:
                books += " Vol. 2"
            if registration.books['book_none']:
                books = "None"
        else:
            books = "None"

        if registration.uniforms:
            uniforms = "None"

            if registration.uniforms['uniform_none']:
                uniforms = "None"
            elif registration.uniforms['uniform_xs']:
                uniforms = "XS"
            elif registration.uniforms['uniform_s']:
                uniforms = "S"
            elif registration.uniforms['uniform_m']:
                uniforms = "M"
            elif registration.uniforms['uniform_l']:
                uniforms = "L"
            elif registration.uniforms['uniform_xl']:
                uniforms = "XL"
            elif registration.uniforms['uniform_xxl']:
                uniforms = "XXL"
        else:
            uniforms = "None"
        
        payment_mode = ""
        if registration.payment_mode == 'full_payment':
            payment_mode = "Full Payment"
        elif registration.payment_mode == 'installment':
            payment_mode = "Installment"
        elif registration.payment_mode == 'premium':
            payment_mode = "Premium Payment"
        elif registration.payment_mode == 'full_payment_promo':
            payment_mode = "Full Payment - Promo"
        elif registration.payment_mode == 'installment_promo':
            payment_mode = "Installment - Promo"
        elif registration.payment_mode == 'premium_promo':
            payment_mode = "Premium Payment - Promo"
        elif registration.payment_mode == "refund":
            payment_mode = "Refunded"

        if registration.amount == registration.amount_deposit:
            deposit = "Yes"
        else: 
            deposit = "No"

        _table_data.append([
            str(registration.id),
            registration.registration_date_local_string,
            registration.full_registration_number,
            registration.full_name,
            registration.batch_number.number if registration.batch_number is not None else "",
            branch.name if branch is not None else '',
            registration.schedule,
            payment_mode,
            str(registration.amount),
            str(registration.balance),
            paid,
            deposit,
            contact_person.fname if contact_person is not None else '',
            books,
            uniforms,
            registration.created_by,
            actions
        ])


    total_installment = Decimal128(str(installment_registrations.sum('amount')))
    total_full_payment = Decimal128(str(full_payment_registrations.sum('amount')))
    total_premium_payment = Decimal128(str(premium_payment_registrations.sum('amount')))

    with decimal.localcontext(D128_CTX):
        total_payment = total_installment.to_decimal() + total_full_payment.to_decimal() + total_premium_payment.to_decimal()

    response = {
        'draw': draw,
        'recordsTotal': registrations.count(),
        'recordsFiltered': registrations.count(),
        'data': _table_data,
        'totalInstallment': str(total_installment),
        'totalFullPayment': str(total_full_payment),
        'totalPremiumPayment': str(total_premium_payment),
        'totalPayment': str(total_payment),
        'salesToday': str(sales_today)
    }

    return jsonify(response)


@bp_lms.route('/api/members/<string:client_id>/edit', methods=['POST'])
@login_required
def edit_member(client_id):
    _from = request.json.get('from', 'student_records')

    if _from == "orientation_attendance":
        lname = request.json['lname']
        fname = request.json['fname']
        mname = request.json['mname']
        suffix = request.json['suffix']
        contact_no = request.json['contact_no']

        client = Registration.objects.get_or_404(id=client_id)
        client.lname = lname
        client.fname = fname
        client.mname = mname
        client.suffix = suffix
        client.contact_number = contact_no

        client.save()

        with mongo.cx.start_session() as session:
            with session.start_transaction():
                edit_student_description = "Update oriented - {lname} {fname} {branch} by {user}".format(
                    lname=client.lname,
                    fname=client.fname,
                    branch=client.branch.name,
                    user=current_user.fname + " " + current_user.lname
                    )

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": edit_student_description,
                    "from_module": "Orientation"
                }, session=session)

        response = {
            'result': True
        }

        return jsonify(response)

    lname = request.json['lname']
    fname = request.json['fname']
    mname = request.json['mname']
    suffix = request.json['suffix']
    birth_date = request.json['birth_date']
    passport = request.json['passport']
    contact_no = request.json['contact_no']
    email = request.json['email']
    address = request.json['address']
    e_registration = request.json['e_registration']
    e_reg_password = request.json['e_reg_password']
    civil_status = request.json['civil_status']
    gender = request.json['gender']

    client = Registration.objects.get_or_404(id=client_id)
    client.lname = lname
    client.fname = fname
    client.mname = mname
    client.suffix = suffix
    # client.birth_date = birth_date
    client.passport = passport
    client.contact_number = contact_no
    client.email = email
    client.address = address
    client.e_registration = e_registration
    client.e_reg_password = e_reg_password
    client.civil_status = civil_status
    client.gender = gender

    client.save()

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            edit_student_description = "Update student - {lname} {fname} {branch} by {user}".format(
                lname=client.lname,
                fname=client.fname,
                branch=client.branch.name,
                user=current_user.fname + " " + current_user.lname
                )

            mongo.db.lms_system_transactions.insert_one({
                "_id": ObjectId(),
                "date": get_date_now(),
                "current_user": current_user.id,
                "description": edit_student_description,
                "from_module": "Student Records"
            }, session=session)

    response = {
        'result': True
    }

    return jsonify(response)


@bp_lms.route('/api/members/<string:client_id>', methods=['GET'])
def get_member(client_id):
    
    client = Registration.objects.get(id=client_id)

    books = 'None'
    uniforms = 'None'
    id_materials = 'None'

    if client.books:
        if client.books['volume1']:
            books = "Vol. 1"
        if client.books['volume2']:
            books += " Vol. 2"
        if client.books['book_none']:
            books = "None"
    else:
        books = "None"

    if client.uniforms:
        if client.uniforms['uniform_none']:
            uniforms = "None"
        elif client.uniforms['uniform_xs']:
            uniforms = "XS"
        elif client.uniforms['uniform_s']:
            uniforms = "S"
        elif client.uniforms['uniform_m']:
            uniforms = "M"
        elif client.uniforms['uniform_l']:
            uniforms = "L"
        elif client.uniforms['uniform_xl']:
            uniforms = "XL"
        elif client.uniforms['uniform_xxl']:
            uniforms = "XXL"
    else:
        uniforms = "None"

    if client.id_materials:
        if client.id_materials['id_card']:
            id_materials = "ID Card"
        if client.id_materials['id_lace']:
            id_materials += " ID Lace"
    else:
        id_materials = "None"

    payments = []

    student_payments = mongo.db.lms_registration_payments.find({"payment_by": ObjectId(client_id)})
    for payment in student_payments:
        if type(payment['date']) == datetime:
            local_datetime = payment['date'].replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(payment['date'] == str):
            to_date = datetime.strptime(payment['date'], "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else:
            local_datetime = ''

        payments.append({
            'amount': str(payment['amount']),
            'current_balance': str(payment['current_balance']),
            'date': local_datetime,
            'remarks': payment['payment_mode'],
            'deposited': payment['deposited'] if payment['deposited'] is not None else 'No',
        })
        
    if client.balance <= 0:
        is_paid = True
    else:
        is_paid = False

    data = {
        'id': str(client.id),
        'fname': client.fname,
        'lname': client.lname,
        'mname': client.mname,
        'suffix': client.suffix,
        'batch_no': client.batch_number.number if client.batch_number is not None else '',
        'schedule': client.schedule,
        'branch': client.branch.name,
        'contact_person': client.contact_person.fname,
        'birth_date': client.birth_date,
        'passport': client.passport,
        'contact_no': client.contact_number,
        'email': client.email,
        'address': client.address,
        'mode_of_payment': client.payment_mode,
        'book': books,
        'uniform': uniforms,
        'books': client.books,
        'uniforms': client.uniforms,
        'id_materials': id_materials,
        'amount': str(client.amount),
        'balance': str(client.balance),
        'status': client.status,
        'is_oriented': client.is_oriented,
        'payments': payments,
        'e_registration': client.e_registration,
        'e_reg_password': client.e_reg_password,
        'civil_status': client.civil_status,
        'gender': client.gender,
        'registration_no': client.full_registration_number,
        'is_paid': is_paid,
        'reviewers': client.get_reviewers()
    }
    response = {
        'data': data
    }
    return jsonify(response)


@bp_lms.route('/clients/new-payment', methods=['POST'])
@login_required
def new_payment():
    client_id = request.form['client_id']
    amount = decimal.Decimal(request.form['new_amount'])
    date = request.form['date']

    try:
        client = Registration.objects.get_or_404(id=client_id)

        is_premium = request.form.get('chkbox_upgrade', False)
        is_upgrade_full_payment = request.form.get('chkbox_upgrade_full_payment', False)

        if is_premium != 'on':
            if amount > client.balance:
                flash("New payment is greater than the student balance!", 'error')
                return redirect(url_for('lms.members'))

        if client.payment_mode == "installment_promo":
            client.payment_mode = client.payment_mode if is_premium != 'on' else 'premium_promo'
        else:
            client.payment_mode = client.payment_mode if is_premium != 'on' else 'premium'

        if is_upgrade_full_payment == 'on':
            client.payment_mode = "full_payment" if client.payment_mode == "installment" else 'full_payment_promo'

        client.amount += amount
        
        if client.payment_mode == "premium" or client.payment_mode == "premium_promo":
            client.balance = ((client.balance + 1000) - amount)
        else:
            if is_upgrade_full_payment == 'on':
                client.balance = client.balance - (amount + 500) # installment - full_payment
            else:
                client.balance = client.balance - amount
        
        if client.level == "first":
            earnings_percent = decimal.Decimal(0.14)
            savings_percent = decimal.Decimal(0.00286)
        elif client.level == "second":
            earnings_percent = decimal.Decimal(0.0286)
            savings_percent = decimal.Decimal(0.00)
        else:
            earnings_percent = decimal.Decimal(0.00)
            savings_percent = decimal.Decimal(0.00)

        earnings = amount * earnings_percent
        savings = amount * savings_percent

        if client.level == "first":
            client.fle = client.fle + earnings
        elif client.level == "second":
            client.sle = client.sle + earnings

        books = request.form.getlist('books')
        
        client.books = {
            'book_none': True if 'book_none' in books else False,
            'volume1': True if 'volume1' in books else False,
            'volume2': True if 'volume2' in books else False,
        }

        uniforms = request.form.getlist('uniforms')

        client.uniforms = {
            'uniform_none': True if 'uniform_none' in uniforms else False,
            'uniform_xs': True if 'uniform_xs' in uniforms else False,
            'uniform_s': True if 'uniform_s' in uniforms else False,
            'uniform_m': True if 'uniform_m' in uniforms else False,
            'uniform_l': True if 'uniform_l' in uniforms else False,
            'uniform_xl': True if 'uniform_xl' in uniforms else False,
            'uniform_xxl': True if 'uniform_xxl' in uniforms else False,
        }

        id_materials = request.form.getlist('others')

        client.id_materials = {
            'id_card': True if 'id_card' in id_materials else False,
            'id_lace': True if 'id_lace' in id_materials else False,
        }

        payment = {
            "_id": ObjectId(),
            "deposited": "Pre Deposit",
            "payment_mode": client.payment_mode,
            "amount": Decimal128(str(amount)),
            "current_balance": Decimal128(str(client.balance)),
            "confirm_by": current_user.id,
            "date": convert_to_utc(date, "date_from"),
            "payment_by": ObjectId(client_id),
            "earnings": Decimal128(str(earnings)),
            "savings": Decimal128(str(savings)),
            "branch": ObjectId(client.branch.id)
        }

        contact_person_earning = {
            "_id": ObjectId(),
            "payment_mode": client.payment_mode,
            "savings": Decimal128(str(savings)),
            "earnings": Decimal128(str(earnings)),
            "branch": client.branch.id,
            "client": ObjectId(client_id),
            "date": convert_to_utc(date, "date_from"),
            "registered_by": current_user.id,
            "payment_id": payment["_id"]
        }

        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.lms_registrations.update_one({"_id": ObjectId(client_id)},
                {"$set": {
                    "payment_mode": client.payment_mode,
                    "amount": Decimal128(str(client.amount)),
                    "balance": Decimal128(str(client.balance)),
                    "fle": Decimal128(str(client.fle)),
                    "sle": Decimal128(str(client.sle)),
                    "books": client.books,
                    "uniforms": client.uniforms,
                    "id_materials": client.id_materials,
                }}, session=session)

                Payment.pay_registration(payment, session=session)

                mongo.db.auth_users.update_one({"_id": client.contact_person.id},
                {"$push": {
                    "earnings": contact_person_earning,
                }}, session=session)

                payment_description = "Update payment - {id} {lname} {fname}  {branch} {batch} w/ amount of Php. {amount}".format(
                    id=client.full_registration_number,
                    lname=client.lname,
                    fname=client.fname,
                    branch=client.branch.name,
                    batch=client.batch_number.number,
                    amount=str(amount)
                )

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": payment_description,
                    "from_module": "Student Records"
                }, session=session)

                earning_description = "Earnings/Savings - Php. {earnings} / {savings} of {contact_person} from {student} 's {payment_mode} w/ amount of Php. {amount}".format(
                    earnings="{:.2f}".format(earnings),
                    savings="{:.2f}".format(savings),
                    contact_person=client.contact_person.fname + " " + client.contact_person.lname,
                    student=client.lname + " " + client.fname,
                    payment_mode=client.payment_mode,
                    amount=str(amount)
                )
                
                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": earning_description,
                    "from_module": "Student Records"
                }, session=session)

                # minus stocks
                # if client.uniforms['uniform_xs'] or client.uniforms['uniform_s'] or client.uniforms['uniform_m'] \
                #     or client.uniforms['uniform_l'] or client.uniforms['uniform_xl'] or client.uniforms['uniform_xxl']:

                #     mongo.db.lms_inventories.update_one({
                #         "description": "UNIFORM"
                #     },
                #     {"$inc": {
                #         "remaining": -1
                #     }}, session=session)

    except Exception as err:
        raise err

    if is_premium == 'on':
        flash("Client's payment upgraded successfully!", 'success')
    else:
        print("TEST!!!!!!!!!!!!")
        flash("Update client's payment successfully!", 'success')

    return redirect(url_for('lms.members'))


@bp_lms.route('/clients/upgrade_to_premium', methods=['POST'])
@login_required
def upgrade_to_premium():
    client_id = request.form['client_id']
    amount = decimal.Decimal(request.form['upgrade_new_amount'])
    date = request.form['upgrade_date']

    try:
        client = Registration.objects.get_or_404(id=client_id)
        
        if client.payment_mode == "full_payment_promo" or client.payment_mode == "installment_promo":
            client.payment_mode = 'premium_promo'
        else:
            client.payment_mode = 'premium'
        
        client.amount += amount
        
        if client.level == "first":
            earnings_percent = decimal.Decimal(0.14)
            savings_percent = decimal.Decimal(0.00286)
        elif client.level == "second":
            earnings_percent = decimal.Decimal(0.0286)
            savings_percent = decimal.Decimal(0.00)
        else:
            earnings_percent = decimal.Decimal(0.00)
            savings_percent = decimal.Decimal(0.00)

        earnings = amount * earnings_percent
        savings = amount * savings_percent

        if client.level == "first":
            client.fle = client.fle + earnings
        elif client.level == "second":
            client.sle = client.sle + earnings

        books = request.form.getlist('upgrade_books')
        
        client.books = {
            'book_none': True if 'book_none' in books else False,
            'volume1': True if 'volume1' in books else False,
            'volume2': True if 'volume2' in books else False,
        }

        uniforms = request.form.getlist('upgrade_uniforms')

        client.uniforms = {
            'uniform_none': True if 'uniform_none' in uniforms else False,
            'uniform_xs': True if 'uniform_xs' in uniforms else False,
            'uniform_s': True if 'uniform_s' in uniforms else False,
            'uniform_m': True if 'uniform_m' in uniforms else False,
            'uniform_l': True if 'uniform_l' in uniforms else False,
            'uniform_xl': True if 'uniform_xl' in uniforms else False,
            'uniform_xxl': True if 'uniform_xxl' in uniforms else False,
        }

        id_materials = request.form.getlist('upgrade_others')

        client.id_materials = {
            'id_card': True if 'upgrade_id_card' in id_materials else False,
            'id_lace': True if 'upgrade_id_lace' in id_materials else False,
        }

        payment = {
            "_id": ObjectId(),
            "deposited": "Pre Deposit",
            "payment_mode": client.payment_mode,
            "amount": Decimal128(str(amount)),
            "current_balance": Decimal128(str(client.balance)),
            "confirm_by": current_user.id,
            "date": convert_to_utc(date, "date_from"),
            "payment_by": ObjectId(client_id),
            "earnings": Decimal128(str(earnings)),
            "savings": Decimal128(str(savings)),
            "branch": ObjectId(client.branch.id)
        }

        contact_person_earning = {
            "_id": ObjectId(),
            "payment_mode": client.payment_mode,
            "savings": Decimal128(str(savings)),
            "earnings": Decimal128(str(earnings)),
            "branch": client.branch.id,
            "client": ObjectId(client_id),
            "date": convert_to_utc(date, "date_from"),
            "registered_by": current_user.id,
            "payment_id": payment["_id"]
        }

        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.lms_registrations.update_one({"_id": ObjectId(client_id)},
                {"$set": {
                    "payment_mode": client.payment_mode,
                    "amount": Decimal128(str(client.amount)),
                    "fle": Decimal128(str(client.fle)),
                    "sle": Decimal128(str(client.sle)),
                    "books": client.books,
                    "uniforms": client.uniforms,
                    "id_materials": client.id_materials,
                }}, session=session)

                Payment.pay_registration(payment, session=session)

                mongo.db.auth_users.update_one({"_id": client.contact_person.id},
                {"$push": {
                    "earnings": contact_person_earning
                }}, session=session)


                payment_description = "Upgrade to premium - {id} {lname} {fname}  {branch} {batch} w/ amount of Php. {amount}".format(
                    id=client.full_registration_number,
                    lname=client.lname,
                    fname=client.fname,
                    branch=client.branch.name,
                    batch=client.batch_number.number,
                    amount=str(amount)
                )

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": payment_description,
                    "from_module": "Student Records"
                }, session=session)

                earning_description = "Earnings/Savings - Php. {earnings} / {savings} of {contact_person} from {student} 's {payment_mode} w/ amount of Php. {amount}".format(
                    earnings="{:.2f}".format(earnings),
                    savings="{:.2f}".format(savings),
                    contact_person=client.contact_person.fname + " " + client.contact_person.lname,
                    student=client.lname + " " + client.fname,
                    payment_mode=client.payment_mode,
                    amount=str(amount)
                )
                
                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": earning_description,
                    "from_module": "Student Records"
                }, session=session)

        flash("Client's payment upgraded successfully!", 'success')
    except Exception as err:
        flash(str(err), 'error')

    return redirect(url_for('lms.members'))


@bp_lms.route('/students.pdf')
def print_students_pdf():
    branch_id = request.args.get('branch', 'all')
    batch_no = request.args.get('batch_no', 'all')
    schedule = request.args.get('schedule', 'all')
    search_value = request.args.get('search_value', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    payment_status = request.args.get('payment_status')
    payment_mode = request.args.get('payment_mode')
    report = request.args.get('report', 'default')
    
    installment_registrations = Registration.objects().filter(Q(payment_mode='installment') | Q(payment_mode="installment_promo")).filter(is_archived__ne=True)
    full_payment_registrations = Registration.objects().filter(Q(payment_mode='full_payment') | Q(payment_mode="full_payment_promo")).filter(is_archived__ne=True)
    premium_payment_registrations = Registration.objects().filter(Q(payment_mode='premium') | Q(payment_mode='premium_promo')).filter(is_archived__ne=True)

    if branch_id != 'all':
        registrations = Registration.objects(branch=branch_id).filter(is_archived__ne=True).filter(status='registered')
        installment_registrations = installment_registrations.filter(branch=branch_id)
        full_payment_registrations = full_payment_registrations.filter(branch=branch_id)
        premium_payment_registrations = premium_payment_registrations.filter(branch=branch_id)

        branch_id = Branch.objects.get_or_404(id=branch_id).name
    else:
        registrations = Registration.objects(status='registered').filter(is_archived__ne=True)

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)
        installment_registrations = installment_registrations.filter(batch_number=batch_no)
        full_payment_registrations = full_payment_registrations.filter(batch_number=batch_no)
        premium_payment_registrations = premium_payment_registrations.filter(batch_number=batch_no)

    if schedule != 'all':
        registrations = registrations.filter(schedule=schedule)
        installment_registrations = installment_registrations.filter(schedule=schedule)
        full_payment_registrations = full_payment_registrations.filter(schedule=schedule)
        premium_payment_registrations = premium_payment_registrations.filter(schedule=schedule)

    if search_value != "undefined":
        registrations = registrations.filter(lname__icontains=search_value)
        installment_registrations = installment_registrations.filter(lname__icontains=search_value)
        full_payment_registrations = full_payment_registrations.filter(lname__icontains=search_value)
        premium_payment_registrations = premium_payment_registrations.filter(lname__icontains=search_value)


    if date_from !="":
        registrations = registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))
        installment_registrations = installment_registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))
        full_payment_registrations = full_payment_registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))
        premium_payment_registrations = premium_payment_registrations.filter(registration_date__gte=convert_to_utc(date_from, 'date_from'))

    if date_to != "":
        registrations = registrations.filter(registration_date__lte=convert_to_utc(date_to))
        installment_registrations = installment_registrations.filter(registration_date__lte=convert_to_utc(date_to))
        full_payment_registrations = full_payment_registrations.filter(registration_date__lte=convert_to_utc(date_to))
        premium_payment_registrations = premium_payment_registrations.filter(registration_date__lte=convert_to_utc(date_to))

    if payment_status == 'PAID':
        registrations = registrations.filter(balance__lte=0)
        installment_registrations = installment_registrations.filter(balance__lte=0)
        full_payment_registrations = full_payment_registrations.filter(balance__lte=0)
        premium_payment_registrations = premium_payment_registrations.filter(balance__lte=0)

    elif payment_status == "NOT PAID":
        registrations = registrations.filter(balance__gt=0)
        installment_registrations = installment_registrations.filter(balance__gt=0)
        full_payment_registrations = full_payment_registrations.filter(balance__gt=0)
        premium_payment_registrations = premium_payment_registrations.filter(balance__gt=0)

    if payment_mode != 'all':
        registrations = registrations.filter(payment_mode=payment_mode)
        installment_registrations = installment_registrations.filter(payment_mode=payment_mode)
        full_payment_registrations = full_payment_registrations.filter(payment_mode=payment_mode)
        premium_payment_registrations = premium_payment_registrations.filter(payment_mode=payment_mode)

    _table_data = []

    uniforms_count = 0
    id_lace_count = 0
    id_card_count = 0
    book1_count = 0
    book2_count = 0

    for registration in registrations:
        books = ""
        uniforms = ""
        id_lace = False
        id_card = False

        actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#editModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-success btn-edit"><i class="pe-7s-wallet btn-icon-wrapper"> </i></button>
            <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""

        paid = 'NOT PAID'

        if registration.balance <= 0.00:
            actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
            paid = 'PAID'

        _branch = registration.branch
        contact_person = registration.contact_person

        if registration.books:
            books = "None"

            if registration.books['volume1']:
                books = "Vol. 1"
                book1_count = book1_count + 1
            if registration.books['volume2']:
                books += " Vol. 2"
                book2_count = book2_count + 1
            if registration.books['book_none']:
                books = "None"
        else:
            books = "None"

        if registration.uniforms:
            uniforms = "None"

            if registration.uniforms['uniform_none']:
                uniforms = "None"
            elif registration.uniforms['uniform_xs']:
                uniforms = "XS"
                uniforms_count = uniforms_count + 1
            elif registration.uniforms['uniform_s']:
                uniforms = "S"
                uniforms_count = uniforms_count + 1
            elif registration.uniforms['uniform_m']:
                uniforms = "M"
                uniforms_count = uniforms_count + 1
            elif registration.uniforms['uniform_l']:
                uniforms = "L"
                uniforms_count = uniforms_count + 1
            elif registration.uniforms['uniform_xl']:
                uniforms = "XL"
                uniforms_count = uniforms_count + 1
            elif registration.uniforms['uniform_xxl']:
                uniforms = "XXL"
                uniforms_count = uniforms_count + 1
        else:
            uniforms = "None"
        
        if registration.id_materials:
            if registration.id_materials['id_card']:
                id_card = True
                id_card_count = id_card_count + 1
            if registration.id_materials['id_lace']:
                id_lace = True
                id_lace_count = id_lace_count + 1

        payment_mode = ""
        if registration.payment_mode == 'full_payment':
            payment_mode = "Full Payment"
        elif registration.payment_mode == 'installment':
            payment_mode = "Installment"
        elif registration.payment_mode == 'premium':
            payment_mode = "Premium Payment"
        elif registration.payment_mode == "full_payment_promo":
            payment_mode = "Full Payment - Promo"
        elif registration.payment_mode == "installment_promo":
            payment_mode = "Installment - Promo"
        elif registration.payment_mode == "premium_promo":
            payment_mode = "Premium - Promo"

        _table_data.append([
            str(registration.id), # 0
            registration.created_at_local, # 1
            registration.full_registration_number, # 2
            registration.full_name, # 3
            registration.batch_number.number if registration.batch_number is not None else "",
            _branch.name if _branch is not None else '', # 5
            registration.schedule, # 6
            payment_mode, # 7
            str(registration.amount), # 8
            str(registration.balance), # 9
            paid, # 10
            contact_person.fname if contact_person is not None else '', # 11
            books, # 12
            uniforms, # 13
            registration.created_by, # 14
            actions, # 15
            registration.passport, # 16
            registration.contact_number, # 17
            id_card, # 18
            id_lace, # 19
            registration.e_registration, # 20
            registration.passport, # 21
            registration.contact_number, #22
            registration.lname, #23
            registration.fname, # 24
            registration.mname, # 25
            registration.address, # 26
            registration.email, # 27
            registration.birth_date if registration.birth_date else '', #28
        ])
        print(books)

    total_installment = Decimal128(str(installment_registrations.sum('amount')))
    total_full_payment = Decimal128(str(full_payment_registrations.sum('amount')))
    total_premium_payment = Decimal128(str(premium_payment_registrations.sum('amount')))

    with decimal.localcontext(D128_CTX):
        total_payment = total_installment.to_decimal() + total_full_payment.to_decimal() + total_premium_payment.to_decimal()

    total_balance = registrations.sum('balance')
    
    template = ""

    if report == 'audit':
        template = 'lms/students_audit_pdf.html'
    else:
        template = 'lms/student_pdf.html'

    html = render_template(
        template,
        students=_table_data,
        branch=branch_id.upper(),
        batch_no=batch_no.upper(),
        schedule=schedule.upper(),
        total_installment=total_installment,
        total_full_payment=total_full_payment,
        total_premium_payment=total_premium_payment,
        total_payment=total_payment,
        total_balance=total_balance,
        uniforms_count=uniforms_count,
        book1_count=book1_count,
        book2_count=book2_count,
        id_card_count=id_card_count,
        id_lace_count=id_lace_count
        )

    return render_pdf(HTML(string=html))


@bp_lms.route('/student_info.pdf')
def print_student_info():
    student_id = request.args.get('student_id', '')

    student = Registration.objects.get_or_404(id=student_id)

    address = student.branch.address

    html = render_template(
            'lms/student_info_pdf.html',
            address=address,
            student=student
            )

    return render_pdf(HTML(string=html))


@bp_lms.route('/student_agreement_form.pdf')
def print_student_agreement_form():
    student_id = request.args.get('student_id', '')

    student = Registration.objects.get_or_404(id=student_id)

    branch = student.branch
    
    settings = mongo.db.lms_configurations.find_one({'name': 'agreement_form_pdf_setting'})['settings']
    payment_rules = settings.get('payment_rules')
    mode_of_payment = settings.get('mode_of_payment')
    refunds_and_withdrawals = settings.get('refunds_and_withdrawals')

    timezone = pytz.timezone('Asia/Manila')
    today = datetime.now(tz=timezone)
    year_last_2 = str(today.year)[2:]
    sequence_no = str(today.month) + str(today.day) + year_last_2 + "SN" + student.full_registration_number + str(today.month) + str(today.day) + str(today.year)
    
    html = render_template(
            'lms/student_agreement_form_pdf.html',
            branch=branch,
            student=student,
            payment_rules=payment_rules,
            mode_of_payment=mode_of_payment,
            refunds_and_withdrawals=refunds_and_withdrawals,
            today=today,
            sequence_no=sequence_no
        )

    return render_pdf(HTML(string=html))


@bp_lms.route('/refund', methods=['POST'])
def refund():
    student_id = request.json.get('student_id', None)
    password = request.json.get('password', '')

    if not current_user.check_password(password):
        return jsonify({
            'status': 'error',
            'message': "Invalid password!"
        }), 400
    student: Registration = Registration.objects.get(id=student_id)
    
    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():                
                with decimal.localcontext(D128_CTX):
                    total_amount_due = student.amount * decimal.Decimal(".8")
                    # refunded_balance = (total_amount_due - student.amount) + student.balance.to_decimal()

                accounting = mongo.db.lms_accounting.find_one({
                    "branch": ObjectId(student.branch.id),
                })
                if accounting:
                    with decimal.localcontext(D128_CTX):
                        previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')
                        new_total_fund_wallet = previous_fund_wallet.to_decimal() - decimal.Decimal(total_amount_due)
                        balance = Decimal128(previous_fund_wallet.to_decimal() - Decimal128(str(total_amount_due)).to_decimal())

                        if total_amount_due > previous_fund_wallet.to_decimal():
                            return jsonify({
                                'status': 'error',
                                'message': "Insufficient fund wallet balance"
                            }), 500

                        mongo.db.lms_accounting.update_one({
                            "branch": ObjectId(student.branch.id)
                        },
                        {'$set': {
                            "total_fund_wallet": Decimal128(new_total_fund_wallet)
                        }},session=session)
                else:
                    return jsonify({
                        'status': 'error',
                        'message': "Accounting data not found"
                    }), 500
                
                payment = {
                    "_id": ObjectId(),
                    "deposited": "Pre Deposit",
                    "payment_mode": 'refund',
                    "amount": Decimal128(str(total_amount_due)),
                    "current_balance": Decimal128(str('0.00')),
                    "confirm_by": current_user.id,
                    "date": get_date_now(),
                    "payment_by": ObjectId(student.id),
                    "earnings": Decimal128('0'),
                    "savings": Decimal128('0'),
                }

                mongo.db.lms_registrations.update_one({
                    "_id": ObjectId(student_id)
                },{"$set": {
                    'status': "refunded",
                    'payment_mode': 'refund'
                },
                    "$push": {
                    'payments': payment
                }}, session=session)

                mongo.db.lms_fund_wallet_transactions.insert_one({
                    'type': 'expenses',
                    'running_balance': balance,
                    'branch': ObjectId(student.branch.id),
                    'date': get_date_now(),
                    'category': "refund",
                    'description': str(student.id),
                    'total_amount_due': Decimal128(total_amount_due),
                    'created_at': get_date_now(),
                    'created_by': current_user.fname + " " + current_user.lname
                },session=session)
        response = {
            'status': 'success',
            'message': "Refunded successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500
        

@bp_lms.route('/update_agreement_form_settings', methods=['POST'])
def update_agreement_form_settings():
    form = request.form
    
    payment_rules = form.get('payment_rules')
    mode_of_payment = form.get('mode_of_payment')
    refund_and_withdrawals = form.get('refunds_and_withdrawals')

    mongo.db.lms_configurations.update_one(
        {"name": "agreement_form_pdf_setting"},
        {"$set": {
            "settings.payment_rules": payment_rules,
            "settings.mode_of_payment": mode_of_payment,
            "settings.refunds_and_withdrawals": refund_and_withdrawals
        }}
    )

    return redirect(url_for('lms.members'))


@bp_lms.route('modify_and_download_certificate')
def modify_and_download_certificate():
    fname = request.args.get('fname', '')
    mname = request.args.get('mname', '')
    lname = request.args.get('lname', '')
    full_name = fname + " " + mname + " " + lname
    prime_registration = request.args.get('prime_registration', '')
    cert_type = request.args.get('cert_type',)
    manager_name = request.args.get('manager_name', '')
    teacher_name = request.args.get('teacher_name', '')
    address = request.args.get('address', '')
    day = request.args.get('day', '23rd')
    month = request.args.get('month', 'October')
    year = request.args.get('year', '2022')
    
    font_full_name = int(request.args.get('font_full_name'))
    font_manager_name = int(request.args.get('font_manager_name'))
    font_teacher_name = int(request.args.get('font_teacher_name'))
    font_address = int(request.args.get('font_address'))
    
    # Delete old pdfs
    old_files = glob.glob(current_app.config['PDF_FOLDER'] + 'generated/*.pdf')
    for file in old_files:
        os.remove(file)

    if cert_type == 'no_partner_no_underline':
        src_dir = current_app.config['PDF_FOLDER'] + 'cert_no_partner_no_underline.pdf'
    elif cert_type == 'partner_underline':
        src_dir = current_app.config['PDF_FOLDER'] + 'cert_partner_underline.pdf'
    elif cert_type == 'partner_no_underline':
        src_dir = current_app.config['PDF_FOLDER'] + 'cert_partner_no_underline.pdf'
    elif cert_type == 'no_partner_underline':
        src_dir = current_app.config['PDF_FOLDER'] + 'cert_no_partner_underline.pdf'

    # Copy template
    file_name = "generated/" +"cert_" + str(datetime.timestamp(datetime.utcnow())) + '.pdf'
    dst_dir = os.path.join(current_app.config['PDF_FOLDER'], file_name)
    copyfile(src_dir,dst_dir)

    # Add texts on the new PDF     
    # Create a new PDF with Reportlab
    packet = io.BytesIO()
    inch = 72.0
    can = canvas.Canvas(packet, pagesize=(14.76*inch, 11.33*inch))
    
    # Full name
    can.setFont('Black Chancery', font_full_name)
    can.drawCentredString(320, 270, full_name)
    
    # day, month, year
    can.setFont('Black Chancery', 18)
    if cert_type in ['partner_underline', 'partner_no_underline']:
        can.drawCentredString(150, 182, day)
        can.drawCentredString(247, 182, month)
        can.drawCentredString(312, 182, year)
    elif cert_type == "no_partner_underline":
        can.drawCentredString(150, 182, day)
        can.drawCentredString(245, 182, month)
        can.drawCentredString(312, 182, year)
    else:
        can.drawCentredString(160, 182, day)
        can.drawCentredString(255, 182, month)
        can.drawCentredString(322, 182, year)
    
    # address
    can.setFont('Black Chancery', font_address)
    if cert_type in ['partner_underline', 'partner_no_underline']:
        can.drawString(360, 182, address)
    else:
        can.drawString(370, 182, address)
    
    # teacher
    can.setFont('Arial', font_teacher_name)
    if cert_type in ['partner_underline', 'partner_no_underline']:
        can.drawCentredString(140, 105, teacher_name)
    else:
        can.drawCentredString(225, 75, teacher_name)

    # manager
    if cert_type in ['partner_underline', 'partner_no_underline']:
        can.setFont('Arial', font_manager_name)
        can.drawCentredString(507, 105, manager_name)
        
    # certificate no.
    can.setFont('Black Chancery', 15)
    can.drawString(682, 498, prime_registration)

    can.showPage()
    can.save()
    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    # Read your existing PDF
    existing_pdf = PdfFileReader(open(src_dir, "rb"))
    output = PdfFileWriter()
    # Add the "watermark" (which is the new pdf) on the existing page
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
    # Finally, write "output" to a real file
    outputStream = open(dst_dir, "wb")
    output.write(outputStream)
    outputStream.close()
    return send_from_directory(directory=current_app.config['PDF_FOLDER'],filename=file_name)

