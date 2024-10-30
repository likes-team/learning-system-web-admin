from prime_admin import bp_lms
from app.admin.templating import admin_render_template
from prime_admin.models import Settings
from prime_admin.models import OurTestimony
from prime_admin.models import PageSettings
from flask_login import login_required
from flask import redirect, url_for, jsonify, request, flash
from prime_admin.forms import OurTestimoniesEditForm
from prime_admin.forms import PageSettingsEditForm
from app.admin.templating import admin_render_template, admin_edit
from prime_admin.utils.upload import allowed_file
from prime_admin.services.s3 import upload_file, delete_file
import time
import json
from app import mongo

@bp_lms.route('/settings/pages/home', methods=['GET','POST'])
@login_required
def pages_home():
    page_settings_form = PageSettingsEditForm()
    home_background_image = PageSettings.objects.filter(key="home_background_image").first()
    if not home_background_image:
        home_background_image = PageSettings()

    if request.method == "POST":
        file = request.files['home_background_image']
        if (file and allowed_file(file.filename)):
            output = upload_file(file, f"{int(time.time())}_{file.filename}", 'landing_page/')

            if not output:
                flash('Error occured, please contact system administrator','error')
                return redirect('/learning-management/settings/pages/home')
                
            home_background_image.key = "home_background_image"
            home_background_image.value = output

            if request.form.get('old_home_background_image'):
                file_url = request.form.get('old_home_background_image')
                file_name = file_url.split('/')[-1]
                delete_file(file_name, 'landing_page/')

        home_background_image.save()

    our_testimonies_form = OurTestimoniesEditForm()
    our_testimonies_modal_data = {
        'title': 'Add new Our Testimony',
        'fields_sizes': [12,12,12,12]
    }
    return admin_render_template(
        Settings, 'lms/pages/home.html', 'learning_management',\
        OUR_TESTIMONIES_FORM=our_testimonies_form, OUR_TESTIMONIES_MODAL_DATA=our_testimonies_modal_data, PAGE_SETTINGS_FORM=page_settings_form, home_background_image=home_background_image
    )


@bp_lms.route('/settings/pages/home/our_testimonies/create',methods=['GET','POST'])
@login_required
def create_our_testimony():
    form = OurTestimoniesEditForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.pages_home'))

    try:
        our_testimony = OurTestimony()

        # Calculate the sort value as the total number of items + 1
        total_items = mongo.db.lms_our_testimonies.count_documents({})
        our_testimony.sort = total_items + 1

        our_testimony.title = form.title.data
        our_testimony.description = form.description.data
        our_testimony.gallerydescription = form.gallerydescription.data

        file = request.files['image']
        if (file and allowed_file(file.filename)):
            output = upload_file(file, f"{int(time.time())}_{file.filename}", 'our_testimonies/')

            if not output:
                flash('Error occured, please contact system administrator','error')
                return redirect('/learning-management/settings/pages/home')
            
            our_testimony.image = output
        
        our_testimony.save()

        flash('Added Successfully!','success')

        return redirect(url_for('lms.pages_home'))

    except Exception as e:
        flash(str(e),'error')
        return redirect(url_for('lms.pages_home'))
    
