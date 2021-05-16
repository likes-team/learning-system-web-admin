import decimal

from flask.json import jsonify
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

    if last_registration_number.registration_number:
        
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
        
        _modals = [
            'lms/search_client_last_name_modal.html'
        ]

        return admin_render_template(
            Registration,
            'lms/registration.html',
            'learning_management',
            form=form,
            data=data,
            scripts=_scripts,
            modals=_modals,
            title="Registration"
            )

    try:
        client_id = request.form['client_id']

        if client_id == '':
            client = Registration()
            client.registration_number = last_registration_number.registration_number + 1 if last_registration_number.registration_number is not None else 1
            client.full_registration_number = registration_generated_number
            client.schedule = form.schedule.data
            client.branch = Branch.objects.get(id=form.branch.data)
            client.batch_number = Batch.objects.get(id=form.batch_number.data)
            client.contact_person = ContactPerson.objects.get(id=form.contact_person.data)
            client.fname = form.fname.data
            client.mname = form.mname.data
            client.lname = form.lname.data
            client.suffix = form.suffix.data
            client.address = form.address.data
            client.passport = form.passport.data
            client.contact_number = form.contact_number.data
            client.email = form.email.data
            client.birth_date = form.birth_date.data
            client.status = "registered"

            client.amount = form.amount.data
            client.payment_mode = request.form['payment_modes']

            if client.payment_mode == "full_payment":
                client.balance = 7000 - client.amount
            else:
                client.balance = 7800 - client.amount

            client.book = request.form['books']
            client.created_by = "{} {}".format(current_user.fname,current_user.lname)

            # contact_person = ContactPerson.objects.get(id=)

            earnings = 0
            savings = 0
            if client.payment_mode == "full_payment":
                earnings = 7000 * decimal.Decimal(0.14286)
            elif client.payment_mode == "installment":
                earnings = client.amount * decimal.Decimal(0.125)
                savings = 25.00

            client.contact_person.earnings.append(
                {
                    'payment_mode': client.payment_mode,
                    'savings': Decimal128(str(savings)),
                    'earnings': Decimal128(str(earnings)),
                    'branch': client.branch
                }
            )

            client.save()
            client.contact_person.save()

            flash("Registered added successfully!", 'success')
            return redirect(url_for('lms.members'))

        client = Registration.objects.get(id=client_id)
        client.registration_number = last_registration_number.registration_number + 1 if last_registration_number.registration_number is not None else 1
        client.full_registration_number = registration_generated_number
        client.schedule = form.schedule.data
        client.branch = Branch.objects.get(id=form.branch.data)
        client.batch_number = Batch.objects.get(id=form.batch_number.data)
        
        if client.status == "pre_registered" and client.is_oriented is False :
            client.contact_person = ContactPerson.objects.get(id=form.contact_person.data)

        elif client.status == "oriented":
            client.mname = form.mname.data
            client.suffix = form.suffix.data
            client.address = form.address.data
            client.contact_number = form.contact_number.data
            client.email = form.email.data
            client.birth_date = form.birth_date.data
        
        client.passport = form.passport.data
        client.status = "registered"

        client.amount = form.amount.data
        client.payment_mode = request.form['payment_modes']

        if client.payment_mode == "full_payment":
            client.balance = 7000 - client.amount
        else:
            client.balance = 7800 - client.amount

        client.book = request.form['books']
        client.created_by = "{} {}".format(current_user.fname,current_user.lname)

        contact_person = ContactPerson.objects.get(id=str(client.contact_person.id))

        earnings = 0
        savings = 0
        if client.payment_mode == "full_payment":
            earnings = 7000 * decimal.Decimal(0.14286)
        elif client.payment_mode == "installment":
            earnings = client.amount * decimal.Decimal(0.125)
            savings = 25.00

        contact_person.earnings.append(
            {
                'payment_mode': client.payment_mode,
                'savings': Decimal128(str(savings)),
                'earnings': Decimal128(str(earnings)),
                'branch': client.branch
            }
        )

        client.save()
        contact_person.save()

        flash("Registered added successfully!", 'success')

    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('lms.members'))


@bp_lms.route('/api/dtbl/mdl-pre-registered-clients-registration', methods=['GET'])
def get_pre_registered_clients_registration():

    clients = Registration.objects(status__ne="registered")

    _data = []

    for client in clients:
        _data.append([
            str(client.id),
            client.lname,
            client.fname,
            client.mname,
            client.suffix,
            client.contact_number,
            client.status
        ])

    response = {
        'data': _data
        }

    return jsonify(response)


@bp_lms.route('/api/clients/<string:client_id>', methods=['GET'])
def get_client(client_id):

    client = Registration.objects.get(id=client_id)

    if client.status == "pre_registered" and client.is_oriented is False:
        _data = {
            'id': str(client.id),
            'fname': client.fname,
            'lname': client.lname,
            'mname': client.mname,
            'suffix': client.suffix,
            'birth_date': client.birth_date,
            'contact_number': client.contact_number,
            'email': client.email,
            'address': client.address,
            'branch': client.branch,
            'status': client.status,
            'is_oriented': client.is_oriented
        }
    elif client.status == "pre_registered" and client.is_oriented is True:
        _data = {
            'id': str(client.id),
            'fname': client.fname,
            'lname': client.lname,
            'mname': client.mname,
            'suffix': client.suffix,
            'birth_date': client.birth_date,
            'contact_number': client.contact_number,
            'email': client.email,
            'address': client.address,
            'branch': client.branch,
            'status': client.status,
            'contact_person': str(client.contact_person.id),
            'is_oriented': client.is_oriented
        }
    else:
        _data = {
            'id': str(client.id),
            'fname': client.fname,
            'lname': client.lname,
            'mname': client.mname if client.mname is not None else '',
            'contact_number': client.contact_number,
            'status': client.status,
            'contact_person': str(client.contact_person.id),
            'is_oriented': client.is_oriented
        }

    response = {
        'data': _data
        }

    return jsonify(response)
