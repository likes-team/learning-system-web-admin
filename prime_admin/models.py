from datetime import datetime
from enum import unique
from app import db
from app.admin.models import Admin
from app.core.models import Base



class Registration(Base, Admin):
    meta = {
        'collection': 'lms_registrations'
    }

    __tablename__ = 'lms_registrations'
    __amname__ = 'registration'
    __amdescription__ = 'Register'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.register'

    registration_number = db.IntField()
    full_registration_number = db.StringField()
    schedule = db.StringField()
    branch = db.ReferenceField('Branch')
    batch_number = db.ReferenceField('Batch')
    amount = db.DecimalField()
    balance = db.DecimalField()
    contact_person = db.ReferenceField('User')
    fname = db.StringField()
    mname = db.StringField()
    lname = db.StringField()
    gender = db.StringField()
    suffix = db.StringField()
    address = db.StringField()
    passport = db.StringField()
    contact_number = db.StringField()
    email = db.StringField()
    birth_date = db.DateField()
    books = db.DictField()
    uniforms = db.DictField()
    payment_mode = db.StringField()
    status = db.StringField()
    is_oriented = db.BooleanField()
    date_oriented = db.DateTimeField()
    orientator = db.ReferenceField('Orientator')
    payments = db.ListField()
    e_registration = db.StringField()

    @property
    def full_name(self):
        if self.mname:
            return self.fname + " " + self.mname + " " + self.lname
        
        return self.fname + " " + self.lname


class Branch(Base, Admin):
    meta = {
        'collection': 'lms_branches'
    }

    __tablename__ = 'lms_branches'
    __amname__ = 'branch'
    __amdescription__ = 'Branches'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.branches'

    name = db.StringField()
    address = db.StringField()


class Batch(Base, Admin):
    meta = {
        'collection': 'lms_batches'
    }

    __tablename__ = 'lms_batches'
    __amname__ = 'batch'
    __amdescription__ = 'Batch Numbers'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.batches'

    number = db.StringField(unique=True)
    branch = db.ReferenceField('Branch')


class Partner(Admin):
    __tablename__ = 'auth_user'
    __amname__ = 'partner'
    __amdescription__ = 'Partners'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.contact_persons'

class Orientator(Base, Admin):
    meta = {
        'collection': 'lms_orientators'
    }

    __tablename__ = 'lms_orientators'
    __amname__ = 'orientator'
    __amdescription__ = 'Orientators'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.contact_persons'

    fname = db.StringField()
    lname = db.StringField()

    @property
    def name(self):
        return self.fname


class Inventory(Base, Admin):
    meta = {
        'collection': 'lms_inventories'
    }
    __amname__ = 'inventory'
    __amdescription__ = 'Inventory'
    __amicon__ = 'pe-7s-tools'

    price = db.DecimalField()
    description = db.StringField()
    maintaining = db.IntField()
    released = db.IntField()
    remaining = db.IntField()
    total_replacement = db.IntField()
    type = db.StringField()
    branch = db.ReferenceField('Branch')

    @property
    def name(self):
        return self.description


class Marketer(Admin):
    __tablename__ = 'auth_users'
    __amname__ = 'marketer'
    __amdescription__ = 'Marketers'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.marketers'

class Member(Admin):
    __tablename__ = 'lms_members'
    __amname__ = 'member'
    __amdescription__ = 'Student Records'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.members'


class Earning(Admin):
    __tablename__ = 'lms_earnings'
    __amname__ = 'earning'
    __amdescription__ = 'Earnings'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.earnings'


class Secretary(Admin):
    __tablename__ = 'auth_users'
    __amname__ = 'secretary'
    __amdescription__ = 'Secretary'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.secretaries'


class OrientationAttendance(Admin):
    __tablename__ = 'lms_orientation_attendance'
    __amname__ = 'orientation_attendance'
    __amdescription__ = 'Orientation Attendance'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.orientation_attendance'


class Expenses(Base, Admin):
    meta = {
        'collection': 'lms_expenses'
    }
    
    __tablename__ = 'lms_expenses'
    __amname__ = 'expenses'
    __amdescription__ = 'Operating Expenses'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.expenses'

    quantity = db.IntField()
    inventory = db.ReferenceField('Inventory')
    uom = db.StringField()
    price = db.DecimalField()
    total = db.DecimalField()
    branch = db.ReferenceField('Branch')


class Dashboard(Admin):
    __amname__ = 'dashboard'
    __amdescription__ = 'Dashboard'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.dashboard'


class Equipment(Admin):
    __tablename__ = 'lms_inventories'
    __amname__ = 'equipment'
    __amdescription__ = 'Equipments'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.equipments'


class Supplies(Admin):
    __tablename__ = 'lms_inventories'
    __amname__ = 'supplies'
    __amdescription__ = 'Supplies'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.supplies'


class Utilities(Admin):
    __tablename__ = 'lms_inventories'
    __amname__ = 'utilities'
    __amdescription__ = 'Utilities'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.utilities'