@bp_lms.route('/settings/pages/home/our_testimonies/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_our_testimony(oid,**kwargs):
    our_testimony = OurTestimony.objects.get_or_404(id=oid)
    form = OurTestimoniesEditForm(obj=our_testimony)

    if request.method == "GET":
        gallery = []    
        if our_testimony.gallery is not None and our_testimony.gallery.strip():
            try:
                # Attempt to load the gallery as a JSON array
                gallery = json.loads(our_testimony.gallery)

                # Check if gallery is a list and has elements
                if isinstance(gallery, list) and gallery:
                    print("Gallery has values:", gallery)
                else:
                    gallery = []
                    print("Gallery is empty or not a valid list.")

            except json.JSONDecodeError:
                print("Error decoding gallery data.")
            except Exception as e:
                print("An unexpected error occurred:", str(e))

        return admin_edit(
            OurTestimony,
            form,
            'lms.edit_our_testimony',
            oid,
            'lms.pages_home',
            action_template="lms/our_testimony_edit_action.html",
            fields_sizes=[12, 12, 12, 12, 12],
            gallery=gallery
        )
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('lms.pages_home'))
        
    try:
        our_testimony.title = form.title.data
        our_testimony.description = form.description.data
        our_testimony.gallerydescription = form.gallerydescription.data

        file = request.files['image']
        if (file and allowed_file(file.filename)):
            output = upload_file(file, f"{int(time.time())}_{file.filename}", 'our_testimonies/')

            if not output:
                flash('Error occured, please contact system administrator','error')
                return redirect('/learning-management/settings/pages/home/our_testimonies/' + oid + '/edit')
                
            our_testimony.image = output

            if form.oldimage.data:
                file_url = form.oldimage.data
                file_name = file_url.split('/')[-1]
                delete_file(file_name, 'our_testimonies/')
        
        our_testimony.save()
        flash('Updated Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('lms.pages_home'))

    
@bp_lms.route('/settings/pages/home/our_testimonies/<string:oid>/upload-gallery', methods=['POST'])
@login_required
def upload_gallery_our_testimony(oid,**kwargs):
    our_testimony = OurTestimony.objects.get_or_404(id=oid)
    
    new_outputs = []    
    if our_testimony.gallery is not None and our_testimony.gallery.strip():
        try:
            # Attempt to load the gallery as a JSON array
            new_outputs = json.loads(our_testimony.gallery)

            # Check if new_outputs is a list and has elements
            if isinstance(new_outputs, list) and new_outputs:
                print("Gallery has values:", new_outputs)
            else:
                new_outputs = []
                print("Gallery is empty or not a valid list.")

        except json.JSONDecodeError:
            print("Error decoding gallery data.")
        except Exception as e:
            print("An unexpected error occurred:", str(e))
    else:
        print("our_testimony.gallery is empty or None.")

    try:
        file = request.files['image']

        if not (file and allowed_file(file.filename)):
            return jsonify({'success': False, 'message': 'File is not allowed'})

        output = upload_file(file, f"{int(time.time())}_{file.filename}", 'our_testimonies/')

        if not output:
            return jsonify({'success': False, 'message': 'Error occured, please contact system administrator'})
            
        new_outputs.append(output)

        our_testimony.gallery = json.dumps(new_outputs)
        
        our_testimony.save()

        return jsonify({'success': True, 'file_url': output, 'message': 'Updated Successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

    
@bp_lms.route('/settings/pages/home/our_testimonies/<string:oid>/delete-gallery', methods=['POST'])
@login_required
def delete_gallery_our_testimony(oid,**kwargs):
    our_testimony = OurTestimony.objects.get_or_404(id=oid)

    new_outputs = []    
    if our_testimony.gallery is not None and our_testimony.gallery.strip():
        try:
            # Attempt to load the gallery as a JSON array
            new_outputs = json.loads(our_testimony.gallery)

            # Check if new_outputs is a list and has elements
            if isinstance(new_outputs, list) and new_outputs:
                print("Gallery has values:", new_outputs)
            else:
                new_outputs = []
                print("Gallery is empty or not a valid list.")

        except json.JSONDecodeError:
            print("Error decoding gallery data.")
        except Exception as e:
            print("An unexpected error occurred:", str(e))
    else:
        print("our_testimony.gallery is empty or None.")

    try:
        file_url = request.form.get('file_url')

        if file_url:
            file_name = file_url.split('/')[-1]
            delete_file(file_name, 'our_testimonies/')

            # Remove the file_url from new_outputs
            new_outputs = [url for url in new_outputs if url.split('/')[-1] != file_name]

            our_testimony.gallery = json.dumps(new_outputs)
            
            our_testimony.save()

        return jsonify({'success': True, 'message': 'Deleted Successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
