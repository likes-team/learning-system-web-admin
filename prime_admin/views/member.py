from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, ContactPerson, Registration, Member
from flask import redirect, url_for, request, current_app, flash, jsonify
from app import db
from datetime import datetime



@bp_lms.route('/members', methods=['GET'])
@login_required
def members():
    _table_columns = [
        'date', 'registration','name of student', 'batch no.', 'branch', 'schedule', 'remark',
        'amount','balance', 'paid/not paid', 'contact person', 'book 1', 'book 2', 'cashier'
        ]

    fields = []

    scripts = [
        {'lms.static': 'js/members.js'}
    ]

    batch_numbers = Batch.objects()
    
    return admin_table(
        Member,
        fields=fields,
        table_data=[],
        table_columns=_table_columns,
        heading='Members',
        subheading="",
        title='Members',
        scripts=scripts,
        table_template="lms/members_table.html",
        branches=Branch.objects,
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
        registrations = Registration.objects(branch=branch_id).filter(status='registered')[start:length]
        sales_today = Registration.objects(created_at__gte=datetime.now().date()).filter(status='registered').filter(branch=branch_id).sum('amount')

    else:
        registrations = Registration.objects(status='registered')[start:length]
        sales_today = Registration.objects(status='registered').filter(created_at__gte=datetime.now().date()).sum('amount')

    if batch_no != 'all':
        registrations = registrations.filter(batch_number=batch_no)

    if schedule != 'all':
        registrations = registrations.filter(schedule=schedule)

    _table_data = []

    for registration in registrations:
        paid = 'NOT PAID'

        if registration.balance <= 0.00:
            paid = 'PAID'

        branch = registration.branch
        contact_person = registration.contact_person
        
        _table_data.append([
            registration.created_at,
            registration.full_registration_number,
            registration.full_name,
            registration.batch_number.number if registration.batch_number is not None else "",
            branch.name if branch is not None else '',
            registration.schedule,
            "Full Payment" if registration.payment_mode == "full_payment" else "Installment",
            str(registration.amount),
            str(registration.balance),
            paid,
            contact_person.fname if contact_person is not None else '',
            '',
            '',
            registration.created_by
        ])

    total_installment = registrations.filter(payment_mode='installment').sum('amount')
    total_full_payment = registrations.filter(payment_mode='full_payment').sum('amount')
    total_payment = registrations.sum('amount')

    print(sales_today)

    response = {
        'draw': draw,
        'recordsTotal': registrations.count(),
        'recordsFiltered': registrations.count(),
        'data': _table_data,
        'totalInstallment': total_installment,
        'totalFullPayment': total_full_payment,
        'totalPayment': total_payment,
        'salesToday': sales_today
    }

    return jsonify(response)