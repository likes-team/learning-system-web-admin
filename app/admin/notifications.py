from flask import render_template
from flask_login import login_required
from app.admin import bp_admin



@bp_admin.route('/notifications/no-url-view')
@login_required
def no_view_url():
    return render_template('admin/notifications/no_view_url.html'), 400


@bp_admin.route('notifications/under-construction')
@login_required
def under_construction():
    return render_template('admin/notifications/under_construction.html'), 400