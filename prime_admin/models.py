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
    branch = db.StringField()
    batch_number = db.IntField()
    amount = db.DecimalField()
    balance = db.DecimalField()
    contact_person = db.StringField()
    fname = db.StringField()
    mname = db.StringField()
    lname = db.StringField()
    suffix = db.StringField()
    address = db.StringField()
    passport = db.StringField()
    contact_number = db.StringField()
    email = db.StringField()
    birth_date = db.DateField()
    book = db.StringField()
    payment_mode = db.StringField()


    @property
    def full_name(self):
        return self.fname + " " + self.mname + " " + self.lname


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


class ContactPerson(Base, Admin):
    meta = {
        'collection': 'lms_contact_persons'
    }

    __tablename__ = 'lms_contact_persons'
    __amname__ = 'contact_person'
    __amdescription__ = 'Partners'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.contact_persons'

    fname = db.StringField()
    lname = db.StringField()
    branches = db.ListField()
    earnings = db.ListField()

    @property
    def name(self):
        return self.fname

class Member(Admin):
    __tablename__ = 'lms_members'
    __amname__ = 'member'
    __amdescription__ = 'Members'
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


class Expenses(Admin):
    __tablename__ = 'lms_expenses'
    __amname__ = 'expenses'
    __amdescription__ = 'Expenses'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.expenses'


class Inventory(Admin):
    __amname__ = 'inventory'
    __amdescription__ = 'Inventory'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'bp_admin.under_construction'


class Dashboard(Admin):
    __amname__ = 'dashboard'
    __amdescription__ = 'Dashboard'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.dashboard'
