import decimal
from bson.objectid import ObjectId
from prime_admin.globals import SECRETARYREFERENCE, convert_to_utc, get_date_now
from prime_admin.functions import generate_number
from prime_admin.forms import RegistrationForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template
from prime_admin import bp_lms
from prime_admin.models import Batch, Branch, Registration
from app.auth.models import User
from flask import redirect, url_for, request, flash, jsonify, abort
from app import mongo
from bson.decimal128 import Decimal128
from mongoengine.queryset.visitor import Q
from prime_admin.helpers import Payment
from prime_admin.services.inventory import InventoryService
from prime_admin.services.registration import RegistrationService



@bp_lms.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    registration_generated_number = ""
    
    last_registration_number = Registration.objects(status="registered").order_by('-registration_number').first()

    date_now = get_date_now()

    if last_registration_number:
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

        _modals = [
            'lms/search_client_last_name_modal.html',
        ]

        return admin_render_template(
            Registration,
            'lms/registration.html',
            'learning_management',
            form=form,
            data=data,
            modals=_modals,
            title="Registration"
            )
    elif request.method == "POST":
        # SAVE STUDENT DATA
        client_id = request.form['client_id']
        registration = RegistrationService.fill_up_form(
            client_id,
            form,
            last_registration_number=last_registration_number,
            registration_generated_number=registration_generated_number,
            payment_mode=request.form['payment_modes']
        )
        client = registration.get_student()
        if client.status == "registered":
            return redirect(url_for('lms.members'))

        client.update_books_from_form(request.form.getlist('books'))
        client.update_uniform_from_form(request.form.getlist('uniforms'))
        client.update_id_materials(request.form.getlist('id_materials'))
        client.update_reviewers(request.form.getlist('reviewers'))
        
        if client.books['volume1']:
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='volume1', value=1):
                flash("Not enough BOOK 1 stocks!", 'error')
                return redirect(url_for('lms.register'))

        if client.books['volume2']:
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='volume2', value=1):
                flash("Not enough BOOK 2 stocks!", 'error')
                return redirect(url_for('lms.register'))

        if not client.uniforms['uniform_none']:
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='uniform', value=1):
                flash("Not enough UNIFORM stocks!", 'error')
                return redirect(url_for('lms.register'))

        if client.id_materials['id_card']:
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='id_card', value=1):
                flash("Not enough ID CARD stocks!", 'error')
                return redirect(url_for('lms.register'))

        if client.id_materials['id_lace']:
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='id_lace', value=1):
                flash("Not enough ID LACE stocks!", 'error')
                return redirect(url_for('lms.register'))
        
        if client.reviewers['reading']:
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='reading', value=1):
                flash("Not enough REVIEWER READING stocks!", 'error')
                return redirect(url_for('lms.register'))

        if client.reviewers['listening']:
            if not InventoryService.is_student_supply_available(branch=client.branch.id, description='listening', value=1):
                flash("Not enough REVIEWER LISTENING stocks!", 'error')
                return redirect(url_for('lms.register'))

        thru = form.thru.data
        reference_no = form.reference_no.data

        registration.compute_marketer_earnings()
        registration.set_payment(thru, reference_no)
        registration.set_marketer_earning()
        
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.lms_registrations.update_one({
                    '_id': ObjectId(client_id),
                },
                {"$set": {
                    "mname": client.mname,
                    "suffix": client.suffix,
                    "address": client.address,
                    "contact_number": client.contact_number,
                    "email": client.email,
                    "birth_date": convert_to_utc(str(client.birth_date), "date_from") if client.birth_date is not None else None,
                    "e_registration": client.e_registration,
                    "registration_number": client.registration_number,
                    "full_registration_number": client.full_registration_number,
                    "schedule": client.schedule,
                    "batch_number": client.batch_number.id,
                    "passport": client.passport,
                    "status": 'registered',
                    "amount": Decimal128(str(client.amount)),
                    "payment_mode": client.payment_mode,
                    "created_by": client.created_by,
                    "registration_date": client.registration_date,
                    "books": client.books,
                    "uniforms": client.uniforms,
                    "id_materials": client.id_materials,
                    "level": client.level,
                    "balance": Decimal128(str(client.balance)),
                    "fle": Decimal128(str(client.fle)),
                    "sle": Decimal128(str(client.sle)),
                    "civil_status": client.civil_status,
                    "gender": client.gender,
                    "session": client.session,
                    'reviewers': client.reviewers
                    }}, session=session)
                
                Payment.pay_registration(registration.get_payment_dict(), session=session)
                
                InventoryService.buy_items(
                    student=client,
                    session=session
                )

                register_description = "New student - {id} {lname} {fname} {batch} {branch} {contact_person} {mode_of_payment}".format(id=client.full_registration_number,
                    lname=client.lname,
                    fname=client.fname,
                    batch=client.batch_number.number,
                    branch=client.branch.name,
                    contact_person=client.contact_person.fname,
                    mode_of_payment=client.payment_mode
                    )

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": register_description,
                    "from_module": "Registration",
                    "branch": ObjectId(client.branch.id)
                }, session=session)

                payment_description = "New payment - {id} {lname} {fname}  {branch} {batch} w/ amount of Php. {amount}".format(
                    id=client.full_registration_number,
                    lname=client.lname,
                    fname=client.fname,
                    branch=client.branch.name,
                    batch=client.batch_number.number,
                    amount=str(client.amount)
                )

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": payment_description,
                    "from_module": "Registration",
                    "branch": ObjectId(client.branch.id)
                }, session=session)

                earning_description = "Earnings/Savings - Php. {earnings} / {savings} of {contact_person} from {student} 's {payment_mode} w/ amount of Php. {amount}".format(
                    earnings="{:.2f}".format(registration.get_earnings()),
                    savings="{:.2f}".format(registration.get_savings()),
                    contact_person=client.contact_person.fname + " " + client.contact_person.lname,
                    student=client.lname + " " + client.fname,
                    payment_mode=client.payment_mode,
                    amount=str(client.amount)
                )
                
                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": earning_description,
                    "from_module": "Registration",
                    "branch": ObjectId(client.branch.id)
                }, session=session)
        flash("Registered added successfully!", 'success')
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


