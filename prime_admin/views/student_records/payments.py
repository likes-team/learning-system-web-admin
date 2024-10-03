from bson import ObjectId
from flask import request, render_template, jsonify
from flask_login import login_required
from app import mongo
from prime_admin import bp_lms
from prime_admin.utils.date import get_utc_date_now, convert_date_input_to_utc



@bp_lms.route('/payments')
@login_required
def payments():
    return render_template(
        'lms/student_records/payments/payments_page.html'
    )
