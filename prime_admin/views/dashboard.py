from datetime import datetime
from flask import request
from flask.json import jsonify
from flask.templating import render_template
from flask_login import login_required, current_user
from prime_admin import bp_lms
from prime_admin.models import Branch, Dashboard
from app.admin.templating import admin_dashboard, DashboardBox
from prime_admin.services.dashboard import DashboardService, ChartService, SalesAndExpensesChart
from prime_admin.utils import currency



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
    
    chart = SalesAndExpensesChart(date_from=date_from, date_to=date_to, branch=branch_id)
    chart.calculate_sales_and_expenses_per_month()

    no_of_students = []
    response = {
        'labels': chart.get_month_labels(),
        'gross_sales': chart.get_gross_sales_per_month(),
        'net': chart.get_nets(),
        'maintaining_sales': chart.get_maintaining_sales(),
        'expenses': chart.get_expenses(),
        'no_of_students': no_of_students
    }
    return jsonify(response), 200
