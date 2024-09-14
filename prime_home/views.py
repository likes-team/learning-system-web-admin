from flask.helpers import url_for
from flask.templating import render_template
from flask_login import current_user
from werkzeug.utils import redirect
from prime_home import bp_prime_home
from prime_admin.models import Branch, Registration
from flask import request, jsonify
from app import mongo
import pymongo
from prime_admin.models_v2 import StudentV2
from bson import ObjectId
from prime_admin.utils.date import format_utc_to_local


@bp_prime_home.route('/')
def index():
    return render_template('prime_home/index.html')


@bp_prime_home.route('/passers')
def passers():
    return render_template('prime_home/passers_page.html')

@bp_prime_home.route('/latest-passers')
def fetch_latest_passers():
    length = 10
    match = {'is_passer': True}
        
    query = mongo.db.lms_registrations.find(match).sort('added_to_passers_date', pymongo.DESCENDING).limit(length)
    data = []
    
    for doc in query:
        student = StudentV2(doc)
        
        data.append({
            'name' : student.get_full_name(),
            'score' : student.document.get('score', ''),
        })
    return jsonify(data)

@bp_prime_home.route('/datatables/passers')
def fetch_datatables_passers():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    match = {'is_passer': True}
        
    query = mongo.db.lms_registrations.find(match).sort('added_to_passers_date', pymongo.DESCENDING).skip(start).limit(length)
    total_records = mongo.db.lms_registrations.find(match).count()
    filtered_records = query.count()
    table_data = []
    ctr = start
    
    for doc in query:
        student = StudentV2(doc)
        ctr = ctr + 1
        
        table_data.append([
            ctr,
            student.get_full_name(),
            student.document.get('score', ''),
        ])
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }
    return jsonify(response)


@bp_prime_home.route('/branches')
def branches():
    return render_template('prime_home/branches_page.html')


@bp_prime_home.route('/testimonies')
def testimonies():
    return render_template('prime_home/testimonies_page.html')


@bp_prime_home.route('/about')
def about():
    return render_template('prime_home/about_page.html')


@bp_prime_home.route('/contact-us')
def contact_us():
    return render_template('prime_home/contact_us_page.html')


@bp_prime_home.route('/pre-register', methods=["GET", 'POST'])
def pre_register():
    if request.method == "GET":
        
        branches = Branch.objects

        return render_template(
            'prime_home/pre_register.html',
            branches=branches
        )

    new = Registration()
    new.registration_number = None
    new.full_registration_number = None
    new.schedule = None
    new.branch = Branch.objects.get(id=request.form['branch'])
    new.batch_number = None
    new.contact_person = None
    new.fname = request.form['fname']
    new.mname = request.form['mname']
    new.lname = request.form['lname']
    new.gender = request.form['gender']
    new.suffix = request.form['suffix']
    new.address = request.form['address']
    new.contact_number = request.form['contact_number']
    new.email = request.form['email']
    new.birth_date = request.form['birth_date']
    new.status = "pre_registered"
    new.is_oriented = False

    new.save()

    return redirect(url_for('prime_home.successfully_registered'))

@bp_prime_home.route('/successfully-registered')
def successfully_registered():
    return render_template('prime_home/pre_registered_successfully.html')

