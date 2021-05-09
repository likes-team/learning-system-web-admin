import decimal
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, ContactPerson, Registration
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime
from bson.decimal128 import Decimal128


@bp_lms.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    registration_generated_number = ""
    
    last_registration_number = Registration.objects().order_by('-registration_number').first()

    date_now = datetime.now()

    if last_registration_number:
        registration_generated_number = generate_number(date_now, last_registration_number.registration_number)
    else:
        registration_generated_number = str(date_now.year) + '%02d' % date_now.month + "0001"

    form = RegistrationForm()

    if request.method == "GET":
        
        contact_persons = ContactPerson.objects
        branches = Branch.objects

        form.batch_number.data = Batch.objects(active=True)

        data = {
            'registration_generated_number': registration_generated_number,
            'contact_persons': contact_persons,
            'branches': branches
        }

        _scripts = [
            {'lms.static': 'js/registration.js'}
        ]

        return admin_render_template(
            Registration,
            'lms/registration.html',
            'learning_management',
            form=form,
            data=data,
            scripts=_scripts,
            title="Registration"
            )

    try:
        new = Registration()
        new.registration_number = last_registration_number.registration_number + 1 if last_registration_number is not None else 1
        new.full_registration_number = registration_generated_number
        new.schedule = form.schedule.data
        new.branch = form.branch.data
        new.batch_number = Batch.objects.get(id=form.batch_number.data)
        new.contact_person = form.contact_person.data
        new.fname = form.fname.data
        new.mname = form.mname.data
        new.lname = form.lname.data
        new.suffix = form.suffix.data
        new.address = form.address.data
        new.passport = form.passport.data
        new.contact_number = form.contact_number.data
        new.email = form.email.data
        new.birth_date = form.birth_date.data

        new.amount = form.amount.data
        new.payment_mode = request.form['payment_modes']
        if new.payment_mode == "full_payment":
            new.balance = 7000 - new.amount
        else:
            new.balance = 7800 - new.amount

        new.book = request.form['books']
        new.created_by = "{} {}".format(current_user.fname,current_user.lname)

        new.save()

        contact_person = ContactPerson.objects.get(id=new.contact_person)

        earnings = 0
        savings = 0
        if new.payment_mode == "full_payment":
            earnings = 7000 * decimal.Decimal(0.14286)
        elif new.payment_mode == "installment":
            earnings = new.amount * decimal.Decimal(0.125)
            savings = 25.00

        contact_person.earnings.append(
            {
                'payment_mode': new.payment_mode,
                'savings': Decimal128(str(savings)),
                'earnings': Decimal128(str(earnings)),
                'branch': new.branch
            }
        )
        
        contact_person.save()

        flash("Registered added successfully!", 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('lms.members'))