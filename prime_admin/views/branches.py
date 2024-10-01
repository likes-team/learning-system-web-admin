from flask.json import jsonify
from prime_admin.forms import BranchEditForm, BranchForm, PartnerForm, SecretaryForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, Teacher
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime
from prime_admin.models_v2 import BranchV2
from prime_admin.utils.date import format_date
from bson import ObjectId
from app import mongo



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
            branch.created_at_local,
            branch.updated_by,
            branch.updated_at_local,
        ))

    return admin_table(
        Branch,
        fields=[],
        form=form,
        table_data=_table_data,
        create_url='lms.create_branch',
        edit_url='lms.edit_branch',
        table_template='lms/branches/branch_table.html',
        view_modal_template="lms/branch_view_modal.html"
    )


@bp_lms.route('/get-view-branch-data', methods=['GET'])
@login_required
def get_view_branch_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    _data = Branch.objects(id=_id).values_list(_column)

    if _column == "teacher":
        response = jsonify(result=str(_data[0].id),column=_column)
    else:
        response = jsonify(result=str(_data[0]),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


@bp_lms.route('/branches/<string:oid>')
def get_branch(oid):
    query = mongo.db.lms_branches.find_one({'_id': ObjectId(oid)})
    if query is None:
        pass
    
    branch = BranchV2(query)
    teacher_id = branch.document.get('teacher')
    
    response = {
        'id': str(branch.get_id()),
        'name': branch.get_name(),
        'address': branch.get_address(),
        'teacher': str(teacher_id) if teacher_id is not None else '',
    }
    return jsonify(response)

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
        branch.teacher = Teacher.objects.get_or_404(id=form.teacher.data)
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
            'lms.branches',
            action_template="lms/batch_edit_action.html"
        )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.branches'))
        
    try:
        
        branch.name = form.name.data
        branch.address = form.address.data
        branch.teacher = Teacher.objects.get_or_404(id=form.teacher.data)
        branch.set_updated_at()
        branch.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        
        branch.save()
        flash('Branch Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.branches'))


@bp_lms.route('/api/branches/<string:branch_id>/batches')
def get_branch_batches(branch_id):
    data = []

    if branch_id == "all":
        response = jsonify({
            'data': data
        })

        return response
    else:
        batches = Batch.objects(branch=branch_id)

    for batch in batches:
        data.append(
            {
                'id': str(batch.id),
                'number': batch.number
            }
        )        

    response = jsonify({
        'data': data
    })

    return response