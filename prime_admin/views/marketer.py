import json
from urllib import response
from prime_admin.globals import MARKETERREFERENCE
from app.auth.models import Role, User
from flask.json import jsonify
from prime_admin.forms import ContactPersonEditForm
from flask_login import login_required, current_user
from app.admin.templating import admin_edit, admin_render_template
from prime_admin import bp_lms
from prime_admin.models import Branch, Marketer
from flask import redirect, url_for, request, flash, render_template
from app import mongo



@bp_lms.route('/marketers')
@login_required
def marketers():
    return render_template('lms/marketers/marketers.html', title="Marketers")


@bp_lms.route('/marketers/dt', methods=['GET'])
def fetch_marketers_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")

    total_records: int
    filtered_records: int

    if search_value != '':
        query = mongo.db.auth_users.find({'lname': {'$regex': search_value}, 'role': MARKETERREFERENCE}).skip(start).limit(length)
        total_records = query.count()
    else:
        query = mongo.db.auth_users.find({'role': MARKETERREFERENCE}).skip(start).limit(length)
        total_records = query.count(True)

    filtered_records = query.count()
    
    table_data = []
    
    for data in query:
        _id = str(data.get('_id', ''))
        lname = data.get('lname', '')
        fname = data.get('fname', '')
        created_by = data.get('created_by', '')
        created_at = data.get('created_at', '')
        updated_by = data.get('updated_by', '')
        updated_at = data.get('updated_at', '')
        
        table_data.append([
            _id,
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


@bp_lms.route('/marketers/<string:marketer_id>', methods=['GET'])
@login_required
def get_marketer(marketer_id):
    marketer: User = User.objects.get(id=marketer_id)

    response = {
        'status': 'success',
        'data': {
            'id': str(marketer.id),
            'fname': marketer.fname,
            'lname': marketer.lname,
        },
        'message': ""
    }
    return jsonify(response), 200


@bp_lms.route('/marketers/<string:marketer_id>/branches/dt')
@login_required
def get_marketer_branches_dt(marketer_id):
    try:
        marketer: User = User.objects.get(id=marketer_id)

        table_data = []
        
        for branch_id in marketer.branches:
            branch = Branch.objects.get(id=branch_id)
            table_data.append([branch.name])
        
        response = {
            'data': table_data
        }
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500
    

@bp_lms.route('/marketers/create',methods=['GET','POST'])
@login_required
def create_marketer():
    form = ContactPersonEditForm()

    if request.method == "GET":
        form.branches_inline.data = []
        form.add_branches_inline.data = Branch.objects()

        _scripts = [
            {'lms.static': 'js/partners.js'}
        ]
        return admin_render_template(Marketer, "lms/marketer_create.html", 'learning_management', form=form,\
            title="Create marketer", scripts=_scripts)

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.marketers'))

    try:
        marketer = User()

        marketer.fname = form.fname.data
        marketer.lname = form.lname.data

        branches_ids = request.form.getlist('branches[]')
        branches = []
        
        print(branches_ids)

        if branches_ids:
            for branch_id in branches_ids:
                branches.append(branch_id)
        
        marketer.branches = branches
        marketer.role = Role.objects(name='Marketer').first()
        marketer.username = marketer.fname.lower() + marketer.lname.lower()
        marketer.set_password('password')
        marketer.created_by = "{} {}".format(current_user.fname,current_user.lname)

        marketer.save()

        flash('New Contact Person Added Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.marketers'))


@bp_lms.route('/marketers/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_marketer(oid):
    contact_person = User.objects.get_or_404(id=oid)
    form = ContactPersonEditForm(obj=contact_person)

    if request.method == "GET":
        form.__heading__ = "Edit Marketer"
        form.__title__ = "Edit marketer"

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
            Marketer,
            form,
            'lms.edit_marketer',
            oid,
            'lms.marketers',
            scripts=_scripts,
            edit_template="lms/marketers/marketer_edit.html",
            modals=['auth/user_change_password_modal.html']
        )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.marketers'))
        
    # try:
    contact_person.fname = form.fname.data
    contact_person.lname = form.lname.data
    contact_person.is_employee = True if form.is_employee.data == 'on' else False
    contact_person.is_teacher = True if form.is_teacher.data == 'on' else False
    
    branches = []
    branch_ids = request.form.getlist('branches[]')

    if branch_ids:
        for b_id in branch_ids:
            branches.append(b_id)

    contact_person.branches = branches

    contact_person.set_updated_at()
    contact_person.updated_by = "{} {}".format(current_user.fname,current_user.lname)
    
    # contact_person.save()
    
    mongo.db.auth_users.update_one(
        {"_id": contact_person.id},
        {"$set": {
            "fname": contact_person.fname,
            "lname": contact_person.lname,
            "branches": contact_person.branches,
            "updated_at": contact_person.updated_at,
            "updated_by": contact_person.updated_by,
            "is_employee": contact_person.is_employee,
            "is_teacher": contact_person.is_teacher
        }})
    
    flash('Contact Person Updated Successfully!','success')

    # except Exception as e:
    #     flash(str(e),'error')

    return redirect(url_for('bp_auth.users'))
