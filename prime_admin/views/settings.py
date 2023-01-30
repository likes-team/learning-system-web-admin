from flask import request, redirect, url_for, flash
from app.admin.templating import admin_render_template
from app import mongo
from prime_admin import bp_lms
from prime_admin.models import Settings



@bp_lms.route('/settings')
def settings():
    return admin_render_template(
        Settings, "lms/settings_page.html", 'learning_management'
        )
    
    
@bp_lms.route('/settings/other-expenses')
def other_expenses_settings():
    return admin_render_template(
        Settings, 'lms/other_expenses_settings_page.html', 'learning_management'
    )
    

@bp_lms.route('/settings/other-expenses/create', methods=['POST'])
def create_other_expenses():
    description = request.form['description']
    
    if description == "":
        return redirect(url_for('lms.other_expenses_settings'))

    mongo.db.lms_other_expenses_items.insert_one({
        'description': description.upper()
    })
    flash("Added successfully!", 'success')
    return redirect(url_for('lms.other_expenses_settings'))
    