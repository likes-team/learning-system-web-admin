from config import TIMEZONE
import decimal
from hashlib import new
from prime_admin.globals import SECRETARYREFERENCE
from app.auth.models import User
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



@bp_lms.route('/cash-flow')
@login_required
def cash_flow():

    if current_user.role.name == "Secretary":
        form = CashFlowSecretaryForm()

    else:
        form = CashFlowAdminForm()
    
    _table_data = []

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    else:
        branches = Branch.objects

    orientators = Orientator.objects()

    scripts = [
        {'lms.static': 'js/cash_flow.js'},
    ]

    modals = [
        'lms/deposit_modal.html',
        'lms/withdraw_modal.html',
        'lms/profit_modal.html'
    ]

    return admin_table(
        CashFlow,
        fields=[],
        form=form,
        table_data=_table_data,
        heading="Cash Flow",
        title="Cash Flow",
        table_template="lms/cash_flow.html",
        scripts=scripts,
        modals=modals,
        branches=branches,
        orientators=orientators
        )


@bp_lms.route('/deposit', methods=['POST'])
@login_required
def deposit():
    form = DepositForm()
    
    try:
        new_deposit = CashFlow()
        new_deposit.date_deposit = form.date_deposit.data
        new_deposit.bank_name = form.bank_name.data
        new_deposit.account_no = form.account_no.data
        new_deposit.account_name = form.account_name.data
        new_deposit.amount = form.amount.data
        new_deposit.from_what = form.from_what.data
        new_deposit.by_who = form.by_who.data
        new_deposit.created_by = "{} {}".format(current_user.fname,current_user.lname)
        new_deposit.branch = current_user.branch
        new_deposit.type = "deposit"

        accounting = Accounting.objects(branch=current_user.branch.id).first()

        if accounting:
            if new_deposit.from_what == "Sales":
                new_deposit.balance = accounting.total_gross_sale + new_deposit.amount
                accounting.total_gross_sale = accounting.total_gross_sale + new_deposit.amount
            elif new_deposit.from_what == "Student Loan Payment":

                if accounting.final_fund1:
                    accounting.final_fund1 = accounting.final_fund1 + new_deposit.amount
                else:
                    accounting.final_fund1 = new_deposit.amount

                new_deposit.balance = accounting.final_fund1
        else:
            accounting = Accounting()
            accounting.branch = current_user.branch
            accounting.active_group = 1
            
            if new_deposit.from_what == "Sales":
                accounting.total_gross_sale = new_deposit.amount
            elif new_deposit.from_what == "Student Loan Payment":
                accounting.final_fund1 = new_deposit.amount
            new_deposit.balance = new_deposit.amount

        new_deposit.group = accounting.active_group
        new_deposit.save()
        accounting.save()

        flash('Deposit Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.cash_flow'))


@bp_lms.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    form = WithdrawForm()
    
    try:
        new_withdraw = CashFlow()
        new_withdraw.date_deposit = form.date_deposit.data
        new_withdraw.bank_name = form.bank_name.data
        new_withdraw.account_no = form.account_no.data
        new_withdraw.account_name = form.account_name.data
        new_withdraw.amount = form.amount.data
        new_withdraw.from_what = form.from_what.data
        new_withdraw.by_who = form.by_who.data
        new_withdraw.created_by = "{} {}".format(current_user.fname,current_user.lname)
        new_withdraw.branch = Branch.objects.get(id=form.branch.data)
        new_withdraw.type = "withdraw"

        accounting = Accounting.objects(branch=form.branch.data).first()

        if accounting:
            if new_withdraw.from_what == "Sales":
                accounting.total_gross_sale = accounting.total_gross_sale - new_withdraw.amount
                new_withdraw.balance = accounting.total_gross_sale
            elif new_withdraw.from_what == "Fund 1":
                accounting.final_fund1 = accounting.final_fund1 - new_withdraw.amount
                new_withdraw.balance = accounting.final_fund1
            elif new_withdraw.from_what == "Fund 2":
                accounting.final_fund2 = accounting.final_fund2 - new_withdraw.amount
                new_withdraw.balance = accounting.final_fund2
        else:
            accounting = Accounting()
            accounting.branch = new_withdraw.branch
            accounting.active_group = 1

            if new_withdraw.from_what == "Sales":
                accounting.total_gross_sale = 0 - new_withdraw.amount
            elif new_withdraw.from_what == "Fund 1":
                accounting.final_fund1 = 0 - new_withdraw.amount
            elif new_withdraw.from_what == "Fund 2":
                accounting.final_fund2 = 0 - new_withdraw.amount
            
            new_withdraw.balance = 0 - new_withdraw.amount

        new_withdraw.group = accounting.active_group
        new_withdraw.save()
        accounting.save()

        flash('Withdraw Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.cash_flow'))


