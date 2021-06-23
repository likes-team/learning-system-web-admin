from flask.app import Flask
from flask_wtf import FlaskForm
from app.admin.forms import AdminTableForm, AdminEditForm, AdminInlineForm, AdminField
from wtforms.validators import DataRequired
from wtforms import StringField, SelectField, DecimalField, DateField



class ExpensesForm(AdminTableForm):
    from .models import Inventory

    __table_columns__ = [
        'date', 'description', 'price', 'quantity', 'subtotal'
    ]

    __heading__ = "Operating Expenses"

    inventory = AdminField(label="Description", validators=[DataRequired()], model=Inventory)
    quantity = AdminField(label='Quantity', validators=[DataRequired()], type='number')
    price = AdminField(label='Price', validators=[DataRequired()], type='numeric')
    uom = AdminField(label='Unit of Measurement', required=False)

    @property
    def fields(self):
        return [
            [self.inventory, self.price],
            [self.quantity, self.uom]
            ]


class OrientationAttendanceForm(AdminTableForm):
    __table_columns__ = [
        'Branch',
        'full name',
        'contact no',
        'contact person',
        'orientator'
    ]

    __heading__ = "Orientation Attendance"

    contact_person = StringField()
    orientator = StringField()
    branch = StringField()

    @property
    def fields(self):
        return []


class InventoryForm(AdminTableForm):
    from prime_admin.models import Branch

    __table_columns__ = ['Maintaining Materials', 'Description', 'Released Materials', 'Remaining Materials','Total of replacement Materials']
    __heading__ = "Inventories"

    description = AdminField(label="Description", validators=[DataRequired()])
    maintaining = AdminField(label="Maintaining Materials", required=False, type='number')
    remaining = AdminField(label="Stocks", required=False, type='number')
    price = AdminField(label="Price", validators=[DataRequired()], type='decimal')
    branch = AdminField(label="Branch", validators=[DataRequired()], model=Branch)

    @property
    def fields(self):
        return [
            [self.branch, self.description],
            [self.price, self.maintaining, self.remaining]
            ]



class BatchForm(AdminTableForm):
    from prime_admin.models import Branch

    __table_columns__ = ['Status', 'Number', 'Branch', 'created by','Created at', 'updated by','updated at']
    __heading__ = "Batches"

    number = AdminField(label="Number", validators=[DataRequired()])
    branch = AdminField(label="Branch", validators=[DataRequired()], model=Branch)

    @property
    def fields(self):
        return [
            [self.number, self.branch]
            ]


class BatchEditForm(AdminEditForm):
    from prime_admin.models import Branch

    __heading__ = "Update existing data"

    number = AdminField(label="Number", validators=[DataRequired()])
    branch = AdminField(label="Branch", validators=[DataRequired()], model=Branch)

    @property
    def fields(self):
        return [
            [self.number, self.branch]
            ]



class SecretaryForm(AdminTableForm):
    from prime_admin.models import Branch

    __table_columns__ = ['First Name', 'Last Name', 'Branch', 'created by','Created at', 'updated by','updated at']
    __heading__ = "Secretaries"

    fname = AdminField(label="First Name", validators=[DataRequired()])
    lname = AdminField(label="Last Name", validators=[DataRequired()])
    branch = AdminField(label="Branch", validators=[DataRequired()], model=Branch)
    username = AdminField(label='Username', validators=[DataRequired()])
    email = AdminField(label='Email', type='email',required=False)

    @property
    def fields(self):
        return [
            [self.fname, self.lname],
            [self.username, self.email],
            [self.branch]
            ]


class SecretaryEditForm(AdminEditForm):
    from prime_admin.models import Branch

    __heading__ = "Update existing data"

    fname = AdminField(label="First Name", validators=[DataRequired()])
    lname = AdminField(label="Last Name", validators=[DataRequired()])
    branch = AdminField(label="Branch", validators=[DataRequired()], model=Branch)
    username = AdminField(label='Username', validators=[DataRequired()])
    email = AdminField(label='Email', type='email',required=False)

    @property
    def fields(self):
        return [
            [self.fname, self.lname],
            [self.username, self.email],
            [self.branch]
            ]


class BranchForm(AdminTableForm):
    __table_columns__ = ['Name', 'created by','Created at', 'updated by','updated at']
    __heading__ = "Branches"

    name = AdminField(label="Name", validators=[DataRequired()])
    address = AdminField(label="Address", validators=[DataRequired()])

    @property
    def fields(self):
        return [[self.name, self.address]]


class ContactPersonForm(AdminTableForm):
    __table_columns__ = ['First Name', 'Last Name', 'created by','Created at', 'updated by','updated at']
    __heading__ = "Partners"

    fname = AdminField(label="First Name", validators=[DataRequired()])
    lname = AdminField(label="Last Name", validators=[DataRequired()])
    
    @property
    def fields(self):
        return [[self.fname, self.lname]]


class BranchEditForm(AdminEditForm):
    __heading__ = "Edit Branch"

    name = AdminField(label="Name", validators=[DataRequired()])
    address = AdminField(label="Address", validators=[DataRequired()])

    @property
    def fields(self):
        return [[self.name, self.address]]


class BranchesInlineForm(AdminInlineForm):
    __table_id__ = 'tbl_branches_inline'
    __table_columns__ =[None, 'Branch', '','','','Action']
    __title__ = "current branches"
    __html__ = 'lms/branches_inline.html'


class AddBranchesInline(AdminInlineForm):
    __table_id__ = 'tbl_add_branches_inline'
    __table_columns__ =[None,'Branch', '','','','Action']
    __title__ = "add branches"
    __html__ = 'lms/add_branches_inline.html'


class ContactPersonEditForm(AdminEditForm):
    from .models import Branch

    __heading__ = "Edit Contact Person"

    fname = AdminField(label="First Name", validators=[DataRequired()])
    lname = AdminField(label="Last Name", validators=[DataRequired()])
    
    branches_inline = BranchesInlineForm()
    add_branches_inline = AddBranchesInline()

    @property
    def inlines(self):
        return [self.branches_inline, self.add_branches_inline]

    @property
    def fields(self):
        return [[self.fname, self.lname]]


class PartnerForm(AdminTableForm):
    __table_columns__ = ['Name', 'created by','Created at', 'updated by','updated at']
    __heading__ = "Partners"

    name = AdminField(label="Name", validators=[DataRequired()])

    @property
    def fields(self):
        return [[self.name]]


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
    from .models import Batch
    
    batch_number = AdminField(label='Batch Number', validators=[DataRequired()], model=Batch)

    schedule = SelectField('Schedule',choices=[
        ('WDC','WDC'), ('SDC', 'SDC')
    ])

    branch = SelectField('Branch', choices=[
        ('cebu', 'Cebu'),
        ('tacloban', 'Tacloban'),
        ('bohol', 'Bohol'),
        ('palawan', 'Palawan')
    ])

    amount = DecimalField()
    contact_person = StringField()
    fname = StringField()
    mname = StringField()
    lname = StringField()
    suffix = StringField()
    address = StringField()
    passport = StringField()
    contact_number = StringField()
    email = StringField()
    birth_date = DateField()
    book = StringField()
    payment_mode = StringField()