@bp_lms.route('/api/dtbl/registered-students', methods=['GET'])
def get_pre_registered_students():
    if current_user.role.name == "Admin":
        clients = Registration.objects(status="registered")
    elif current_user.role.name == "Manager":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
    elif current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)

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
    is_check_existing_client = request.args.get('check_existing_client', False)
    client = Registration.objects.get(id=client_id)

    payment_status = "PAID"
    if client.balance is not None:
        if client.balance > 0:
            payment_status = "NOT PAID"

    if is_check_existing_client:
        check_existing_client = list(mongo.db.lms_registrations.find({
            '_id': {"$ne": ObjectId(client.id)},
            'fname': {'$regex': client.fname, '$options' : 'i'},
            'lname': {'$regex': client.lname, '$options' : 'i'},
            'status': 'registered'
        }))
        
        if len(check_existing_client) > 0:
            return jsonify({
                'status': 'error',
                'message': "Student is already registered"
            })

    _data = {
        'id': str(client.id),
        'fname': client.fname,
        'lname': client.lname,
        'mname': client.mname if client.mname is not None else '',
        'contact_number': client.contact_number,
        'status': client.status,
        'contact_person': str(client.contact_person.id),
        'is_oriented': client.is_oriented,
        'branch': str(client.branch.id) if client.branch is not None else '',
        'branch_name': str(client.branch.name) if client.branch is not None else '',
        'registration_no': client.full_registration_number,
        'batch_number': client.batch_number.number if client.batch_number is not None else '',
        'schedule': client.schedule,
        'payment_status': payment_status
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
