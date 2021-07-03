from prime_admin.globals import SECRETARYREFERENCE
from app.auth.models import User
from prime_admin.forms import CashFlowForm, OrientationAttendanceForm
from flask.helpers import flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import redirect
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, CashFlow, OrientationAttendance, Registration, Batch, Orientator
from flask import jsonify, request
from datetime import datetime
from mongoengine.queryset.visitor import Q


@bp_lms.route('/cash-flow')
@login_required
def cash_flow():
    _table_columns = [
        'Date',
        'Bank name',
        'account no.',
        'account name',
        'Deposit amount'
        'from'
        'by who'
    ]

    _table_data = []

    # for client in Registration.objects(Q(is_oriented=True) & Q(status__ne="registered")):
    #     print(client.status)
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
        contact_persons = User.objects(branches__in=[str(current_user.branch.id)] | Q(role__ne=SECRETARYREFERENCE) | Q(is_superuser=False))
    else:
        branches = Branch.objects
        contact_persons = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))

    orientators = Orientator.objects()

    scripts = [
        {'lms.static': 'js/orientation_attendance.js'},
        {'bp_admin.static': 'js/admin_table.js'}
    ]

    return admin_table(
        CashFlow,
        fields=[],
        form=CashFlowForm(),
        table_data=_table_data,
        table_columns=_table_columns,
        heading="Cash Flow",
        title="Cash Flow",
        table_template="lms/cash_flow.html",
        scripts=scripts,
        contact_persons=contact_persons,
        branches=branches,
        orientators=orientators
        )
