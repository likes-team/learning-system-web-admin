from datetime import datetime
import decimal
from prime_admin.globals import get_date_now
from flask import request
from flask.json import jsonify
from flask.templating import render_template
from flask_login import login_required, current_user
from prime_admin import bp_lms
from prime_admin.models import Branch, CashFlow, Dashboard, Registration
from app.admin.templating import admin_dashboard, DashboardBox
from mongoengine.queryset.visitor import Q
from prime_admin.services.dashboard import DashboardService, ChartService
from prime_admin.utils import currency



JANSTART = datetime(2021, 1, 1)
JANEND = datetime(2021, 1, 31)
FEBSTART = datetime(2021, 2, 1)
FEBEND = datetime(2021, 2, 28)
MARSTART = datetime(2021, 3, 1)
MAREND = datetime(2021, 3, 31)
APRSTART = datetime(2021, 4, 1)
APREND = datetime(2021, 4, 30)
MAYSTART = datetime(2021, 5, 1)
MAYEND = datetime(2021, 5, 31)
JUNSTART = datetime(2021, 6, 1)
JUNEND = datetime(2021, 6, 30)
JULSTART = datetime(2021, 7, 1)
JULEND = datetime(2021, 7, 31)
AUGSTART = datetime(2021, 8, 1)
AUGEND = datetime(2021, 8, 31)
SEPSTART = datetime(2021, 9, 1)
SEPEND = datetime(2021, 9, 30)
OCTSTART = datetime(2021, 10, 1)
OCTEND = datetime(2021, 10, 31)
NOVSTART = datetime(2021, 11, 1)
NOVEND = datetime(2021, 11, 30)
DECSTART = datetime(2021, 12, 1)
DECEND = datetime(2021, 12, 31)


@bp_lms.route('/')
@bp_lms.route('/dashboard')
@login_required
def dashboard():
    if current_user.role.name not in ["Admin", 'Secretary', 'Partner']:
        return render_template('auth/authorization_error.html')

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Admin":
        branches = Branch.objects

    dashboard_service = DashboardService()
    sales_today = dashboard_service.get_sales_today()
    dashboard_service.reset_match()
    total_installment = dashboard_service.get_total_installment()
    total_full_payment = dashboard_service.get_total_full_payment()
    total_premium_payment = dashboard_service.get_total_premium_payment()
    total = dashboard_service.get_total()
    
    options = {
        'branches': branches,
        'box1': DashboardBox("Number of enrollees","Current", 0),
        'box2': DashboardBox("Total Sales","Montly", 0),
        'box3': DashboardBox("Gross Income","Total users", 0),
        'scripts': [{'lms.static': 'js/utils.js'}],
        'sales_today': sales_today,
        'total_installment': total_installment,
        'total_full_payment': total_full_payment,
        'total_premium_payment': total_premium_payment,
        'total': total
    }
    return admin_dashboard(
        Dashboard,
        **options,
        dashboard_template="lms/dashboard.html",
        module="learning_management"
    )


@bp_lms.route('/dashboard/fetch-chart-sales-today', methods=['GET'])
def fetch_chart_sales_today():
    branch = request.args['branch'] if request.args['branch'] != 'all' else None
    data = ChartService.fetch_chart_sales_today(branch)
    response = {
        'status': 'success',
        'data': data
    }
    return jsonify(response), 200


@bp_lms.route('/dashboard/fetch-sales-breakdown', methods=['GET'])
def fetch_sales_breakdown():
    date_from = request.args['date_from'] if request.args['date_from'] != '' else None
    date_to = request.args['date_to'] if request.args['date_to'] != '' else None
    branch = request.args['branch'] if request.args['branch'] != 'all' else None

    dashboard_service = DashboardService(
        date_from=date_from,
        date_to=date_to,
        branch=branch
    )
    total_installment = dashboard_service.get_total_installment()
    total_full_payment = dashboard_service.get_total_full_payment()
    total_premium_payment = dashboard_service.get_total_premium_payment()
    total = dashboard_service.get_total()

    response = {
        'status': 'success',
        'data': {
            'total_installment': total_installment,
            'total_full_payment': total_full_payment,
            'total_premium_payment': total_premium_payment,
            'total': total
        }
    }
    return jsonify(response), 200


@bp_lms.route('/api/dashboard/get-chart-data/<string:branch_id>', methods=['GET'])
@login_required
def get_chart_data(branch_id):
    date_from = request.args['date_from']
    date_to = request.args['date_to']
    
    labels = ChartService.get_month_labels(date_from, date_to)
    labels_count = len(labels)
    gross_sales = [0 for _ in range(labels_count)]
    expenses = [0 for _ in range(labels_count)]
    maintaining_sales = [85000 for _ in range(labels_count)]
    nets = [0 for _ in range(labels_count)]
    no_of_students = []
    raw_gross_sales = ChartService.get_gross_sales_per_month(date_from=date_from, date_to=date_to ,branch=branch_id)
    raw_expenses = ChartService.get_expenses_per_month(date_from=date_from, date_to=date_to ,branch=branch_id)

    for gross_sale in raw_gross_sales:
        index = labels.index(gross_sale['date'])
        gross_sales[index] = gross_sale['amount']
        
    for expense in raw_expenses:
        index = labels.index(expense['date'])
        expenses[index] = expense['amount']
    
    for i in range(labels_count):
        nets[i] = currency.format_to_str_php(gross_sales[i] - expenses[i])
    
    for i in range(len(expenses)):
        expenses[i] = currency.format_to_str_php(expenses[i])
    
    for i in range(len(gross_sales)):
        gross_sales[i] = currency.format_to_str_php(gross_sales[i])
    
    response = {
        'labels': labels,
        'gross_sales': gross_sales,
        'net': nets,
        'maintaining_sales': maintaining_sales,
        'expenses': expenses,
        'no_of_students': no_of_students
    }
    return jsonify(response), 200
