import decimal

from flask.json import jsonify
from prime_admin.functions import generate_number
from prime_admin.forms import ExpensesForm, RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Expenses, Inventory
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime


@bp_lms.route('/expenses')
@login_required
def expenses():
    form = ExpensesForm()

    scripts = [
        {'lms.static': 'js/expenses.js'}
    ]

    return admin_table(
        Expenses,
        fields=[],
        form=form,
        table_data=[],
        heading="",
        subheading='',
        title='Expenses',
        scripts=scripts,
        table_template='lms/expenses.html',
        create_url='lms.create_expenses',
    )


@bp_lms.route('/expenses/create',methods=['GET','POST'])
@login_required
def create_expenses():
    form = ExpensesForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.contact_persons'))

    try:
        _expenses = Expenses()
        _expenses.inventory = Inventory.objects.get(id=form.inventory.data)
        _expenses.uom = form.uom.data
        _expenses.quantity = decimal.Decimal(form.quantity.data)
        _expenses.price = decimal.Decimal(form.price.data)
        _expenses.total = _expenses.quantity * _expenses.price

        _expenses.created_by = "{} {}".format(current_user.fname,current_user.lname)
        
        _expenses.save()

        flash('New Expenses Added Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.expenses'))


@bp_lms.route('/dtbl/expenses')
def get_dtbl_expenses():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    # search_value = "%" + request.args.get("search[value]") + "%"
    # column_order = request.args.get('column_order')
    branch_id = request.args.get('branch')
    description_id = request.args.get('description')
    # schedule = request.args.get('schedule')

    if branch_id != '':
        # _expenses = Expenses.objects(branch=branch_id)[start:length]
        # sales_today = Registration.objects(created_at__gte=datetime.now().date()).filter(status='registered').filter(branch=branch_id).sum('amount')
        _expenses = Expenses.objects[start:length]
    else:
        _expenses = Expenses.objects[start:length]
        # sales_today = Registration.objects(status='registered').filter(created_at__gte=datetime.now().date()).sum('amount')

    if description_id != 'all':
        print("TESTSET")
        _expenses = _expenses.filter(inventory=description_id)
    # if schedule != 'all':
    #     registrations = registrations.filter(schedule=schedule)
    print(_expenses)

    _table_data = []

    for exp in _expenses:
        _table_data.append([
            exp.created_at,
            exp.inventory.description,
            str(exp.price),
            exp.quantity,
            str(exp.total),
        ])

    # total_installment = registrations.filter(payment_mode='installment').sum('amount')
    # total_full_payment = registrations.filter(payment_mode='full_payment').sum('amount')
    # total_payment = registrations.sum('amount')

    # print(sales_today)

    response = {
        'draw': draw,
        'recordsTotal': _expenses.count(),
        'recordsFiltered': _expenses.count(),
        'data': _table_data,
        # 'totalInstallment': total_installment,
        # 'totalFullPayment': total_full_payment,
        # 'totalPayment': total_payment,
        # 'salesToday': sales_today
    }

    return jsonify(response)