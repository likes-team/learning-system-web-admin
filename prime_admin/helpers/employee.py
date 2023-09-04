from app.auth.models import User
from flask_login import current_user
from mongoengine.queryset.visitor import Q
from prime_admin.globals import SECRETARYREFERENCE, MARKETERREFERENCE, MANAGEREFERENCE


def get_employees(position, branch_id='all'):
    if branch_id == "all":
        contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_employee=True))
    else:
        contact_persons = User.objects((Q(branches__in=[branch_id]) | Q(branch=branch_id)) & Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_employee=True))

        if position == "Teacher":
            contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_teacher=True))
        elif position == "Staff":
            contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_employee=True))
        elif position == "Secretary":
            contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(role=SECRETARYREFERENCE))
        elif position == "Manager":
            contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(role=MANAGEREFERENCE))
        elif position == "Marketer":
            contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(role=MARKETERREFERENCE))
        else:
            contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_employee=True))

    if contact_persons is None:
        return []

    data = []
    for contact_person in contact_persons:
        data.append(contact_person)
    return data
