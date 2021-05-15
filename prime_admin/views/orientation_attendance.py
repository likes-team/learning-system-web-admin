from prime_admin.forms import OrientationAttendanceForm
from flask.globals import request
from flask.helpers import flash, url_for
from flask_login import login_required
from werkzeug.utils import redirect
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, ContactPerson, OrientationAttendance, Registration
from flask import jsonify
from datetime import datetime
from mongoengine.queryset.visitor import Q


@bp_lms.route('/orientation-attendance')
@login_required
def orientation_attendance():

    _table_columns = [
        'Branch',
        'full name',
        'contact no',
        'contact person',
        'orientator'
    ]

    _table_data = []

    for client in Registration.objects(is_oriented=True):
        _table_data.append((
            client.id,
            client.branch.name if client.branch is not None else "",
            client.full_name,
            client.contact_number,
            client.contact_person.name,
            ""
        ))
    print(_table_data)
    contact_persons = ContactPerson.objects
    branches = Branch.objects

    scripts = [
        {'lms.static': 'js/orientation_attendance.js'},
        {'bp_admin.static': 'js/admin_table.js'}
    ]

    return admin_table(
        OrientationAttendance,
        fields=[],
        form=OrientationAttendanceForm(),
        table_data=_table_data,
        table_columns=_table_columns,
        heading="Orientation Attendance",
        title="Orientation attendance",
        table_template="lms/orientation_attendance.html",
        scripts=scripts,
        contact_persons=contact_persons,
        branches=branches
        )

@bp_lms.route('/api/dtbl/mdl-pre-registered-clients', methods=['GET'])
def get_pre_registered_clients():

    clients = Registration.objects(Q(is_oriented=False) | Q(is_oriented__exists=False))

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

    print(form.contact_person.data)
    client_id = request.form['client_id']
    try:

        if client_id != '':
            client = Registration.objects.get(id=client_id)

            client.is_oriented = True
            client.date_oriented = datetime.now()
            client.contact_person = ContactPerson.objects.get(id=form.contact_person.data)
            client.orientator = None
            client.save()

            flash("Added successfully!", 'success')
            return redirect(url_for('lms.orientation_attendance'))

        new_client = Registration()
        new_client.fname = request.form['fname']
        new_client.lname = request.form['lname']
        new_client.contact_number = request.form['contact_no']
        new_client.contact_person = ContactPerson.objects.get(id=form.contact_person.data)
        new_client.date_oriented = datetime.now()
        new_client.orientator = None
        new_client.is_oriented = True
        new_client.status = "oriented"
        
        new_client.save()

        flash("Added successfully!", 'success')

    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('lms.orientation_attendance'))