from flask import redirect, url_for, request, flash
from prime_admin.forms import InventoryForm
from flask_login import login_required
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import StudentSupply
import decimal
from app.auth.models import User
from prime_admin.forms import InventoryForm
from flask_login import login_required, current_user
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import InboundOutbound, Branch, Batch



@bp_lms.route('/student-supplies')
@login_required
def student_supplies():
    form = InventoryForm()
    form.__heading__ = "Student Supplies"

    _table_data = []

    if current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
        batch_numbers = Batch.objects(branch=current_user.branch.id)
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    else:
        branches = Branch.objects()

    return admin_table(
        StudentSupply,
        fields=[],
        form=form,
        table_template="lms/student_supplies_page.html",
        table_data=_table_data,
        create_url='lms.create_student_supply',
        edit_url=False,
        modals=['lms/inbound_modal.html', 'lms/outbound_modal.html'],  
        scripts=[],
        view_modal=False,
        inbound_url='lms.inbound_student_supply',
        outbound_url='lms.outbound_student_supply',
        branches=branches,
    )


@bp_lms.route('/student-supplies/inbound', methods=["POST"])
@login_required
def inbound_student_supply():
    supply_id = request.form['supply_id']
    brand = request.form['brand']
    price = decimal.Decimal(request.form['price'])
    quantity = int(request.form['quantity'])

    supply : StudentSupply = StudentSupply.objects.get(id=supply_id)

    if supply is None:
        raise Exception("Product cannot be found")

    supply.remaining = supply.remaining + quantity

    supply.transactions.append(
        InboundOutbound(
            brand=brand,
            price=price,
            quantity=quantity,
            total_amount=price * quantity,
            confirm_by=User.objects.get(id=current_user.id)
        )
    )
    supply.save()
    flash('Process Successfully!','success')
    return redirect(url_for('lms.student_supplies'))


@bp_lms.route('/student-supplies/outbound', methods=["POST"])
@login_required
def outbound_student_supply():
    # try:
    supply_id = request.form['outbound_supply_id']
    withdraw_by = request.form['withdraw_by']
    date = request.form['date']
    quantity = int(request.form['quantity'])
    remarks = request.form['remarks']
    
    supply : StudentSupply = StudentSupply.objects.get(id=supply_id)

    if supply is None:
        raise Exception("Product cannot be found")
    
    supply.remaining = supply.remaining - quantity 
    supply.released = supply.released + quantity if supply.released is not None else quantity

    supply.transactions.append(
        InboundOutbound(
            quantity=quantity,
            date=date,
            remarks=remarks,
            withdraw_by=withdraw_by,
            confirm_by=User.objects.get(id=current_user.id)
        )
    )

    supply.save()

    flash('Process Successfully!','success')
    # except Exception as e:
    #     flash(str(e),'error')
    
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