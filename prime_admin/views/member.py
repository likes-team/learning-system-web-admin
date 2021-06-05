from decimal import Decimal
from random import uniform
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, ContactPerson, Registration, Member
from flask import json, redirect, url_for, request, current_app, flash, jsonify
from app import db
from datetime import datetime



@bp_lms.route('/members', methods=['GET'])
@login_required
def members():
    _table_columns = [
        'id', 'date', 'registration','name of student', 'batch no.', 'branch', 'schedule', 'remark',
        'amount','balance', 'paid/not paid', 'contact person', 'book', 'Uniform', 'cashier', 'actions'
        ]

    fields = []

    scripts = [
        {'lms.static': 'js/members.js'}
    ]

    modals = [
        'lms/client_view_modal.html',
        'lms/client_edit_modal.html'
    ]

    if current_user.role_name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
    elif current_user.role_name == "Admin":
        branches = Branch.objects
        batch_numbers = Batch.objects()
    
    return admin_table(
        Member,
        fields=fields,
        table_data=[],
        table_columns=_table_columns,
        heading='Student Records',
        subheading="",
        title='Student Records',
        scripts=scripts,
        modals=modals,
        table_template="lms/members_table.html",
        branches=branches,
        batch_numbers=batch_numbers,
        schedules=['WDC', 'SDC']
        )


@bp_lms.route('/dtbl/members')
def get_dtbl_members():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    # search_value = "%" + request.args.get("search[value]") + "%"
    # column_order = request.args.get('column_order')
    branch_id = request.args.get('branch')
    batch_no = request.args.get('batch_no')
    schedule = request.args.get('schedule')

    if branch_id != 'all':
        registrations = Registration.objects(branch=branch_id).filter(status='registered').skip(start).limit(length)
        sales_today = registrations.filter(created_at__gte=datetime.now().date()).sum('amount')
    else:
        registrations = Registration.objects(status='registered').skip(start).limit(length)
        sales_today = registrations.filter(created_at__gte=datetime.now().date()).sum('amount')

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)

    if schedule != 'all':
        registrations = registrations.filter(schedule=schedule)

    _table_data = []

    for registration in registrations:
        books = ""
        uniforms = ""
        actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#editModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-success btn-edit"><i class="pe-7s-wallet btn-icon-wrapper"> </i></button>
            <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""

        paid = 'NOT PAID'

        if registration.balance <= 0.00:
            actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
            paid = 'PAID'

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


        _table_data.append([
            str(registration.id),
            registration.created_at,
            registration.full_registration_number,
            registration.full_name,
            registration.batch_number.number if registration.batch_number is not None else "",
            branch.name if branch is not None else '',
            registration.schedule,
            payment_mode,
            str(registration.amount),
            str(registration.balance),
            paid,
            contact_person.fname if contact_person is not None else '',
            books,
            uniforms,
            registration.created_by,
            actions
        ])

    total_installment = registrations.filter(payment_mode='installment').sum('amount')
    total_full_payment = registrations.filter(payment_mode='full_payment').sum('amount')
    total_premium_payment = registrations.filter(payment_mode='premium').sum('amount')
    total_payment = registrations.sum('amount')

    response = {
        'draw': draw,
        'recordsTotal': registrations.count(),
        'recordsFiltered': registrations.count(),
        'data': _table_data,
        'totalInstallment': total_installment,
        'totalFullPayment': total_full_payment,
        'totalPremiumPayment': total_premium_payment,
        'totalPayment': total_payment,
        'salesToday': sales_today
    }

    return jsonify(response)


@bp_lms.route('/api/members/<string:client_id>/edit', methods=['POST'])
@login_required
def edit_member(client_id):
    lname = request.json['lname']
    fname = request.json['fname']
    mname = request.json['mname']
    suffix = request.json['suffix']
    birth_date = request.json['birth_date']
    passport = request.json['passport']
    contact_no = request.json['contact_no']
    email = request.json['email']
    address = request.json['address']
    print("TEST!")
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
    
    client.save()

    response = {
        'result': True
    }

    return jsonify(response)


@bp_lms.route('/api/members/<string:client_id>', methods=['GET'])
def get_member(client_id):
    
    client = Registration.objects.get(id=client_id)

    books = 'None'
    uniforms = 'None'

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

    data = {
        'id': str(client.id),
        'fname': client.fname,
        'lname': client.lname,
        'mname': client.mname,
        'suffix': client.suffix,
        'batch_no': client.batch_number.number,
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
        'amount': str(client.amount),
        'balance': str(client.balance),
        'status': client.status,
        'is_oriented': client.is_oriented
    }

    response = {
        'data': data
        }

    return jsonify(response)


@bp_lms.route('/clients/new-payment', methods=['POST'])
@login_required
def new_payment():
    client_id = request.form['client_id']
    amount = Decimal(request.form['new_amount'])

    client = Registration.objects.get_or_404(id=client_id)

    client.amount += amount
    client.balance = amount - client.balance

    client.save()
    
    flash("Update client's payment successfully!", 'success')

    return redirect(url_for('lms.members'))