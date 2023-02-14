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



def get_employees(branch_id='all'):
    if branch_id == "all":
        contact_persons = User.objects(Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_teacher=True) | Q(role=PARTNERREFERENCE))
    else:
        contact_persons = User.objects(Q(branches__in=[branch_id]) & Q(role__ne=SECRETARYREFERENCE) & Q(is_superuser=False) & Q(id__ne=current_user.id) | Q(role=PARTNERREFERENCE))

    if contact_persons is None:
        return []

    data = []
    for contact_person in contact_persons:
        data.append(contact_person)
    return data
