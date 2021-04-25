from app.auth.views.user import edit_user
from flask.json import jsonify
from prime_admin.forms import BranchEditForm, BranchForm, ContactPersonEditForm, ContactPersonForm, PartnerForm, SecretaryForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, ContactPerson
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/contact-persons')
@login_required
def contact_persons():
    form = ContactPersonForm()

    _table_data = []

    for contact_person in ContactPerson.objects:
        _table_data.append((
            contact_person.id,
            contact_person.fname,
            contact_person.lname,
            contact_person.created_by,
            contact_person.created_at,
            contact_person.updated_by,
            contact_person.updated_at,
        ))

    return admin_table(
        ContactPerson,
        fields=[],
        form=form,
        table_data=_table_data,
        create_url='lms.create_contact_person',
        edit_url='lms.edit_contact_person',
        view_modal_url='/learning-management/get-view-contact-person-data')


@bp_lms.route('/contact-persons/create',methods=['GET','POST'])
@login_required
def create_contact_person():
    form = ContactPersonForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.contact_persons'))

    try:
        contact_person = ContactPerson()

        contact_person.fname = form.fname.data
        contact_person.lname = form.lname.data

        contact_person.created_by = "{} {}".format(current_user.fname,current_user.lname)
        
        contact_person.save()

        flash('New Contact Person Added Successfully!','success')

        return redirect(url_for('lms.contact_persons'))

    except Exception as e:
        flash(str(e),'error')
        return redirect(url_for('lms.contact_persons'))


@bp_lms.route('/get-view-contact-person-data', methods=['GET'])
@login_required
def get_view_contact_person_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    _data = ContactPerson.objects(id=_id).values_list(_column)

    response = jsonify(result=str(_data[0]),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


@bp_lms.route('/contact-persons/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact_person(oid,**kwargs):
    contact_person = ContactPerson.objects.get_or_404(id=oid)
    form = ContactPersonEditForm(obj=contact_person)

    if request.method == "GET":

        return admin_edit(
            ContactPerson,
            form,
            'lms.edit_contact_person',
            oid,
            'lms.contact_persons')
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.contact_persons'))
        
    try:
        contact_person.fname = form.fname.data
        contact_person.lname = form.lname.data
        contact_person.updated_at = datetime.now()
        contact_person.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        
        contact_person.save()
        flash('Contact Person Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')

    return redirect(url_for('lms.contact_persons'))
