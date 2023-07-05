from datetime import datetime
import decimal
from flask import redirect, url_for, request, flash, render_template
from bson import ObjectId, Decimal128
from prime_admin.forms import InventoryForm
from flask_login import login_required
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import OfficeSupply
from app.auth.models import User
from prime_admin.forms import InventoryForm
from flask_login import login_required, current_user
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import InboundOutbound, Branch
from flask_weasyprint import HTML, render_pdf
from app import mongo
from prime_admin.globals import convert_to_utc, D128_CTX
from prime_admin.services.inventory import InventoryService
from prime_admin.errors import NotEnoughStocksError



@bp_lms.route('/office-supplies')
@login_required
def office_supplies():
    form = InventoryForm()
    form.__heading__ = "Office Supplies"

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
        OfficeSupply,
        fields=[],
        form=form,
        table_template="lms/office_supplies/office_supplies_page.html",
        table_data=[],
        create_url='lms.create_office_supply',
        edit_url=False,
        modals=['lms/outbound_modal.html', 'lms/office_supplies/modals/supply_transactions_modal.html'],
        scripts=[],
        view_modal=False,
        outbound_url='lms.outbound_office_supply',
        branches=branches,
    )


@bp_lms.route('/office-supplies/outbound', methods=["POST"])
@login_required
def outbound_office_supply():
    supply_id = request.form['outbound_supply_id']
    quantity = int(request.form['quantity'])

    try:
        InventoryService.outbound_office_supply(supply_id, quantity)
        flash('Processed successfully!','success')
        return redirect(url_for('lms.office_supplies'))
    except NotEnoughStocksError as err:
        flash(str(err),'error')
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
    equipment.branch = ObjectId(form.branch.data)
    equipment.created_by = "{} {}".format(current_user.fname,current_user.lname)
    equipment.save()
    flash('New Supplies Added Successfully!','success')
    return redirect(url_for('lms.office_supplies'))


@bp_lms.route('/office_supplies_summary.pdf')
def print_office_supplies_summary():
    branch_id = request.args.get('branch', '')
    branch = Branch.objects.get_or_404(id=branch_id)
    filter_year = request.args.get('year', 'all')
    filter_month = request.args.get('month', 'all')
    _filter = {'branch': ObjectId(branch_id)}
    query = mongo.db.lms_office_supplies.find(_filter)
    table_data = []

    with decimal.localcontext(D128_CTX):
        for supply in query:
            total_used = 0
            
            transactions = InventoryService.find_supply_transactions(supply['_id'], 'outbound', 'office_supplies')
            for trans in transactions:
                quantity = trans.get('quantity', 0)
                date = trans.get('date', None)
                
                if date is None:
                    continue
                
                year = date.year
                month = date.month

                if filter_year != "all":
                    if year != int(filter_year):
                        continue
                    
                if filter_month != "all":
                    if month != int(filter_month):
                        continue
                total_used += quantity
                        
            unit_price = Decimal128(str(supply.get('price', 0)))
            total_price = Decimal128(str(total_used)).to_decimal() * unit_price.to_decimal()
            replacement = InventoryService.supply_total_used(
                supply_id=supply['_id'],
                from_what='office_supplies',
                year=filter_year,
                month=filter_month
            )
            row = [
                str(supply['_id']),
                supply['description'],
                supply.get('remaining', ''),
                supply.get('replacement', ''),
                str(unit_price),
                str(total_price)
            ]
   
            table_data.append(row)
    
    if filter_month != "all":
        month = datetime(1998, month=int(filter_month), day=1).strftime("%B")
    else:
        month = 'all'
    
    html = render_template(
            "lms/pdfs/office_supplies_pdf.html",
            supplies=table_data,
            branch=branch.name.upper(),
            year=filter_year,
            month=month
        )
    return render_pdf(HTML(string=html))