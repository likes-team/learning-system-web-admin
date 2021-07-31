import decimal
from prime_admin.globals import get_date_now, get_sales_today_date
from random import uniform
from pymongo.common import clean_node
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, Registration, Member
from flask import json, redirect, url_for, request, current_app, flash, jsonify, render_template
from app import db, csrf
from datetime import datetime
from bson.decimal128 import Decimal128
from app.auth.models import Earning, User
from flask_weasyprint import HTML, render_pdf
from config import TIMEZONE



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
        'lms/client_edit_modal.html',
        'lms/client_upgrade_modal.html'
    ]

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
    elif current_user.role.name == "Admin":
        branches = Branch.objects
        batch_numbers = Batch.objects()
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
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
    search_value = request.args.get("search[value]")
    branch_id = request.args.get('branch')
    batch_no = request.args.get('batch_no')
    schedule = request.args.get('schedule')

    if branch_id != 'all':
        registrations = Registration.objects(branch=branch_id).filter(status='registered').skip(start).limit(length)
        # sales_today = registrations.filter(registration_date__gte=get_sales_today_date().date()).sum('amount')
    else:
        if current_user.role.name == "Marketer":
            registrations = Registration.objects(status='registered').filter(branch__in=current_user.branches).skip(start).limit(length)
            # sales_today = registrations.filter(registration_date__gte=get_sales_today_date().date()).filter(branch__in=current_user.branches).sum('amount')
        else:
            registrations = Registration.objects(status='registered').skip(start).limit(length)
            # sales_today = registrations.filter(registration_date__gte=get_sales_today_date().date()).sum('amount')

    sales_today = 0

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)

    if schedule != 'all':
        registrations = registrations.filter(schedule=schedule)

    if search_value != "":
        registrations = registrations.filter(lname__icontains=search_value)

    _table_data = []

    for registration in registrations:
        books = ""
        uniforms = ""

        actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#editModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-success btn-edit"><i class="pe-7s-wallet btn-icon-wrapper"> </i></button>
            <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""

        paid = 'NOT PAID'

        if registration.balance <= 0.00:
            paid = 'PAID'

        if registration.payment_mode == "premium":
            actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
        elif registration.payment_mode == "full_payment":
            actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#upgradeModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-warning btn-upgrade"><i class="pe-7s-upload btn-icon-wrapper"> </i></button>
            <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
        elif registration.payment_mode == "installment" and registration.balance <= 0.00:
            actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#upgradeModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-warning btn-upgrade"><i class="pe-7s-upload btn-icon-wrapper"> </i></button>
                <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""

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

        if get_sales_today_date().date() == registration.registration_date_local_date.date():
            sales_today += registration.amount

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

    for payment in client.payments:
        payments.append({
            'amount': str(payment['amount']),
            'current_balance': str(payment['current_balance']),
            'date': payment['date']
        })

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
        'e_registration': client.e_registration
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

    client = Registration.objects.get_or_404(id=client_id)

    is_premium = request.form.get('chkbox_upgrade', False)

    if is_premium != 'on':
        if amount > client.balance:
            flash("New payment is greater than the student balance!", 'error')
            return redirect(url_for('lms.members'))

    client.payment_mode = client.payment_mode if is_premium != 'on' else 'premium'
    client.amount += amount
    
    if client.payment_mode == "premium":
        client.balance = ((client.balance + 700) - amount)
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

    custom_id = client.full_registration_number + str(get_date_now())

    client.contact_person.earnings.append(
        Earning(
            custom_id=custom_id,
            payment_mode=client.payment_mode,
            savings=Decimal128(str(savings)),
            earnings=Decimal128(str(earnings)),
            branch=client.branch,
            client=client,
            date=get_date_now(),
            registered_by=User.objects.get(id=str(current_user.id))
        )
    )

    client.payments.append(
        {
            'payment_mode': client.payment_mode,
            'amount': Decimal128(str(amount)),
            'current_balance': Decimal128(str(client.balance)),
            'confirm_by': User.objects.get(id=str(current_user.id)),
            'date': date
        }
    )

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

    client.save()
    client.contact_person.save()
    
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

    client = Registration.objects.get_or_404(id=client_id)
    
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

    custom_id = client.full_registration_number + str(get_date_now())

    client.contact_person.earnings.append(
        Earning(
            custom_id=custom_id,
            payment_mode=client.payment_mode,
            savings=Decimal128(str(savings)),
            earnings=Decimal128(str(earnings)),
            branch=client.branch,
            client=client,
            date=get_date_now(),
            registered_by=User.objects.get(id=str(current_user.id))
        )
    )

    client.payments.append(
        {
            'payment_mode': client.payment_mode,
            'amount': Decimal128(str(amount)),
            'current_balance': Decimal128(str(client.balance)),
            'confirm_by': User.objects.get(id=str(current_user.id)),
            'date': date
        }
    )

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
        'id_card': True if 'id_card' in id_materials else False,
        'id_lace': True if 'id_lace' in id_materials else False,
    }

    client.save()
    client.contact_person.save()
    
    flash("Client's payment upgraded successfully!", 'success')

    return redirect(url_for('lms.members'))


@bp_lms.route('/students.pdf')
def print_students_pdf():
    branch = request.args.get('branch', 'all')
    batch_no = request.args.get('batch_no', 'all')
    schedule = request.args.get('schedule', 'all')
    report = request.args.get('report', 'default')
    
    if branch != 'all':
        registrations = Registration.objects(branch=branch).filter(status='registered')
        branch = Branch.objects.get_or_404(id=branch).name
    else:
        registrations = Registration.objects(status='registered')

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)

    if schedule != 'all':
        registrations = registrations.filter(schedule=schedule)

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

    total_installment = registrations.filter(payment_mode='installment').sum('amount')
    total_full_payment = registrations.filter(payment_mode='full_payment').sum('amount')
    total_premium_payment = registrations.filter(payment_mode='premium').sum('amount')
    total_payment = registrations.sum('amount')
    total_balance = registrations.sum('balance')
    
    template = ""

    if report == 'audit':
        template = 'lms/students_audit_pdf.html'
    else:
        template = 'lms/student_pdf.html'

    html = render_template(
        template,
        students=_table_data,
        branch=branch.upper(),
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
