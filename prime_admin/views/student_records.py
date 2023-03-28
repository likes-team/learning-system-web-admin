import decimal
import pytz
from bson.objectid import ObjectId
from mongoengine.queryset.visitor import Q
from prime_admin.globals import convert_to_utc, get_date_now
from flask_login import login_required, current_user
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, Registration, Member, Student
from prime_admin.models_v2 import StudentV2
from flask import redirect, url_for, request, current_app, flash, jsonify, render_template, send_from_directory
from app import mongo
from datetime import datetime
from bson.decimal128 import Decimal128, create_decimal128_context
from flask_weasyprint import HTML, render_pdf
from config import TIMEZONE
from prime_admin.helpers import Payment
from prime_admin.services.printing import Certificate, AttendanceList
from prime_admin.utils.date import format_utc_to_local
from prime_admin.helpers.query_filter import StudentQueryFilter
from prime_admin.services.student import StudentService
from prime_admin.services.inventory import InventoryService
from prime_admin.services.branch import BranchService
from prime_admin.services.batch import BatchService



D128_CTX = create_decimal128_context()


@bp_lms.route('/members', methods=['GET'])
@login_required
def members():
    _table_columns = [
        'id', 'date', 'registration','name of student', 'batch no.', 'branch', 'schedule', 'remark',
        'amount','balance', 'paid/not paid', 'Deposit','contact person', 'session', 'contact no.', 'cashier', 'actions'
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
    sessions = mongo.db.lms_configurations.find_one({'name': 'sessions'})['values']
    payment_rules = settings.get('payment_rules')
    mode_of_payment = settings.get('mode_of_payment')
    refunds_and_withdrawals = settings.get('refunds_and_withdrawals')
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
        refunds_and_withdrawals=refunds_and_withdrawals,
        sessions=sessions
    )


