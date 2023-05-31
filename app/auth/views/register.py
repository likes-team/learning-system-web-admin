from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user
from app import mongo
from app.auth import bp_auth
from app.auth.models import Role, User
from app.auth.forms import RegisterForm
from app.admin import admin_urls
from app.auth import auth_templates
from prime_admin.models import Branch



@bp_auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for(admin_urls['admin']))

        branches = Branch.objects()

        positions = Role.objects(name__ne='Admin')

        return render_template(auth_templates['register'], \
            title=current_app.config['ADMIN']['APPLICATION_NAME'],
            form=form,
            branches=branches,
            positions=positions
            )

    role = Role.objects.get(id=form.position.data)

    if role.name not in ['Secretary', 'Admin', 'Marketer', 'Partner', 'Manager']:
        flash('Sorry, only Secretaries and Marketers can be registered at the moment','error')
        return redirect(url_for('bp_auth.register'))

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_auth.register'))

    check_fname = mongo.db.auth_users.find({'fname': form.fname.data}).count()
    check_lname = mongo.db.auth_users.find({'lname': form.lname.data}).count()
    if check_fname > 0 and check_lname > 0:
        flash('User already exists','error')
        return redirect(url_for('bp_auth.register'))


    try:
        user = User()
        # user.custom_id = 
        user.username = form.username.data
        user.fname = form.fname.data
        user.lname = form.lname.data
        user.email = form.email.data if form.email.data != '' else None
        user.role = Role.objects.get(id=form.position.data)
        user.set_password(form.password.data)
        user.is_superuser = False
        user.active = False
        user.father_name = form.father_name.data
        user.mother_name = form.mother_name.data
        user.nickname = form.nickname.data
        user.date_of_birth = form.date_of_birth.data
        user.contact_no = form.contact_no.data
        user.address = form.address.data

        if user.role.name in ['Partner', 'Marketer', 'Manager']:
            user.branches.append(form.branch.data)
        else:
            user.branch = Branch.objects.get(id=form.branch.data)

        user.save()
        flash('Account created successfully, please wait for the admin to approve your account','success')
        return redirect(url_for('bp_auth.login'))
    except Exception as e:
        flash(str(e),'error')
        return redirect(url_for('bp_auth.register'))

