import pymongo
from datetime import datetime
from flask import redirect, url_for, request, flash
from flask_login import login_required, current_user
from flask.json import jsonify
from app import mongo
from app.admin.templating import admin_render_template, admin_edit
from config import TIMEZONE
from app.auth.models import Role, User
from prime_admin.forms import ContactPersonEditForm
from prime_admin.globals import PARTNERREFERENCE
from prime_admin import bp_lms
from prime_admin.models import Branch, Partner



@bp_lms.route('/partners')
@login_required
def contact_persons():
    return admin_render_template(
        Partner,
        "lms/partners.html",
        'learning_management',
        title="Partners"
    )


@bp_lms.route('/partners/dt', methods=['GET'])
def fetch_partners_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")

    total_records: int
    filtered_records: int

    if search_value != '':
        query = mongo.db.auth_users.find({'lname': {'$regex': search_value, '$options' : 'i'}, 'role': PARTNERREFERENCE}).skip(start).limit(length)
        total_records = query.count()
    else:
        query = mongo.db.auth_users.find({'role': PARTNERREFERENCE}).skip(start).limit(length)
        total_records = query.count(True)

    # query = mongo.db.auth_users.find({}).sort('date', pymongo.DESCENDING).skip(start).limit(length)
    filtered_records = query.count()
    
    table_data = []
    
    for data in query:
        lname = data.get('lname', '')
        fname = data.get('fname', '')
        created_by = data.get('created_by', '')
        created_at = data.get('created_at', '')
        updated_by = data.get('updated_by', '')
        updated_at = data.get('updated_at', '')
        
        table_data.append([
            str(),
            lname,
            fname,
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


@bp_lms.route('/contact-persons/create',methods=['GET','POST'])
@login_required
def create_contact_person():
    form = ContactPersonEditForm()

    if request.method == "GET":

        form.branches_inline.data = []
        form.add_branches_inline.data = Branch.objects()

        _scripts = [
            {'lms.static': 'js/partners.js'}
        ]
        return admin_render_template(Partner, "lms/partner_create.html", 'learning_management', form=form,\
            title="Create partner", scripts=_scripts)

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.contact_persons'))

    try:
        contact_person = User()

        contact_person.fname = form.fname.data
        contact_person.lname = form.lname.data

        branches_ids = request.form.getlist('branches[]')
        if branches_ids:
            branches = []
            for branch_id in branches_ids:
                branches.append(branch_id)
        
        contact_person.branches = branches
        contact_person.role = Role.objects(name='Partner').first()
        contact_person.username = contact_person.fname.lower() + contact_person.lname.lower()
        contact_person.set_password('password')
        contact_person.created_by = "{} {}".format(current_user.fname,current_user.lname)

        contact_person.save()

        flash('New Contact Person Added Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.contact_persons'))


@bp_lms.route('/get-view-contact-person-data', methods=['GET'])
@login_required
def get_view_contact_person_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    _data = User.objects(id=_id).values_list(_column)

    response = jsonify(result=str(_data[0]),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


@bp_lms.route('/contact-persons/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact_person(oid):
    contact_person = User.objects.get_or_404(id=oid)
    form = ContactPersonEditForm(obj=contact_person)

    if request.method == "GET":
        current_branches_list = User.objects.get(id=oid).branches
        current_branches = []
        
        add_branches_list = Branch.objects
        add_branches = []

        for branch in current_branches_list:
            current_branches.append(Branch.objects.get(id=branch))

        for branch in add_branches_list:
            if str(branch.id) not in current_branches_list:
                add_branches.append(branch)

        form.branches_inline.data = current_branches
        form.add_branches_inline.data = add_branches

        _scripts = [
            {'lms.static': 'js/partners.js'}
        ]

        return admin_edit(
            Partner,
            form,
            'lms.edit_contact_person',
            oid,
            'lms.contact_persons',
            scripts=_scripts,
            edit_template="lms/partner_edit.html"
            )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.contact_persons'))
        
    try:
        contact_person.fname = form.fname.data
        contact_person.lname = form.lname.data
        
        branches = []
        branch_ids = request.form.getlist('branches[]')

        if branch_ids:
            for b_id in branch_ids:
                branches.append(b_id)

        contact_person.branches = branches

        contact_person.set_updated_at()
        contact_person.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        
        contact_person.save()
        flash('Contact Person Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')

    return redirect(url_for('lms.contact_persons'))
