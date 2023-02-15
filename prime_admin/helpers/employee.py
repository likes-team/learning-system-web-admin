from app.auth.models import User
from flask_login import current_user
from mongoengine.queryset.visitor import Q



def get_employees(branch_id='all'):
    if branch_id == "all":
        contact_persons = User.objects(Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_employee=True))
    else:
        contact_persons = User.objects((Q(branches__in=[branch_id]) | Q(branch=branch_id)) & Q(is_superuser=False) & Q(id__ne=current_user.id) & Q(is_employee=True))

    if contact_persons is None:
        return []

    data = []
    for contact_person in contact_persons:
        data.append(contact_person)
    return data
