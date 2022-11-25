from flask import redirect, url_for, request, flash
from prime_admin.forms import InventoryForm
from flask_login import login_required
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import OfficeSupply
import decimal
from app.auth.models import User
from prime_admin.forms import InventoryForm
from flask_login import login_required, current_user
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import InboundOutbound




@bp_lms.route('/office-supplies')
@login_required
def office_supplies():
    form = InventoryForm()
    form.__heading__ = "Office Supplies"

    _table_data = []

    return admin_table(
        OfficeSupply,
        fields=[],
        form=form,
        table_template="lms/office_supplies_page.html",
        table_data=_table_data,
        create_url='lms.create_office_supply',
        edit_url=False,
        modals=['lms/inbound_modal.html', 'lms/outbound_modal.html'],
        scripts=[],
        view_modal=False,
        inbound_url='lms.inbound_office_supply',
        outbound_url='lms.outbound_office_supply',
    )


@bp_lms.route('/office-supplies/inbound', methods=["POST"])
@login_required
def inbound_office_supply():
    supply_id = request.form['supply_id']
    brand = request.form['brand']
    price = decimal.Decimal(request.form['price'])
    quantity = int(request.form['quantity'])

    supply : OfficeSupply = OfficeSupply.objects.get(id=supply_id)

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
    return redirect(url_for('lms.office_supplies'))


@bp_lms.route('/office-supplies/outbound', methods=["POST"])
@login_required
def outbound_office_supply():
    # try:
    supply_id = request.form['outbound_supply_id']
    withdraw_by = request.form['withdraw_by']
    date = request.form['date']
    quantity = int(request.form['quantity'])
    remarks = request.form['remarks']
    
    supply : OfficeSupply = OfficeSupply.objects.get(id=supply_id)

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
    
    return redirect(url_for('lms.office_supplies'))


@bp_lms.route('/office-supplies/create',methods=['GET','POST'])
@login_required
def create_office_supply():
    form = InventoryForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.office_supplies'))

    equipment = OfficeSupply()
    equipment.description = form.description.data
    equipment.maintaining = form.maintaining.data
    equipment.remaining = form.remaining.data
    equipment.type = "supplies"
    equipment.created_by = "{} {}".format(current_user.fname,current_user.lname)
    equipment.save()
    flash('New Supplies Added Successfully!','success')
    return redirect(url_for('lms.office_supplies'))