@bp_lms.route('/dtbl/members')
def get_dtbl_members():
    draw = request.args.get('draw')
    query_filter = StudentQueryFilter.from_request(request)
    service = StudentService.find_students(query_filter)
    students = service.get_data()
    _table_data = []

    student: Student
    for student in students:
        # TODO Move this to JS
        actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#editModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-success btn-edit"><i class="pe-7s-wallet btn-icon-wrapper"> </i></button>
            <button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
        
        if current_user.role.name in ['Secretary', 'Admin', 'Partner']:
            if student.payment_mode == "premium" or student.payment_mode == "premium_promo":
                actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""
        else: # Marketers
            actions = ""
            
        _table_data.append([
            str(student.get_id()),
            student.get_registration_date(),
            student.full_registration_number,
            student.get_full_name(),
            student.get_batch_no(),
            student.get_branch_name(),
            student.schedule,
            student.get_payment_mode(),
            student.get_amount(currency=True),
            student.get_balance(currency=True),
            student.get_payment_status(),
            student.get_is_deposited(),
            student.get_contact_person_name(),
            student.get_session(),
            student.contact_number,
            student.created_by,
            actions
        ])
    response = {
        'draw': draw,
        'recordsTotal': service.total_filtered(),
        'recordsFiltered': service.total_filtered(),
        'data': _table_data,
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
        
    if client.balance is not None and client.balance <= 0:
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
        'birth_date': format_utc_to_local(client.birth_date),
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

    service = StudentService.find_student(client_id)
    client = service.get_student()

    client.update_books_from_form(request.form.getlist('books'))
    client.update_uniform_from_form(request.form.getlist('uniforms'))
    client.update_id_materials(request.form.getlist('others'))
    client.update_reviewers(request.form.getlist('reviewers'))
    
    existing_item = mongo.db.lms_registrations.find_one({'_id': ObjectId(client.id)})
    if client.books['volume1']:
        if not existing_item['books'].get('volume1'):
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='volume1', value=1):
                flash("Not enough BOOK 1 stocks!", 'error')
                return redirect(url_for('lms.members'))

    if client.books['volume2']:
        if not existing_item['books'].get('volume2'):
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='volume2', value=1):
                flash("Not enough BOOK 2 stocks!", 'error')
                return redirect(url_for('lms.members'))

    if not client.uniforms['uniform_none']:
        if existing_item['uniforms'].get('uniform_none'):
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='uniform', value=1):
                flash("Not enough UNIFORM stocks!", 'error')
                return redirect(url_for('lms.members'))

    if client.id_materials['id_card']:
        if not existing_item['id_materials'].get('id_card'):
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='id_card', value=1):
                flash("Not enough ID CARD stocks!", 'error')
                return redirect(url_for('lms.members'))

    if client.id_materials['id_lace']:
        if not existing_item['id_materials'].get('id_lace'):
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='id_lace', value=1):
                flash("Not enough ID LACE stocks!", 'error')
                return redirect(url_for('lms.members'))
        
    if client.reviewers['reading']:
        if not existing_item['reviewers'].get('reading'):
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='reading', value=1):
                flash("Not enough REVIEWER READING stocks!", 'error')
                return redirect(url_for('lms.members'))

    if client.reviewers['listening']:
        if not existing_item['reviewers'].get('listening'):
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='listening', value=1):
                flash("Not enough REVIEWER LISTENING stocks!", 'error')
                return redirect(url_for('lms.members'))
            
    is_premium = request.form.get('chkbox_upgrade', False)
    is_upgrade_full_payment = request.form.get('chkbox_upgrade_full_payment', False)

    if is_premium != 'on':
        if amount > client.balance:
            flash("New payment is greater than the student balance!", 'error')
            return redirect(url_for('lms.members'))

    if client.payment_mode == "installment_promo" or client.payment_mode == "full_payment_promo":
        client.payment_mode = client.payment_mode if is_premium != 'on' else 'premium_promo'
    else:
        client.payment_mode = client.payment_mode if is_premium != 'on' else 'premium'

    if is_upgrade_full_payment == 'on':
        client.payment_mode = "full_payment" if client.payment_mode == "installment" else 'full_payment_promo'

    client.amount += amount
    
    if client.payment_mode == "premium" or client.payment_mode == "premium_promo":
        if client.balance > 0:
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
        "branch": ObjectId(client.branch.id),
        "created_at": get_date_now(),
        "contact_person": ObjectId(client.contact_person.id)
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
                'reviewers': client.reviewers
            }}, session=session)

            Payment.pay_registration(payment, session=session)

            InventoryService.buy_items(
                student=client,
                session=session
            )
            
            if is_premium == 'on':
                description = "Upgrade to premium"
            else:
                description = "Update payment"
            payment_description = "{description} - {id} {lname} {fname}  {branch} {batch} w/ amount of Php. {amount}".format(
                description=description,
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

    if is_premium == 'on':
        flash("Client's payment upgraded successfully!", 'success')
    else:
        flash("Update client's payment successfully!", 'success')
    return redirect(url_for('lms.members'))


@bp_lms.route('/students.pdf')
def print_students_pdf():
    branch_id = request.args.get('branch', 'all')
    batch_no = request.args.get('batch_no', 'all')
    schedule = request.args.get('schedule', 'all')
    report = request.args.get('report', 'default')
    query_filter = StudentQueryFilter.from_request(request)
    service = StudentService.find_students(query_filter)
    students = service.get_data()

    table_data = []
    uniforms_count = 0
    id_lace_count = 0
    id_card_count = 0
    book1_count = 0
    book2_count = 0
    for student in students:
        student: StudentV2
        books = ""
        uniforms = ""
        id_lace = False
        id_card = False
        contact_person = "student.contact_person"

        table_data.append([
            str(student.get_id()), # 0
            '', # 1
            student.full_registration_number, # 2
            student.get_full_name(), # 3
            student.batch_no.get_no() if student.batch_no is not None else '',
            student.branch.get_name() if student.branch is not None else '', # 5
            student.schedule, # 6
            student.get_payment_mode(), # 7
            student.get_amount(currency=True), # 8
            student.get_balance(currency=True), # 9
            student.get_payment_status(), # 10
            contact_person, # 11
            student.get_books(), # 12
            student.get_uniform(), # 13
            student.created_by, # 14
            student.passport, # 16
            student.contact_number, # 17
            student.has_id_card(), # 18
            student.has_id_lace(), # 19
            student.e_registration, # 20
            student.passport, # 21
            student.contact_number, #22
            student.lname, #23
            student.fname, # 24
            student.mname, # 25
            student.address, # 26
            student.email, # 27
            student.get_birth_date(), #28
        ])

    total_installment = 0
    total_full_payment = 0
    total_premium_payment = 0
    total_payment = 0
    total_balance = 0
    
    if report == 'audit':
        template = 'lms/students_audit_pdf.html'
    else:
        template = 'lms/student_pdf.html'
        
    if branch_id != 'all':
        branch_name = BranchService.get_name_by_id(branch_id)
    else:
        branch_name = 'all'

    if batch_no != 'all':
        batch_no = BatchService.get_name_by_id(batch_no)

    html = render_template(
        template,
        students=table_data,
        branch=branch_name.upper(),
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


@bp_lms.route('/print-certificate')
def print_certificate():
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
    
    certificate: Certificate = Certificate(cert_type)
    certificate.create()
    certificate.set_full_name(full_name, font_full_name)
    certificate.set_date(day, month, year)
    certificate.set_address(address, font_address)
    certificate.set_teacher(teacher_name, font_teacher_name)
    certificate.set_manager(manager_name, font_manager_name)
    certificate.set_certificate_no(prime_registration)
    certificate.save()
    return send_from_directory(directory=current_app.config['PDF_FOLDER'],filename=certificate.get_file_name())


@bp_lms.route('/attendance_list.pdf')
def print_attendance_list_pdf():
    query_filter = StudentQueryFilter.from_request(request)
    service = AttendanceList.fetch(query_filter)
    service.set_teacher(request.args.get('teacher'))
    return service.generate_pdf()
