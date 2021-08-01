import decimal
from prime_admin.globals import SECRETARYREFERENCE, get_date_now
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm, StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, Registration
from app.auth.models import Earning, Role, User
from flask import redirect, url_for, request, current_app, flash, jsonify, abort
from app import db, mongo
from datetime import datetime
from bson.decimal128 import Decimal128
from mongoengine.queryset.visitor import Q
from config import TIMEZONE



@bp_lms.route('/register', methods=['GET', 'POST'])
@login_required
def register():

    registration_generated_number = ""
    
    last_registration_number = Registration.objects(status="registered").order_by('-registration_number').first()

    date_now = get_date_now()

    if last_registration_number:
        print(last_registration_number)
        registration_generated_number = generate_number(date_now, last_registration_number.registration_number)
    else:
        registration_generated_number = str(date_now.year) + '%02d' % date_now.month + "0001"

    form = RegistrationForm()

    if request.method == "GET":
        if current_user.role.name == "Secretary":
            branches = Branch.objects(id=current_user.branch.id)
            contact_persons = User.objects(Q(branches__in=[str(current_user.branch.id)]) | Q(role__ne=SECRETARYREFERENCE))
            form.batch_number.data = Batch.objects(active=True).filter(branch=current_user.branch).all()
        if current_user.role.name == "Partner":
            branches = Branch.objects(id__in=current_user.branches)
            contact_persons = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(id__ne=current_user.id) & Q(is_superuser=False))
            form.batch_number.data = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
        else:
            branches = Branch.objects
            contact_persons = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))
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
            'lms/search_client_last_name_modal.html',
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

    # SAVE STUDENT DATA
    try:
        client_id = request.form['client_id']
        earnings = 0
        savings = 0

        if client_id == '': # NO SELECTED CLIENT
            client = Registration()
            client.contact_person = User.objects.get(id=form.contact_person.data)
            client.fname = form.fname.data
            client.mname = form.mname.data
            client.lname = form.lname.data
            client.suffix = form.suffix.data
            client.address = form.address.data
            client.contact_number = form.contact_number.data
            client.email = form.email.data
            client.birth_date = form.birth_date.data
        else: # HAS SELECTED CLIENT
            client = Registration.objects.get(id=client_id)

            if client.status == "pre_registered" and client.is_oriented is False :
                client.contact_person = User.objects.get(id=form.contact_person.data)

            elif client.status == "oriented":
                client.mname = form.mname.data
                client.suffix = form.suffix.data
                client.address = form.address.data
                client.contact_number = form.contact_number.data
                client.email = form.email.data
                client.birth_date = form.birth_date.data

        client.e_registration = form.e_registration.data
        client.registration_number = last_registration_number.registration_number + 1 if last_registration_number is not None else 1
        client.full_registration_number = registration_generated_number
        client.schedule = form.schedule.data
        client.branch = Branch.objects.get(id=form.branch.data)
        client.batch_number = Batch.objects.get(id=form.batch_number.data) 
        client.passport = form.passport.data
        client.status = "registered"
        client.amount = form.amount.data
        client.payment_mode = request.form['payment_modes']
        client.created_by = "{} {}".format(current_user.fname,current_user.lname)
        client.set_registration_date()

        books = request.form.getlist('books')
        
        client.books = {
            'book_none': True if 'book_none' in books else False,
            'volume1': True if 'volume1' in books else False,
            'volume2': True if 'volume2' in books else False,
        }

        uniforms = request.form.getlist('uniforms')

        client.uniforms = {
            'uniform_none': True if 'uniform_none' in uniforms else False,
            'uniform_xs': True if 'uniform_xs' in uniforms else False,
            'uniform_s': True if 'uniform_s' in uniforms else False,
            'uniform_m': True if 'uniform_m' in uniforms else False,
            'uniform_l': True if 'uniform_l' in uniforms else False,
            'uniform_xl': True if 'uniform_xl' in uniforms else False,
            'uniform_xxl': True if 'uniform_xxl' in uniforms else False,
        }

        id_materials = request.form.getlist('id_materials')

        client.id_materials = {
            'id_card': True if 'id_card' in id_materials else False,
            'id_lace': True if 'id_lace' in id_materials else False,
        }

        if client.level == "first":
            earnings_percent = decimal.Decimal(0.14)
            savings_percent = decimal.Decimal(0.00286)
        elif client.level == "second":
            earnings_percent = decimal.Decimal(0.0286)
            savings_percent = decimal.Decimal(0.00)
        else:
            earnings_percent = decimal.Decimal(0.00)
            savings_percent = decimal.Decimal(0.00)

        if client.payment_mode == "full_payment":
            client.balance = 7000 - client.amount
            earnings = 7000 * earnings_percent
            savings = 7000 * savings_percent
        elif client.payment_mode == "installment":
            client.balance = 7800 - client.amount
            earnings = client.amount * earnings_percent
            savings = client.amount * savings_percent
        elif client.payment_mode == 'premium':
            client.balance = 8500 - client.amount
            earnings = 8500 * earnings_percent
            savings = 8500 * savings_percent
        elif client.payment_mode == "full_payment_promo":
            client.balance = 5500 - client.amount
            earnings = 5500 * earnings_percent
            savings = 5500 * savings_percent
        elif client.payment_mode == "installment_promo":
            client.balance = 6300 - client.amount
            earnings = client.amount * earnings_percent
            savings = client.amount * savings_percent
        elif client.payment_mode == 'premium_promo':
            client.balance = 7000 - client.amount
            earnings = 7000 * earnings_percent
            savings = 7000 * savings_percent

        if client.level == "first":
            client.fle = earnings
            client.sle = decimal.Decimal(0.00)
        elif client.level == "second":
            client.sle = earnings
            client.fle = decimal.Decimal(0.00)
        else:
            client.fle = decimal.Decimal(0.00)
            client.sle = decimal.Decimal(0.00)

        client.payments.append(
            {
                'payment_mode': client.payment_mode,
                'amount': Decimal128(str(client.amount)),
                'current_balance': Decimal128(str(client.balance)),
                'confirm_by': User.objects.get(id=str(current_user.id)),
                'date': get_date_now()
            }
        )

        if client_id == '': # NO SELECTED CLIENT
            client.contact_person.earnings.append(
                Earning(
                    custom_id=client.full_registration_number,
                    payment_mode=client.payment_mode,
                    savings=Decimal128(str(savings)),
                    earnings=Decimal128(str(earnings)),
                    branch=client.branch,
                    client=client,
                    date=get_date_now(),
                    registered_by=User.objects.get(id=str(current_user.id))
                )
            )

            client.save()
            client.contact_person.save()
        else:
            contact_person = User.objects.get(id=str(client.contact_person.id))
            contact_person.earnings.append(
                Earning(
                    custom_id=client.full_registration_number,
                    payment_mode=client.payment_mode,
                    savings=Decimal128(str(savings)),
                    earnings=Decimal128(str(earnings)),
                    branch=client.branch,
                    client=client,
                    date=get_date_now(),
                    registered_by=User.objects.get(id=str(current_user.id))
                )
            )

            client.save()
            contact_person.save()

        flash("Registered added successfully!", 'success')

    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('lms.members'))


@bp_lms.route('/api/dtbl/mdl-pre-registered-clients-registration', methods=['GET'])
def get_pre_registered_clients_registration():

    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="oriented").filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(status="oriented")
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="oriented").filter(branch__in=current_user.branches)
    else:
        return abort(404)

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
            'is_oriented': client.is_oriented,
            'branch': str(client.branch.id) if client.branch is not None else ''
        }

    batch_numbers = Batch.objects(branch=client.branch.id).filter(active=True)

    batch_no_data = []

    for batch_number in batch_numbers:
        batch_no_data.append({
            'id': str(batch_number.id),
            'number': batch_number.number
        })

    _data['batch_numbers'] = batch_no_data

    response = {
        'data': _data
        }

    return jsonify(response)


@bp_lms.route('/api/get-batch-numbers/<string:branch_id>', methods=['GET'])
def get_batch_numbers(branch_id):
    batch_numbers = Batch.objects(branch=branch_id).filter(active=True)

    if batch_numbers is None:
        response = {
            'data': []
        }

        return jsonify(response)

    data = []

    for batch_number in batch_numbers:
        data.append({
            'id': str(batch_number.id),
            'number': batch_number.number
        })

    response = {
        'data': data
        }

    return jsonify(response)
