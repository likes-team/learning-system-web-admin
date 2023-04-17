from flask_login import current_user
from prime_admin.models import Branch, Batch



def get_current_user_branches():
    if current_user.role.name == "Admin":
        branches = Branch.objects
    elif current_user.role.name == 'Manager':
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Marketer":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Partner":
        branches = Branch.objects(id__in=current_user.branches)
    elif current_user.role.name == "Secretary":
        branches = Branch.objects(id=current_user.branch.id)
    return branches


def get_current_user_batches():
    if current_user.role.name == "Admin":
        batch_numbers = Batch.objects()
    elif current_user.role.name == 'Manager':
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
    elif current_user.role.name == 'Marketer':
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
    elif current_user.role.name == "Partner":
        batch_numbers = Batch.objects(active=True).filter(branch__in=current_user.branches).all()
    elif current_user.role.name == "Secretary":
        batch_numbers = Batch.objects(branch=current_user.branch.id)
    return batch_numbers
