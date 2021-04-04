from prime_admin.forms import StudentForm, TeacherForm, TrainingCenterEditForm, TrainingCenterForm
from flask_login import login_required, current_user
from app.admin.templating import admin_render_template, admin_table, admin_edit
from prime_admin import bp_lms
from prime_admin.models import TrainingCenter, Teacher, Student
from flask import redirect, url_for, request, current_app, flash
from app import db
from datetime import datetime



@bp_lms.route('/')
@bp_lms.route('/training-centers')
@login_required
def training_centers():
    _fields = [TrainingCenter.id,TrainingCenter.name, TrainingCenter.created_by, TrainingCenter.created_at, TrainingCenter.updated_by, TrainingCenter.updated_at]
    form = TrainingCenterForm()

    _training_centers = TrainingCenter.objects

    _table_data = []

    for training_center in _training_centers:
        _table_data.append((
            training_center.id,
            training_center.name,
            training_center.created_by,
            training_center.created_at,
            training_center.updated_by,
            training_center.updated_at
        ))

    return admin_table(TrainingCenter, fields=_fields, form=form, create_url='lms.create_training_center',\
        edit_url='lms.edit_training_center', table_data=_table_data)


@bp_lms.route('/training-centers/create', methods=['POST'])
@login_required
def create_training_center():
    form = TrainingCenterForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.training_centers'))

    try:
        new = TrainingCenter()
        new.name = form.name.data
        new.created_by = "{} {}".format(current_user.fname,current_user.lname)
        new.save()

        flash("Created successfully!", 'success')
    except Exception as exc:
        flash(str(exc), 'error')
    
    return redirect(url_for('lms.training_centers'))


@bp_lms.route('/training-centers/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_training_center(oid):
    ins = TrainingCenter.objects.get_or_404(id=oid)
    form = TrainingCenterEditForm(obj=ins)

    if request.method == 'GET':
        return admin_edit(TrainingCenter, form, 'lms.edit_training_center', oid, 'lms.training_centers')

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.training_centers'))

    try:
        ins.name = form.name.data
        ins.updated_at = datetime.now()
        ins.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        ins.save()

        flash('Updated Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.training_centers'))


@bp_lms.route('/teachers')
@login_required
def teachers():
    _fields = [Teacher.id, Teacher.fname, Teacher.mname, Teacher.lname, Teacher.created_by, Teacher.created_at, Teacher.updated_by, Teacher.updated_at]
    
    _teachers = Teacher.objects

    _table_data = []

    for teacher in _teachers:
        _table_data.append((
            teacher.id,
            teacher.fname,
            teacher.mname,
            teacher.lname,
            teacher.created_by,
            teacher.created_at,
            teacher.updated_by,
            teacher.updated_at
        ))

    return admin_table(Teacher, fields=_fields, form=TeacherForm(), create_url='lms.create_teacher',\
        edit_url='lms.edit_teacher', table_data=_table_data)


@bp_lms.route('/teachers/create', methods=['POST'])
@login_required
def create_teacher():
    form = TeacherForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.teachers'))

    try:
        new = Teacher()
        new.fname = form.fname.data
        new.mname = form.mname.data
        new.lname = form.lname.data
        
        db.session.add(new)
        db.session.commit()
        flash("Created successfully!", 'success')
    except Exception as exc:
        flash(str(exc), 'error')
    
    return redirect(url_for('lms.teachers'))


@bp_lms.route('/teachers/<int:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_teacher(oid):
    ins = Teacher.query.get_or_404(oid)
    form = TeacherForm(obj=ins)

    if request.method == 'GET':
        return admin_edit(Teacher, form, 'lms.edit_teacher', oid, 'lms.teachers')

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.teachers'))

    try:
        ins.fname = form.fname.data
        ins.mname = form.mname.data
        ins.lname = form.lname.data
        ins.updated_at = datetime.now()
        ins.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        db.session.commit()

        flash('Updated Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.teachers'))


@bp_lms.route('/students')
@login_required
def students():
    _fields = [Student.id, Student.fname, Student.mname, Student.lname, Student.created_by, Student.created_at, Student.updated_by, Student.updated_at]
    
    _students = Student.objects

    _table_data = []

    for student in _students:
        _table_data.append((
            student.id,
            student.fname,
            student.mname,
            student.lname,
            student.created_by,
            student.created_at,
            student.updated_by,
            student.updated_at,
        ))

    return admin_table(Student, fields=_fields, form=StudentForm(), create_url='lms.create_student',\
        edit_url='lms.edit_student', table_data=_table_data)


@bp_lms.route('/students/create', methods=['POST'])
@login_required
def create_student():
    form = StudentForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.students'))

    try:
        new = Student()
        new.fname = form.fname.data
        new.mname = form.mname.data
        new.lname = form.lname.data
        
        new.save()

        flash("Created successfully!", 'success')
    except Exception as exc:
        flash(str(exc), 'error')
    
    return redirect(url_for('lms.students'))


@bp_lms.route('/students/<int:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(oid):
    ins = Student.objects.get(id=oid)
    form = StudentForm(obj=ins)

    if request.method == 'GET':
        return admin_edit(Teacher, form, 'lms.edit_student', oid, 'lms.students')

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.students'))

    try:
        ins.fname = form.fname.data
        ins.mname = form.mname.data
        ins.lname = form.lname.data
        ins.updated_at = datetime.now()
        ins.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        db.session.commit()

        flash('Updated Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('lms.students'))