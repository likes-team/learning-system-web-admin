from bson.decimal128 import create_decimal128_context
from bson.objectid import ObjectId
from flask_mongoengine import json
import pytz
from config import TIMEZONE
import decimal
from prime_admin.globals import PARTNERREFERENCE, SECRETARYREFERENCE, convert_to_utc, get_date_now
from app.auth.models import Earning, User
from prime_admin.forms import CashFlowAdminForm, CashFlowSecretaryForm, DepositForm, OrientationAttendanceForm, WithdrawForm
from flask.helpers import flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import redirect
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Accounting, Branch, CashFlow, OrientationAttendance, Registration, Batch, Orientator
from flask import jsonify, request
from datetime import date, datetime
from mongoengine.queryset.visitor import Q
from bson import Decimal128
from app import mongo



D128_CTX = create_decimal128_context()


@bp_lms.route('/fund_wallet')
@login_required
def fund_wallet():

    # if current_user.role.name == "Secretary":
    #     form = CashFlowSecretaryForm()

    # else:
    #     form = CashFlowAdminForm()
    
    _table_data = []

    # if current_user.role.name == "Secretary":
    #     branches = Branch.objects(id=current_user.branch.id)
    # elif current_user.role.name == "Partner":
    #     branches = Branch.objects(id__in=current_user.branches)
    # else:
    #     branches = Branch.objects

    # orientators = Orientator.objects()

    # scripts = [
    #     {'lms.static': 'js/cash_flow.js'},
    # ]

    # modals = [
    #     'lms/deposit_modal.html',
    #     'lms/withdraw_modal.html',
    #     'lms/profit_modal.html',
    #     'lms/pre_deposit_modal.html',
    # ]

    return admin_table(
        CashFlow,
        fields=[],
        # form=form,
        table_data=_table_data,
        table_columns=['id'],
        heading="Cash On Hand",
        subheading="Cash In / Cash Out",
        title="Cash On Hand",
        table_template="lms/cash_on_hand.html",
        )
