""" MODULE: AUTH.MODELS """
""" FLASK IMPORTS """
from enum import unique
from flask_login import UserMixin

"""--------------END--------------"""

""" PYTHON IMPORTS """
from werkzeug.security import generate_password_hash, check_password_hash

"""--------------END--------------"""

""" APP IMPORTS  """
from app import login_manager,db
from app.admin.models import Admin
from app.core.models import Base
"""--------------END--------------"""
from mongoengine.document import Document



class Earning(db.EmbeddedDocument):
    custom_id = db.StringField(primary_key=True)
    payment_mode = db.StringField()
    savings = db.DecimalField()
    earnings = db.DecimalField()
    branch = db.ReferenceField('Branch')
    client = db.ReferenceField('Registration')
    date = db.DateTimeField()
    registered_by = db.ReferenceField('User')
    status = db.StringField()
    payment_id = db.StringField()


# AUTH.MODEL.USER
class User(UserMixin, Base, Admin):
    meta = {
        'collection': 'auth_users',
        'strict': False
    }
    __tablename__ = 'auth_users'
    __amname__ = 'user'	
    __amicon__ = 'pe-7s-users'	
    __amdescription__ = "Users"	
    __view_url__ = 'bp_auth.users'

    """ COLUMNS """
    # custom_id = db.StringField(primary_key=True)
    username = db.StringField(unique=True)
    fname = db.StringField()
    lname = db.StringField()
    email = db.EmailField()
    password_hash = db.StringField()
    image_path = db.StringField(default="img/user_default_image.png")
    permissions = db.ListField(db.ReferenceField('UserPermission'))
    is_superuser = db.BooleanField(default=False)
    role = db.ReferenceField('Role')
    is_admin = db.BooleanField(default=False)
    branch = db.ReferenceField('Branch')
    branches = db.ListField()
    earnings = db.ListField(db.EmbeddedDocumentField(Earning))
    father_name = db.StringField()
    mother_name = db.StringField()
    nickname = db.StringField()
    date_of_birth = db.DateField()
    contact_no = db.StringField()
    address = db.StringField()
    full_employee_id = db.StringField()
    employee_id_no = db.IntField()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User {}>".format(self.username)

    @property
    def name(self):
        return self.fname + self.lname

    @property
    def full_name(self):
        return self.fname + " " + self.lname

class UserPermission(db.Document):
    meta = {
        'collection': 'auth_user_permissions'
    }

    model = db.ReferenceField('CoreModel')
    read = db.BooleanField(default=True)
    create = db.BooleanField(default=False)
    write = db.BooleanField(default=False)
    doc_delete = db.BooleanField(default=False)


class Role(Base, Admin):
    meta = {
        'collection': 'auth_user_roles',
        'strict': False,
    }

    __tablename__ = 'auth_user_roles'
    __amname__ = 'role'
    __amicon__ = 'pe-7s-id'
    __amdescription__ = "Roles"
    __view_url__ = 'bp_auth.roles'

    """ COLUMNS """
    name = db.StringField()
    permissions = db.ListField()


class RolePermission(db.Document):
    meta = {
        'collection': 'auth_role_permissions'
    }

    role = db.ReferenceField('Role')
    model = db.ReferenceField('CoreModel')
    read = db.BooleanField(default=True)
    create = db.BooleanField(default=False)
    write = db.BooleanField(default=False)
    doc_delete = db.BooleanField(default=False)


@login_manager.user_loader
def load_user(user_id):
    return User.objects.get(id=user_id)