from flask_wtf import FlaskForm
from wtforms import validators
from app.admin.forms import AdminTableForm, AdminEditForm, AdminInlineForm, AdminField
from wtforms.validators import DataRequired



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
