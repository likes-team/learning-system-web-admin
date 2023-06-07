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
        Settings, 'lms//settings/other_expenses_settings_page.html', 'learning_management'
    )
    

@bp_lms.route('/settings/examination/batch-numbers')
def batch_numbers_settings():
    return admin_render_template(
        Settings, 'lms/settings/examination/batch_numbers_settings_page.html', 'learning_management'
    )


@bp_lms.route('/settings/examination/sessions')
def sessions_settings():
    return admin_render_template(
        Settings, 'lms/settings/examination/sessions_settings_page.html', 'learning_management'
    )


@bp_lms.route('/settings/examination/industries')
def industries_settings():
    return admin_render_template(
        Settings, 'lms/settings/examination/industries_settings_page.html', 'learning_management'
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


@bp_lms.route('/settings/examination/batch-numbers/create', methods=['POST'])
def create_batch_number():
    description = request.form['description']
    
    if description == "":
        return redirect(url_for('lms.batch_numbers_settings'))

    mongo.db.lms_examination_batch_numbers.insert_one({
        'description': description
    })
    flash("Added successfully!", 'success')
    return redirect(url_for('lms.batch_numbers_settings'))


@bp_lms.route('/settings/examination/session/create', methods=['POST'])
def create_session():
    description = request.form['description']
    
    if description == "":
        return redirect(url_for('lms.sessions_settings'))

    mongo.db.lms_examination_sessions.insert_one({
        'description': description
    })
    flash("Added successfully!", 'success')
    return redirect(url_for('lms.sessions_settings'))
    
    

@bp_lms.route('/settings/examination/industries/create', methods=['POST'])
def create_industry():
    description = request.form['description']
    
    if description == "":
        return redirect(url_for('lms.industries_settings'))

    mongo.db.lms_configurations.update_one({
        'name': "industries"
    }, {"$push": {
        'values': description
    }})
    flash("Added successfully!", 'success')
    return redirect(url_for('lms.industries_settings'))