@bp_lms.route('/dtbl/get-cash-flow')
def get_cash_flow():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    # search_value = "%" + request.args.get("search[value]") + "%"
    # column_order = request.args.get('column_order')
    branch_id = request.args.get('branch')
    from_what = request.args.get('from_what')

    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'totalGrossSales': 0.00,
            'remaining': 0.00,
            'net': 0.00,
            'fund1': 0.00,
            'fund2': 0.00,
            'finalFund1': 0.00,
            'finalFund2': 0.00
        }

        return jsonify(response)
        # bank_statements = CashFlow.objects.skip(start).limit(length)
        
    if current_user.role.name == "Secretary":
        accounting = Accounting.objects(branch=current_user.branch.id).first()
    else:
        accounting = Accounting.objects(branch=branch_id).first()

    if accounting:
        total_gross_sales = accounting.total_gross_sale
        remaining = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.05)
        net = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.55)
        fund1 = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.20)
        fund2 = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.20)
        final_fund1 = accounting.final_fund1 if accounting.final_fund1 is not None else 0.00
        final_fund2 = accounting.final_fund2 if accounting.final_fund2 is not None else 0.00

        if current_user.role.name == "Secretary":
            if from_what == "sales":
                bank_statements = CashFlow.objects(branch=current_user.branch.id).filter(group=accounting.active_group).filter(from_what="Sales").skip(start).limit(length)
            else: # fund
                bank_statements = CashFlow.objects(branch=current_user.branch.id).filter(group=accounting.active_group).filter(from_what__ne="Sales").skip(start).limit(length)
        else:
            if from_what == "sales":
                bank_statements = CashFlow.objects(branch=branch_id).filter(group=accounting.active_group).filter(from_what="Sales").skip(start).limit(length)
            else: # fund
                bank_statements = CashFlow.objects(branch=branch_id).filter(group=accounting.active_group).filter(from_what__ne="Sales").skip(start).limit(length)
        recordsTotal = bank_statements.count(),
        recordsFiltered = bank_statements.count(),
    else:
        total_gross_sales = 0.00
        remaining = 0.00
        net = 0.00
        fund1 = 0.00
        fund2 = 0.00
        final_fund1 = 0.00
        final_fund2 = 0.00
        recordsTotal = 0,
        recordsFiltered = 0,
        bank_statements = []

    _table_data = []

    if current_user.role.name == "Secretary":
        for statement in bank_statements:
            _table_data.append((
                statement.date_deposit,
                statement.bank_name,
                statement.account_no,
                statement.account_name,
                str(statement.amount),
                statement.from_what,
                statement.by_who,
                '',
                statement.group
            ))
    else:
        for statement in bank_statements:
            _table_data.append((
                statement.date_deposit,
                '' if statement.type == 'withdraw' else str(statement.amount),
                '' if statement.type == 'withdraw' else statement.from_what,
                '' if statement.type == "deposit" else str(statement.amount),
                str(statement.balance) if statement.balance is not None else '',
                '' if statement.type == "deposit" else statement.from_what,
                statement.by_who,
                '',
                statement.group
            ))

    response = {
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'data': _table_data,
        'totalGrossSales': str(total_gross_sales),
        'remaining': str(remaining),
        'net': str(net),
        'fund1': str(fund1),
        'fund2': str(fund2),
        'finalFund1': str(final_fund1),
        'finalFund2': str(final_fund2)
    }

    return jsonify(response)


@bp_lms.route('/profit', methods=['POST'])
@login_required
def profit():
    password = request.form['password']
    branch = request.form['branch']

    if not current_user.check_password(password):
        flash('Invalid password','error')
        return redirect(url_for('lms.cash_flow'))

    accounting = Accounting.objects(branch=branch).first()

    if accounting is None:
        flash('Error Occured','error')
        return redirect(url_for('lms.cash_flow'))

    remaining = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.05)
    net = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.55)
    fund1 = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.20)
    fund2 = decimal.Decimal(accounting.total_gross_sale) * decimal.Decimal(.20)
    previous_final_fund1 = accounting.final_fund1
    previous_final_fund2 = accounting.final_fund2 if accounting.final_fund2 is not None else '0.00'
    previous_total_gross_sale = accounting.total_gross_sale
    
    accounting.total_gross_sale = remaining

    accounting.final_fund1 = decimal.Decimal(accounting.final_fund1) + fund1

    if accounting.final_fund2:
        accounting.final_fund2 = decimal.Decimal(accounting.final_fund2) + fund2
    else:
        accounting.final_fund2 = fund2
    
    accounting.profits.append(
        {
            'date': datetime.now(TIMEZONE),
            'previous_total_gross_sale': Decimal128(previous_total_gross_sale),
            'new_total_gross_sale': Decimal128(accounting.total_gross_sale),
            'net': Decimal128(net),
            'remaining': Decimal128(remaining),
            'fund1': Decimal128(fund1),
            'fund2': Decimal128(fund2),
            'previous_final_fund1': Decimal128(previous_final_fund1),
            'previous_final_fund2': Decimal128(previous_final_fund2),
            'new_final_fund1': Decimal128(accounting.final_fund1),
            'new_final_fund2': Decimal128(accounting.final_fund2),
        }
    )

    accounting.active_group += 1
    accounting.save()

    flash('Proccessed Successfully!','success')

    return redirect(url_for('lms.cash_flow'))
