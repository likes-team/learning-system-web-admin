import pymongo
from bson.objectid import ObjectId
from prime_admin.globals import PARTNERREFERENCE, SECRETARYREFERENCE, get_date_now
from app.auth.models import User
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template
from prime_admin import bp_lms
from prime_admin.models import Branch, OrientationAttendance, Registration, Orientator
from flask import jsonify, request
from mongoengine.queryset.visitor import Q
from app import mongo



@bp_lms.route('/orientation-attendance')
@login_required
def orientation_attendance():
    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        contact_persons = User.objects(Q(branches__in=[str(current_user.branch.id)]) & Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        contact_persons = User.objects(id=current_user.id)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
        contact_persons = User.objects(Q(branches__in=current_user.branches) & Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))
    else:
        branches = Branch.objects
        contact_persons = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False))

    orientators = Orientator.objects()

    return admin_render_template(
        OrientationAttendance,
        "lms/orientation_attendance.html",
        'learning_management',
        title="Orientation attendance",
        contact_persons=contact_persons,
        branches=branches,
        orientators=orientators,
    )


@bp_lms.route('/orientation-attendance/orient', methods=['POST'])
@login_required
def orient():
    form = request.form

    fname = form.get('fname', '')
    lname = form.get('lname', '')
    contact_no = form.get('contact_no', '')
    branch_id = form.get('branch', None)
    contact_person_id = form.get('contact_person', None)
    orientator = form.get('orientator', None)
    client_id = form.get('client_id', None)
    referred_by = form.get('referred_by', None)
    
    try:
        if client_id != '':
            client = Registration.objects.get(id=client_id)

            client.is_oriented = True
            client.date_oriented = get_date_now()
            client.contact_person = User.objects.get(id=contact_person_id)
            client.orientator = Orientator.objects.get(id=orientator)
            client.save()
        else:
            new_client = Registration()
            new_client.fname = fname
            new_client.lname = lname
            new_client.contact_number = contact_no
            new_client.contact_person = User.objects.get(id=contact_person_id)
            new_client.branch = Branch.objects.get(id=branch_id)
            new_client.date_oriented = get_date_now()
            new_client.orientator = Orientator.objects.get(id=orientator)
            new_client.is_oriented = True
            new_client.status = "oriented"
            new_client.set_created_at()

            if referred_by == '':
                new_client.level = "first"
            else:
                referred_student = Registration.objects.get(id=referred_by)

                if referred_student.level == "first":
                    new_client.level = "second"
                elif referred_student.level == "second":
                    new_client.level = "third"
                elif referred_student.level == "third":
                    new_client.level = str(4)
                else:
                    print(referred_student.level)
                    new_client.level = str(int(referred_student.level) + 1)

            new_client.save()

        with mongo.cx.start_session() as session:
            with session.start_transaction():
                orient_description = "New oriented - {lname} {fname} {branch} {contact_person}".format(
                    lname=new_client.lname,
                    fname=new_client.fname,
                    branch=new_client.branch.name,
                    contact_person=new_client.contact_person.fname,
                    )

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": orient_description,
                    "from_module": "Orientation Attendance"
                }, session=session)

        response = {
            'status': 'success',
            'message': "Oriented successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_lms.route('/orientation-attendance/students/dt')
def fetch_orientation_attendance_students_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    branch_id = request.args.get('branch')
    contact_person_id = request.args.get('contact_person')

    total_records: int
    filtered_records: int
    filter: dict

    if branch_id == 'all':
        if current_user.role.name == "Admin":
            registrations = Registration.objects(status='oriented').order_by("-date_oriented").skip(start).limit(length)
            filter = {'status': 'oriented'}
        elif current_user.role.name == "Partner":
            registrations = Registration.objects(status='oriented').filter(branch__in=current_user.branches).order_by("-date_oriented").skip(start).limit(length)
            filter = {'status': 'oriented', 'branch': {'$in': current_user.branches}}
        elif current_user.role.name == "Secretary":
            registrations = Registration.objects(status='oriented').filter(branch=current_user.branch.id).order_by("-date_oriented").skip(start).limit(length)
            filter = {'status': 'oriented', 'branch': ObjectId(current_user.branch.id)}
        elif current_user.role.name == "Marketer":
            registrations = Registration.objects(status='oriented').filter(branch__in=current_user.branches).order_by("-date_oriented").skip(start).limit(length)
            filter = {'status': 'oriented', 'branch': {'$in': current_user.branches}}
    else:
        registrations = Registration.objects(branch=branch_id).filter(status='oriented').order_by("-date_oriented").skip(start).limit(length)
        filter = {'status': 'oriented', 'branch': ObjectId(branch_id)}

    if search_value != "":
        registrations = registrations.filter(lname__icontains=search_value)
        filter['lname'] = {"$regex": search_value}
        
    if contact_person_id != 'all':
        registrations = registrations.filter(contact_person=contact_person_id)
        filter['contact_person'] = ObjectId(contact_person_id)

    query = mongo.db.lms_registrations.find(filter).sort('date_oriented', pymongo.DESCENDING).skip(start).limit(length)
    total_records = mongo.db.lms_registrations.find(filter).count()
    filtered_records = query.count()

    table_data = []

    for registration in registrations:
        actions = """<button style="margin-bottom: 8px;" type="button" data-toggle="modal" data-target="#viewModal" class="mr-2 btn-icon btn-icon-only btn btn-outline-info btn-view"><i class="pe-7s-look btn-icon-wrapper"> </i></button>"""

        table_data.append([
            str(registration.id),
            registration.branch.name if registration.branch is not None else "",
            registration.full_name,
            registration.contact_number,
            registration.contact_person.name if registration.contact_person is not None else '',
            registration.orientator.fname if registration.orientator is not None else '',
            registration.oriented_date_local,
            actions
        ])

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }

    return jsonify(response)


@bp_lms.route('/api/dtbl/mdl-pre-registered-clients', methods=['GET'])
def get_pre_registered_clients():

    clients = Registration.objects(Q(is_oriented=False) | Q(is_oriented__exists=False) & Q(status="pre_registered"))

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


@bp_lms.route('/api/dtbl/mdl-referrals', methods=['GET'])
def get_referrals():
    if current_user.role.name == "Secretary":
        clients = Registration.objects(status="registered").filter(branch=current_user.branch)
    elif current_user.role.name == "Admin":
        clients = Registration.objects(status="registered")
    elif current_user.role.name == "Partner":
        clients = Registration.objects(status="registered").filter(branch__in=current_user.branches)
    else:
        return jsonify({'data': []})

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


@bp_lms.route('/api/get-branch-contact-persons/<string:branch_id>', methods=['GET'])
def get_branch_contact_persons(branch_id):
    print(branch_id)
    if branch_id == "all":
        contact_persons = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False) & Q(id__ne=current_user.id) | Q(role=PARTNERREFERENCE))
    else:
        contact_persons = User.objects(Q(branches__in=[branch_id]) & Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False) & Q(id__ne=current_user.id) | Q(role=PARTNERREFERENCE))

    if contact_persons is None:
        response = {
            'data': []
        }

        return jsonify(response)

    data = []

    print(contact_persons)

    for contact_person in contact_persons:
        data.append({
            'id': str(contact_person.id),
            'fname': contact_person.fname
        })

    response = {
        'data': data
        }

    return jsonify(response)
