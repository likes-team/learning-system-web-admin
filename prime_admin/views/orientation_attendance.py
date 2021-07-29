from flask_mongoengine import json
from werkzeug.exceptions import abort
from prime_admin.globals import SECRETARYREFERENCE
from app.auth.models import User
from prime_admin.forms import OrientationAttendanceForm
from flask.helpers import flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import redirect
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, OrientationAttendance, Registration, Batch, Orientator
from flask import jsonify, request
from datetime import datetime
from mongoengine.queryset.visitor import Q
from config import TIMEZONE



@bp_lms.route('/orientation-attendance')
@login_required
def orientation_attendance():
    _table_data = []

    # for client in Registration.objects(Q(is_oriented=True) & Q(status__ne="registered")):
    #     _table_data.append((
    #         client.id,
    #         client.branch.name if client.branch is not None else "",
    #         client.full_name,
    #         client.contact_number,
    #         client.contact_person.name if client.contact_person is not None else '',
    #         client.orientator.fname if client.orientator is not None else ''
    #     ))
    
    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        contact_persons = User.objects(Q(branches__in=[str(current_user.branch.id)]) & Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        contact_persons = User.objects(id=current_user.id)
    else:
        branches = Branch.objects
        contact_persons = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))

    orientators = Orientator.objects()

    scripts = [
        {'lms.static': 'js/orientation_attendance.js'},
        {'bp_admin.static': 'js/admin_table.js'}
    ]

    modals = [
        'lms/search_refferal_modal.html'
    ]

    return admin_table(
        OrientationAttendance,
        fields=[],
        form=OrientationAttendanceForm(),
        table_data=_table_data,
        heading="Orientation Attendance",
        title="Orientation attendance",
        table_template="lms/orientation_attendance.html",
        scripts=scripts,
        contact_persons=contact_persons,
        branches=branches,
        orientators=orientators,
        modals=modals
        )

@bp_lms.route('/api/dtbl/mdl-pre-registered-clients', methods=['GET'])
def get_pre_registered_clients():

    clients = Registration.objects(Q(is_oriented=False) | Q(is_oriented__exists=False) & Q(status="pre_registered"))

    _data = []

    for client in clients:
        _data.append([
            str(client.id),
            client.lname,
            client.fname,
            client.mname,
            client.suffix,
            client.contact_number,
            client.status
        ])

    response = {
        'data': _data
        }

    return jsonify(response)


@bp_lms.route('/orientation-attendance/orient', methods=['POST'])
@login_required
def orient():
    form = OrientationAttendanceForm()

    client_id = request.form['client_id']

    referred_by = request.form['referred_by']

    try:
        if client_id != '':
            client = Registration.objects.get(id=client_id)

            client.is_oriented = True
            client.date_oriented = datetime.now(TIMEZONE)
            client.contact_person = User.objects.get(id=form.contact_person.data)
            client.orientator = Orientator.objects.get(id=form.orientator.data)
            client.save()
        else:
            new_client = Registration()
            new_client.fname = request.form['fname']
            new_client.lname = request.form['lname']
            new_client.contact_number = request.form['contact_no']
            new_client.contact_person = User.objects.get(id=form.contact_person.data)
            new_client.branch = Branch.objects.get(id=form.branch.data)
            new_client.date_oriented = datetime.now(TIMEZONE)
            new_client.orientator = Orientator.objects.get(id=form.orientator.data)
            new_client.is_oriented = True
            new_client.status = "oriented"
            new_client.set_created_at()

            if referred_by == '':
                new_client.level = "first"
            else:
                referred_student = Registration.objects.get(id=referred_by)

                if referred_student.level == "first":
                    new_client.level = "second"
                elif referred_student.level == "second":
                    new_client.level = "third"
                elif referred_student.level == "third":
                    new_client.level = str(4)
                else:
                    print(referred_student.level)
                    new_client.level = str(int(referred_student.level) + 1)

            new_client.save()

        flash("Added successfully!", 'success')

    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('lms.orientation_attendance'))


@bp_lms.route('/api/dtbl/mdl-referrals', methods=['GET'])
def get_referrals():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(status="registered")
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
    else:
        return jsonify({'data': []})

    _data = []

    for client in clients:
        _data.append([
            str(client.id),
            client.lname,
            client.fname,
            client.mname,
            client.suffix,
            client.contact_number,
            client.status
        ])

    response = {
        'data': _data
        }

    return jsonify(response)


@bp_lms.route('/api/get-branch-contact-persons/<string:branch_id>', methods=['GET'])
def get_branch_contact_persons(branch_id):
    contact_persons = User.objects(Q(branches__in=[branch_id]) & Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))

    if contact_persons is None:
        response = {
            'data': []
        }

        return jsonify(response)

    data = []

    for contact_person in contact_persons:
        data.append({
            'id': str(contact_person.id),
            'fname': contact_person.fname
        })

    response = {
        'data': data
        }

    return jsonify(response)

@bp_lms.route('/dtbl/orientation-attendance-members')
def get_dtbl_orientation_attendance_members():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    branch_id = request.args.get('branch')
    contact_person_id = request.args.get('contact_person')

    if branch_id != 'all':
        registrations = Registration.objects(branch=branch_id).filter(status='oriented').skip(start).limit(length)
    else:
        if current_user.role.name == "Marketer":
            registrations = Registration.objects(status='oriented').filter(branch__in=current_user.branches).skip(start).limit(length)
        elif current_user.role.name == "Secretary":
            registrations = Registration.objects(status='oriented').filter(branch=current_user.branch.id).skip(start).limit(length)
        else:
            registrations = Registration.objects(status='oriented').skip(start).limit(length)

    if contact_person_id != 'all':
        registrations = registrations.filter(contact_person=contact_person_id)

    _table_data = []

    print(registrations)
    for registration in registrations:
        _table_data.append([
            str(registration.id),
            registration.branch.name if registration.branch is not None else "",
            registration.full_name,
            registration.contact_number,
            registration.contact_person.name if registration.contact_person is not None else '',
            registration.orientator.fname if registration.orientator is not None else '',
            registration.created_at_local,
        ])

    response = {
        'draw': draw,
        'recordsTotal': registrations.count(),
        'recordsFiltered': registrations.count(),
        'data': _table_data,
    }

    return jsonify(response)