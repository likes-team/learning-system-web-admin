from flask.json import jsonify
from app.auth.models import Role, User
from prime_admin.forms import PartnerForm, SecretaryEditForm, SecretaryForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Branch, Secretary
from flask import redirect, url_for, request, current_app, flash
from app import mongo
from datetime import datetime
from config import TIMEZONE
from prime_admin.globals import SECRETARYREFERENCE



@bp_lms.route('/secretaries')
@login_required
def secretaries():
    return admin_render_template(
        Secretary,
        'lms/secretaries.html',
        'learning_management',
        title="Secretaries"
    )
    
    # form = SecretaryForm()
    # _table_data = []
    # secretary_role = Role.objects(name="Secretary").first()
    # _secretaries = User.objects(role=secretary_role)
    # for secretary in _secretaries:
    #     _table_data.append((
    #         secretary.id,
    #         secretary.fname,
    #         secretary.lname,
    #         secretary.branch.name if secretary.branch is not None else '',
    #         secretary.created_by,
    #         secretary.created_at_local,
    #         secretary.updated_by,
    #         secretary.updated_at_local
    #     ))

    # return admin_table(
    #     Secretary,
    #     fields=[],
    #     form=form,
    #     table_data=_table_data,
    #     create_button=None,
    #     create_url=None,
    #     create_modal=False,
    #     # create_url='lms.create_secretary',
    #     edit_url='lms.edit_secretary',
    #     view_modal_url='/learning-management/get-view-secretary-data'
    #     )


@bp_lms.route('/secretaries/dt', methods=['GET'])
def fetch_secretaries_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")

    total_records: int
    filtered_records: int

    if search_value != '':
        query = list(mongo.db.auth_users.aggregate([
            {"$match": {'lname': {'$regex': search_value}, 'role': SECRETARYREFERENCE}},
            {"$lookup": {
                'from': 'lms_branches',
                'localField': 'branch',
                'foreignField': '_id',
                'as': 'branch'
                }
            }]))
        total_records = len(query)
    else:
        query = list(mongo.db.auth_users.aggregate([
            {"$match": {'role': SECRETARYREFERENCE}},
            {"$lookup": {
                'from': 'lms_branches',
                'localField': 'branch',
                'foreignField': '_id',
                'as': 'branch'
                }
            },
            {"$skip": start},
            {"$limit": length},
            ]))
        total_records = mongo.db.auth_users.find({'role': SECRETARYREFERENCE}).count()

    filtered_records = len(query)
    
    table_data = []
    
    for data in query:
        lname = data.get('lname', '')
        fname = data.get('fname', '')
        branch = data.get('branch', [{'name': ''}])[0]
        created_by = data.get('created_by', '')
        created_at = data.get('created_at', '')
        updated_by = data.get('updated_by', '')
        updated_at = data.get('updated_at', '')
        
        table_data.append([
            str(),
            lname,
            fname,
            branch['name'],
            created_by,
            created_at,
            updated_by,
            updated_at,
        ])

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }

    return jsonify(response)


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
        secretary.set_updated_at()
        secretary.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        
        secretary.save()
        flash('Secretary Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')

    return redirect(url_for('lms.secretaries'))
