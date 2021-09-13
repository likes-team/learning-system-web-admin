from flask_pymongo import ASCENDING
import pymongo
from app.admin.models import SystemLogs
from flask_mongoengine import json
from werkzeug.exceptions import abort
from flask_login import login_required
from app.admin.templating import admin_table
from flask import jsonify, request
from mongoengine.queryset.visitor import Q
from app.admin import bp_admin
from app import mongo

@bp_admin.route('/system-logs')
@login_required
def system_logs():
    _table_data = []

    scripts = [
        {'bp_admin.static': 'js/system_logs.js'},
    ]

    return admin_table(
        SystemLogs,
        fields=[],
        table_data=_table_data,
        table_columns=['date', 'description', 'module'],
        heading="System Logs",
        title="System Logs",
        # table_template="lms/orientation_attendance.html",
        scripts=scripts,
        view_modal=False
        )


@bp_admin.route('/dtbl/system-logs')
def get_dtbl_system_logs():
    from prime_admin.globals import convert_to_local

    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))


    logs = mongo.db.lms_system_transactions.find().skip(start).sort([("date", pymongo.DESCENDING)]).limit(length)

    _table_data = []

    for log in logs:
        _table_data.append([
            str(log["_id"]),
            convert_to_local(log['date']),
            log["description"],
            log['from_module']
        ])

    response = {
        'draw': draw,
        'recordsTotal': logs.count(),
        'recordsFiltered': logs.count(),
        'data': _table_data,
    }

    return jsonify(response)
