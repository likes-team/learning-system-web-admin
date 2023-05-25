from flask import render_template
from prime_admin import bp_lms



@bp_lms.route('/transactions')
def transactions():
    return render_template('lms/transactions/transactions_page.html', title='Transactions')
