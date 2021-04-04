from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms.widgets.core import Select
from app.admin.forms import AdminTableForm, AdminEditForm, AdminInlineForm, AdminField
from wtforms.validators import DataRequired
from wtforms import StringField, SelectField



class TrainingCenterForm(AdminTableForm):
    __table_columns__ = ['Name', 'created by','Created at', 'updated by','updated at']
    __heading__ = "Training Centers"

    name = AdminField(label="Name", validators=[DataRequired()])

    @property
    def fields(self):
        return [[self.name]]


class TrainingCenterEditForm(AdminEditForm):
    __heading__ = "Edit Training Center"

    name = AdminField(label="Name", validators=[DataRequired()])

    @property
    def fields(self):
        return [[self.name]]


class TeacherForm(AdminTableForm):
    __table_columns__ = ['First name', 'middle name', 'last name','created by','Created at', 'updated by','updated at']
    __heading__ = "Teachers"

    fname = AdminField(label="First name",validators=[DataRequired()])
    lname = AdminField(label="Last name",validators=[DataRequired()])
    mname = AdminField(label="Middle name",required=False)

    @property
    def fields(self):
        return [[self.fname, self.mname, self.lname]]


class TeacherEditForm(AdminEditForm):
    __heading__ = 'Edit teacher'

    fname = AdminField(label="First name",validators=[DataRequired()])
    lname = AdminField(label="Last name",validators=[DataRequired()])
    mname = AdminField(label="Middle name",required=False)

    @property
    def fields(self):
        return [[self.fname, self.mname, self.lname]]


class StudentForm(AdminTableForm):
    __table_columns__ = ['First name', 'middle name', 'last name', 'created by','Created at', 'updated by','updated at']
    __heading__ = "Students"

    fname = AdminField(label="First name",validators=[DataRequired()])
    lname = AdminField(label="Last name",validators=[DataRequired()])
    mname = AdminField(label="Middle name",required=False)

    @property
    def fields(self):
        return [[self.fname, self.mname, self.lname]]


class StudentEditForm(AdminEditForm):
    __heading__ = 'Edit student'

    fname = AdminField(label="First name",validators=[DataRequired()])
    lname = AdminField(label="Last name",validators=[DataRequired()])
    mname = AdminField(label="Middle name",required=False)

    @property
    def fields(self):
        return [[self.fname, self.mname, self.lname]]


class RegistrationForm(FlaskForm):
    po_number = StringField()
    
    status = StringField()
    
    supplier_id = StringField()
    
    schedule = SelectField('Schedule',choices=[
        ('WDC','WDC'), ('SDC', 'SDC')
    ])

    branch = SelectField('Branch', choices=[
        ('cebu', 'Cebu'),
        ('tacloban', 'Tacloban'),
        ('bohol', 'Bohol'),
        ('palawan', 'Palawan')
    ])

    contact_person = SelectField('Contact Person', choices=[
        ('Gerson', 'Gerson'),
        ('Carlo', 'Carlo'),
        ('Dhan', 'Dhan'),
        ('Hairel', 'Hairel'),
        ('Aim', 'Aim'),
        ('Russel', 'Russel'),
        ('Ace', 'Ace'),
        ('Vincent', 'Vincent'),
        ('Jay-r', 'Jay-r'),
        ('Maevellyn', 'Maevellyn'),
        ('Greggy', 'Greggy'),
        ('Rowee', 'Rowee'),
        ('Jhie', 'Jhie')
    ])

    warehouse_id = StringField()
    
    address = StringField()
    
    ordered_date = StringField()
    
    delivery_date = StringField()
    
    approved_by = StringField()
    
    remarks = StringField()