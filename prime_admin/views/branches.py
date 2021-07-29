from config import TIMEZONE
from app.auth.views.user import edit_user
from flask.json import jsonify
from prime_admin.forms import BranchEditForm, BranchForm, PartnerForm, SecretaryForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/branches')
@login_required
def branches():
    form = BranchForm()

    _table_data = []

    for branch in Branch.objects:
        _table_data.append((
            branch.id,
            branch.name,
            branch.created_by,
            branch.created_at,
            branch.updated_by,
            branch.updated_at,
        ))

    return admin_table(
        Branch,
        fields=[],
        form=form,
        table_data=_table_data,
        create_url='lms.create_branch',
        edit_url='lms.edit_branch',
        view_modal_url='/learning-management/get-view-branch-data')


@bp_lms.route('/get-view-branch-data', methods=['GET'])
@login_required
def get_view_branch_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    _data = Branch.objects(id=_id).values_list(_column)

    response = jsonify(result=str(_data[0]),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response

@bp_lms.route('/branches/create',methods=['GET','POST'])
@login_required
def create_branch():
    form = BranchForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.branches'))

    try:
        branch = Branch()

        branch.name = form.name.data
        branch.address = form.address.data
        branch.created_by = "{} {}".format(current_user.fname,current_user.lname)
        
        branch.save()

        flash('New Branch Added Successfully!','success')

        return redirect(url_for('lms.branches'))

    except Exception as e:
        flash(str(e),'error')
        return redirect(url_for('lms.branches'))


@bp_lms.route('/branches/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_branch(oid,**kwargs):
    branch = Branch.objects.get_or_404(id=oid)
    form = BranchEditForm(obj=branch)

    if request.method == "GET":

        return admin_edit(
            Branch,
            form,
            'lms.edit_branch',
            oid,
            'lms.branches')
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.branches'))
        
    try:
        
        branch.name = form.name.data
        branch.address = form.address.data
        branch.updated_at = datetime.now(TIMEZONE)
        branch.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        
        branch.save()
        flash('Branch Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.branches'))