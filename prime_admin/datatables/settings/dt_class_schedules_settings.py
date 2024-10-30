from flask import jsonify, request
from app import mongo
from prime_admin import bp_lms
from prime_admin.models import Branch


@bp_lms.route('/datatables/settings/class-schedules')
def datatables_settings_class_schedules():
    class_schedules = mongo.db.lms_class_schedules.find()
    table_data = []

    for class_schedule in class_schedules:
        branch = Branch.objects.get(id=class_schedule['branch'])
        table_data.append([
            str(class_schedule['_id']),
            branch.name,
            class_schedule['schedule'],
            class_schedule['start_date'],
            class_schedule['end_date'],
            class_schedule.get('is_active', False),
            ''
        ])

    response = {
        'data': table_data,
    }
    return jsonify(response)
