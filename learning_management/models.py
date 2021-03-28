from app import db
from app.admin.models import Admin
from app.core.models import Base



class Teacher(Base, Admin):
    __tablename__ = 'lms_teachers'
    __amname__ = 'teacher'
    __amdescription__ = 'Teachers'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'lms.teachers'
    
    """ COLUMNS """
    fname = db.Column(db.String(64), nullable=True)
    mname = db.Column(db.String(64), nullable=True)
    lname = db.Column(db.String(64), nullable=True)


class Student(Base, Admin):
    __tablename__ = 'lms_students'
    __amname__ = 'student'
    __amdescription__ = 'Students'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'lms.students'

    """ COLUMNS """
    fname = db.Column(db.String(64), nullable=True)
    mname = db.Column(db.String(64), nullable=True)
    lname = db.Column(db.String(64), nullable=True)


class TrainingCenter(Base, Admin):
    __tablename__ = 'lms_training_centers'
    __amname__ = 'training_center'
    __amdescription__ = 'Training Centers'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'lms.training_centers'

    """ COLUMNS """
    name = db.Column(db.String(64), nullable=True)