from prime_admin.forms import InventoryForm
from flask_login import login_required
from app.admin.templating import admin_table
from prime_admin import bp_lms
from prime_admin.models import StudentSupply



@bp_lms.route('/student-supplies')
@login_required
def student_supplies():
    form = InventoryForm()
    form.__heading__ = "Student Supplies"

    _table_data = []

    return admin_table(
        StudentSupply,
        fields=[],
        form=form,
        table_template="lms/student_supplies_page.html",
        table_data=_table_data,
        create_url='lms.create_supplies',
        edit_url=False,
        modals=['lms/inbound_modal.html', 'lms/outbound_modal.html'],  
        scripts=[],
        view_modal=False,
    )
