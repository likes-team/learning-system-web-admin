from bson import ObjectId
from flask_login import login_required, current_user
from flask import redirect, url_for, request, flash, jsonify
from app import mongo
from app.admin.templating import admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch
from prime_admin.forms import BatchEditForm, BatchForm
from prime_admin.models_v2 import BatchV2, BranchV2
from prime_admin.utils.date import format_date



@bp_lms.route('/batches')
@login_required
def batches():
    form = BatchForm()

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Manager":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Admin":
        branches = Branch.objects

    table_data = []
    for batch in Batch.objects:
        table_data.append((
            batch.id,
            batch.active,
            batch.number,
            batch.branch.name if batch.branch is not None else '',
            batch.start_date,
            batch.created_by,
            batch.created_at_local,
            batch.updated_by,
            batch.updated_at_local
        ))
    return admin_table(
        Batch,
        fields=[],
        form=form,
        table_data=table_data,
        create_url='lms.create_batch',
        edit_url='lms.edit_batch',
        table_template='lms/batches/batch_table.html',
        view_modal_template="lms/batch_view_modal.html",
        branches=branches
    )


@bp_lms.route('/batches/<string:oid>')
def get_batch(oid):
    query = mongo.db.lms_batches.find_one({'_id': ObjectId(oid)})
    if query is None:
        pass
    
    batch = BatchV2(query)
    branch_id = batch.document.get('branch')
    if branch_id:
        query = mongo.db.lms_branches.find_one({'_id': ObjectId(branch_id)})
        branch = BranchV2(query)
    
    response = {
        'id': str(batch.get_id()),
        'no': batch.get_no(),
        'branch': str(branch.get_id()),
        'start_date': format_date(batch.get_start_date())
    }
    return jsonify(response)


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
        batch.start_date = form.start_date.data
        batch.created_by = "{} {}".format(current_user.fname,current_user.lname)
        batch.set_created_at()

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
            action_template="lms/batch_edit_action.html"
            )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.batches'))
        
    try:
        batch.number = form.number.data
        # batch.branch = Branch.objects.get_or_404(id=form.branch.data)
        batch.start_date = form.start_date.data
        batch.set_updated_at()
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
    response = jsonify({
        'result': True
    })
    batch = Batch.objects.get(id=batch_id)
    batch.active = True if status == 1 else False 
    batch.save()
    return response
    
