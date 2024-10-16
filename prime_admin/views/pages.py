from prime_admin import bp_lms
from app.admin.templating import admin_render_template
from prime_admin.models import Settings
from prime_admin.models import OurTestimony
from flask_login import login_required
from flask import redirect, url_for, jsonify, request, flash
from prime_admin.forms import OurTestimoniesEditForm
from app.admin.templating import admin_render_template, admin_edit
from prime_admin.utils.upload import allowed_file
from prime_admin.services.s3 import upload_file, delete_file
import time

@bp_lms.route('/settings/pages/home')
@login_required
def pages_home():
    return admin_render_template(
        Settings, 'lms/pages/home.html', 'learning_management'
    )


@bp_lms.route('/settings/pages/home/our_testimonies/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_our_testimony(oid,**kwargs):
    our_testimony = OurTestimony.objects.get_or_404(id=oid)
    form = OurTestimoniesEditForm(obj=our_testimony)

    if request.method == "GET":

        return admin_edit(
            OurTestimony,
            form,
            'lms.edit_our_testimony',
            oid,
            'lms.pages_home',
            action_template="lms/our_testimony_edit_action.html",
            fields_sizes=[12, 12]
        )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.pages_home'))
        
    try:
        
        our_testimony.title = form.title.data
        our_testimony.description = form.description.data

        file = request.files['image']
        if not (file and allowed_file(file.filename)):
            flash('File is not allowed','error')
            return redirect('/learning-management/settings/pages/home/our_testimonies/' + oid + '/edit')

        output = upload_file(file, f"{int(time.time())}_{file.filename}", 'our_testimonies/')

        if not output:
            flash('Error occured, please contact system administrator','error')
            return redirect('/learning-management/settings/pages/home/our_testimonies/' + oid + '/edit')
            
        our_testimony.image = output

        if form.oldimage.data:
            delete_file(form.oldimage.data, 'our_testimonies/')
        
        our_testimony.save()
        flash('Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.pages_home'))