from datetime import datetime
from flask import request
from flask.json import jsonify
from flask.templating import render_template
from flask_login import login_required, current_user
from prime_admin import bp_lms
from prime_admin.models import Branch, Dashboard
from app.admin.templating import admin_dashboard, DashboardBox
from prime_admin.services.dashboard import DashboardService, ChartService, SalesAndExpensesChart
from prime_admin.utils import currency, expenses


@bp_lms.route('/')
@bp_lms.route('/dashboard')
@login_required
def dashboard():
    if current_user.role.name not in ["Admin", 'Secretary', 'Partner', "Manager"]:
        return render_template('auth/authorization_error.html')

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Manager":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Admin":
        branches = Branch.objects()
        
    options = {
        'branches': branches,
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
    sales_today = DashboardService(branch=branch).get_sales_today()
    response = {
        'status': 'success',
        'sales_today': sales_today,
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


@bp_lms.route('/dashboard/fetch-gross-sales-breakdown')
def fetch_gross_sales_breakdown():
    date_from = request.args['date_from']
    date_to = request.args['date_to']
    branch = request.args['branch']

    chart = SalesAndExpensesChart(date_from=date_from, date_to=date_to, branch=branch)
    registration_sales_per_month = chart.get_registration_sales()
    accommodation_sales_per_month = chart.get_accommodation_sales()
    store_sales_per_month = chart.get_store_sales()
    
    registration_sales = 0
    accommodation_sales = 0
    store_sales = 0

    for sale in registration_sales_per_month:
        registration_sales += sale['amount']

    for sale in accommodation_sales_per_month:
        accommodation_sales += sale['amount']

    for sale in store_sales_per_month:
        store_sales += sale['amount']
    
    total = registration_sales + accommodation_sales + store_sales    
    response = {
        'labels': ['Enrollee', 'Accommodation', 'Store'],
        'gross_sales_breakdown': [
            currency.format_to_str_php(registration_sales),
            currency.format_to_str_php(accommodation_sales),
            currency.format_to_str_php(store_sales)
        ],
        'total': currency.format_to_str_php(total)
    }
    return jsonify(response), 200


@bp_lms.route('/dashboard/fetch-expenses-breakdown')
def fetch_expenses_breakdown():
    date_from = request.args['date_from']
    date_to = request.args['date_to']
    branch = request.args['branch']
    
    chart = SalesAndExpensesChart(date_from=date_from, date_to=date_to, branch=branch)
    expenses_per_category = chart.get_expenses_per_category()
    labels = [
        'UTILITIES', 'OFFICE SUPPLIES', 'SALARY', 'REBATES', 'REFUND', 'OTHER EXPENSES',
        'BIR', 'BUSINESS PERMIT', 'EMP. BENEFITS', 'BOOK. RET. FEE',
        'SNPL FEE'
    ]
    expenses_breakdown = [0 for _ in range(len(labels))]
    
    total = 0
    for expense in expenses_per_category:
        try:
            index = labels.index(expenses.CATEGORIES[expense['category']])
        except KeyError:
            print(expense['category'])
            continue
        total += expense['amount']
        expenses_breakdown[index] = currency.format_to_str_php(expense['amount'])
    
    response = {
        'labels': labels,
        'expenses_breakdown': expenses_breakdown,
        'total': currency.format_to_str_php(total)
    }
    return jsonify(response), 200


@bp_lms.route('/dashboard/fetch-net-lose')
def fetch_net_lose():
    date_from = request.args['date_from']
    date_to = request.args['date_to']
    branch = request.args['branch']

    chart = SalesAndExpensesChart(
        date_from=date_from, date_to=date_to, branch=branch)
    chart.calculate_sales_and_expenses_per_month(format_to_currency=False)

    total_net = 0
    total_lose = 0
    total = 0
    for net in chart.get_nets():
        total += net
 
    if total >= 0:
        total_net = total
    elif total < 0:
        total_lose = total
            
    response = {
        'labels': ['NET', 'LOSE'],
        'data': [currency.format_to_str_php(total_net), currency.format_to_str_php(total_lose)]
    }
    return jsonify(response), 200


@bp_lms.route('/dashboard/fetch-all-branches-net-lose')
def fet_all_branches_net_lose():
    date_from = request.args['date_from']
    date_to = request.args['date_to']

    chart = SalesAndExpensesChart(
        date_from=date_from,
        date_to=date_to,
        per='branch'
    )
    response = chart.calculate_net_lose_per_branch()
    return jsonify(response), 200


@bp_lms.route('/api/dashboard/get-chart-data/<string:branch_id>', methods=['GET'])
@login_required
def get_chart_data(branch_id):
    date_from = request.args['date_from']
    date_to = request.args['date_to']

    chart = SalesAndExpensesChart(
        date_from=date_from, date_to=date_to, branch=branch_id)
    chart.calculate_sales_and_expenses_per_month()

    no_of_students = []
    response = {
        'labels': chart.get_month_labels(),
        'gross_sales': chart.get_gross_sales(),
        'net': chart.get_nets(),
        'maintaining_sales': chart.get_maintaining_sales(),
        'expenses': chart.get_expenses(),
        'no_of_students': no_of_students
    }
    return jsonify(response), 200
