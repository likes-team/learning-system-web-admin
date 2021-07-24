from flask.json import jsonify
from app.auth.models import Role, User
from prime_admin.forms import PartnerForm, SecretaryEditForm, SecretaryForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, Secretary
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/secretaries')
@login_required
def secretaries():
    form = SecretaryForm()

    _table_data = []

    secretary_role = Role.objects(name="Secretary").first()

    _secretaries = User.objects(role=secretary_role)

    for secretary in _secretaries:
        _table_data.append((
            secretary.id,
            secretary.fname,
            secretary.lname,
            secretary.branch.name if secretary.branch is not None else '',
            secretary.created_by,
            secretary.created_at,
            secretary.updated_by,
            secretary.updated_at
        ))

    return admin_table(
        Secretary,
        fields=[],
        form=form,
        table_data=_table_data,
        create_button=None,
        create_url=None,
        create_modal=False,
        # create_url='lms.create_secretary',
        edit_url='lms.edit_secretary',
        view_modal_url='/learning-management/get-view-secretary-data'
        )


@bp_lms.route('/get-view-secretary-data', methods=['GET'])
@login_required
def get_view_user_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    _data = User.objects(id=_id).values_list(_column)

    response = jsonify(result=str(_data[0]),column=_column)

    if _column == "branch" and _data[0] is not None:
        response = jsonify(result=str(_data[0].id),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


@bp_lms.route('/secretaries/create',methods=['GET','POST'])
@login_required
def create_secretary():
    form = SecretaryForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.secretaries'))

    try:
        secretary = User()

        secretary.fname = form.fname.data
        secretary.lname = form.lname.data
        secretary.branch = Branch.objects.get(id=form.branch.data)
        secretary.role = Role.objects(name="Secretary").first()
        secretary.username = form.username.data
        secretary.email = form.email.data if form.email.data != '' else None
        secretary.set_password("password")
        secretary.is_superuser = False

        secretary.created_by = "{} {}".format(current_user.fname,current_user.lname)

        secretary.save()

        flash('New Secretary Added Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.secretaries'))


@bp_lms.route('/secretaries/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_secretary(oid):
    secretary = User.objects.get_or_404(id=oid)
    form = SecretaryEditForm(obj=secretary)

    if request.method == "GET":

        return admin_edit(
            Secretary,
            form,
            'lms.edit_secretary',
            oid,
            'lms.secretaries',
            )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.secretaries'))
        
    try:
        secretary.fname = form.fname.data
        secretary.lname = form.lname.data
        secretary.branch = Branch.objects.get(id=form.branch.data)
        secretary.role = Role.objects(name="Secretary").first()
        secretary.username = form.username.data
        secretary.email = form.email.data if form.email.data != '' else None
        secretary.updated_at = datetime.now()
        secretary.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        
        secretary.save()
        flash('Secretary Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')

    return redirect(url_for('lms.secretaries'))
