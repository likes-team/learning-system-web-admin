from app import db
from app.admin.models import Admin
from app.core.models import Base



class Teacher(Base, Admin):
    meta = {
        'collection': 'lms_teachers'
    }

    __tablename__ = 'lms_teachers'
    __amname__ = 'teacher'
    __amdescription__ = 'Teachers'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'lms.teachers'
    
    """ COLUMNS """
    fname = db.StringField()
    mname = db.StringField()
    lname = db.StringField()


class Student(Base, Admin):
    meta = {
        'collection': 'lms_students'
    }

    __tablename__ = 'lms_students'
    __amname__ = 'student'
    __amdescription__ = 'Students'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'lms.students'

    """ COLUMNS """
    fname = db.StringField()
    mname = db.StringField()
    lname = db.StringField()


class TrainingCenter(Base, Admin):
    meta = {
        'collection': 'lms_training_centers'
    }

    __tablename__ = 'lms_training_centers'
    __amname__ = 'training_center'
    __amdescription__ = 'Training Centers'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'lms.training_centers'

    """ COLUMNS """
    name = db.StringField()


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
    contact_person = db.StringField()
    fname = db.StringField()
    mname = db.StringField()
    lname = db.StringField()

    @property
    def full_name(self):
        return self.fname + " " + self.mname + " " + self.lname


class Member(Admin):
    __amname__ = 'member'
    __amdescription__ = 'Members'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'bp_admin.under_construction'


class Earning(Admin):
    __amname__ = 'earning'
    __amdescription__ = 'Earnings'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'bp_admin.under_construction'


class Partner(Admin):
    __amname__ = 'partner'
    __amdescription__ = 'Partners'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'bp_admin.under_construction'


class Secretary(Admin):
    __amname__ = 'partner'
    __amdescription__ = 'Secretary'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'bp_admin.under_construction'


class OrientationAttendance(Admin):
    __amname__ = 'orientation_attendance'
    __amdescription__ = 'Orientation Attendance'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'bp_admin.under_construction'


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
