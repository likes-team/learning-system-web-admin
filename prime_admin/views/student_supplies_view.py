import decimal
from flask import redirect, url_for, request, flash, jsonify
from prime_admin.forms import InventoryForm
from flask_login import login_required
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import StudentSupply
from app.auth.models import User
from prime_admin.forms import InventoryForm
from flask_login import login_required, current_user
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import InboundOutbound, Branch
from prime_admin.services.inventory import InventoryService



@bp_lms.route('/student-supplies')
@login_required
def student_supplies():
    form = InventoryForm()
    form.__heading__ = "Student Supplies"

    _table_data = []

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Manager":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Admin":
        branches = Branch.objects()

    return admin_table(
        StudentSupply,
        fields=[],
        form=form,
        table_template="lms/student_supplies/student_supplies_page.html",
        table_data=_table_data,
        create_url='lms.create_student_supply',
        edit_url=False,
        modals=['lms/inbound_modal.html', 'lms/student_supplies/modals/supply_transactions_modal.html'],
        scripts=[],
        view_modal=False,
        inbound_url='lms.inbound_student_supply',
        branches=branches,
    )


@bp_lms.route('/student-supplies/inbound', methods=["POST"])
@login_required
def inbound_student_supply():
    supply_id = request.form['supply_id']
    brand = request.form['brand']
    price = request.form['price']
    quantity = int(request.form['quantity'])

    InventoryService.inbound_student_supply(supply_id, quantity, brand, price)
    flash('Processed successfully!','success')
    return redirect(url_for('lms.student_supplies'))


@bp_lms.route('/student-supplies/create',methods=['GET','POST'])
@login_required
def create_student_supply():
    form = InventoryForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.student_supplies'))

    equipment = StudentSupply()
    equipment.description = form.description.data
    equipment.maintaining = form.maintaining.data
    equipment.remaining = form.remaining.data
    equipment.type = "supplies"

    equipment.created_by = "{} {}".format(current_user.fname,current_user.lname)

    equipment.save()
    flash('New Supplies Added Successfully!','success')
    return redirect(url_for('lms.student_supplies'))


@bp_lms.route('/deposit-stocks', methods=['POST'])
def deposit_stocks():
    supply_id = request.json['supply_id']
    try:
        InventoryService.deposit_stocks(supply_id)
        return jsonify({"result": "success"}), 200
    except ValueError as err:
        return jsonify({"result": "error", 'message': str(err)}), 400
