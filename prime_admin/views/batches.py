from config import TIMEZONE
from prime_admin.views.branches import branches
from flask.json import jsonify
from app.auth.models import Role, User
from prime_admin.forms import BatchEditForm, BatchForm, PartnerForm, SecretaryEditForm, SecretaryForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/batches')
@login_required
def batches():
    form = BatchForm()

    _table_data = []

    for batch in Batch.objects:
        _table_data.append((
            batch.id,
            batch.active,
            batch.number,
            batch.branch.name if batch.branch is not None else '',
            batch.created_by,
            batch.created_at,
            batch.updated_by,
            batch.updated_at
        ))


    _scripts = [
        {'bp_admin.static': 'js/admin_table.js'},
        {'lms.static': 'js/batch.js'}
    ]

    return admin_table(
        Batch,
        fields=[],
        form=form,
        table_data=_table_data,
        create_url='lms.create_batch',
        edit_url='lms.edit_batch',
        table_template='lms/branch_table.html',
        view_modal_url='/learning-management/get-view-batch-data',
        view_modal_template="lms/batch_view_modal.html",
        scripts=_scripts
        )


@bp_lms.route('/get-view-batch-data', methods=['GET'])
@login_required
def get_view_batch_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    _data = Batch.objects(id=_id).values_list(_column)

    if _column == "branch":
        response = jsonify(result=str(_data[0].id),column=_column)
    else:
        response = jsonify(result=str(_data[0]),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


@bp_lms.route('/batches/create',methods=['GET','POST'])
@login_required
def create_batch():
    form = BatchForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.batches'))

    try:
        batch = Batch()

        batch.number = form.number.data
        batch.branch = Branch.objects.get_or_404(id=form.branch.data)
        batch.created_by = "{} {}".format(current_user.fname,current_user.lname)

        batch.save()

        flash('New Batch Added Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.batches'))


@bp_lms.route('/batches/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_batch(oid):
    batch = Batch.objects.get_or_404(id=oid)
    form = BatchEditForm(obj=batch)

    if request.method == "GET":
        
        return admin_edit(
            Batch,
            form,
            'lms.edit_batch',
            oid,
            'lms.batches',
            )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.batches'))
        
    try:
        batch.number = form.number.data
        # batch.branch = Branch.objects.get_or_404(id=form.branch.data)
        batch.updated_at = datetime.now(TIMEZONE)
        batch.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        
        batch.save()
        flash('Batch Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')

    return redirect(url_for('lms.batches'))

@bp_lms.route('/batches/<string:batch_id>/set-active', methods=['POST'])
@login_required
def set_active(batch_id):
    status = request.json['status']
    print(status)
    response = jsonify({
        'result': True
    })

    try:
        batch = Batch.objects.get(id=batch_id)

        batch.active = True if status == 1 else False 
        batch.save()

    except Exception:
        return jsonify({'result': False})

    return response
    
