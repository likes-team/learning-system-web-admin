from threading import local
import pytz
from config import TIMEZONE
from datetime import datetime
from enum import unique
from mongoengine.fields import DateField, EmbeddedDocumentListField
from app import db
from app.admin.models import Admin
from app.core.models import Base
from bson.objectid import ObjectId



class Payment(db.EmbeddedDocument):
    # custom_id = db.StringField(primary_key=True)
    _id = db.ObjectIdField( required=True, default=lambda: ObjectId())
    deposited = db.StringField()
    payment_mode = db.StringField()
    amount = db.DecimalField()
    current_balance = db.DecimalField()
    confirm_by = db.ReferenceField('User')
    date = db.DateTimeField()
    payment_by = db.ReferenceField('Registration')
    earnings = db.DecimalField()
    savings = db.DecimalField()
    status = db.StringField()

    @property
    def id(self):
        if not self._id:
            return ''

        return str(self._id)


class Registration(Base, Admin):
    meta = {
        'collection': 'lms_registrations',
        'strict': False
    }

    __tablename__ = 'lms_registrations'
    __amname__ = 'registration'
    __amdescription__ = 'Register'
    __amicon__ = 'pe-7s-add-user'
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
    id_materials = db.DictField()
    payment_mode = db.StringField()
    status = db.StringField()
    is_oriented = db.BooleanField()
    date_oriented = db.DateTimeField()
    orientator = db.ReferenceField('Orientator')
    # payments = db.ListField()
    payments = db.EmbeddedDocumentListField(Payment)
    # payments = db.ListField(db.EmbeddedDocumentField(Payment))
    e_registration = db.StringField()
    referred_by = db.ReferenceField('Registration')
    level = db.StringField()
    fle = db.DecimalField()
    sle = db.DecimalField()
    registration_date = db.DateTimeField()
    amount_deposit = db.DecimalField()
    copy_payments = db.ListField()
    
    def set_registration_date(self):
        date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
        naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        local_dt = TIMEZONE.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        self.registration_date = utc_dt

    @property
    def registration_date_local_string(self):
        local_datetime = ''
        if self.registration_date is not None:
            local_datetime = self.registration_date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
            return local_datetime.strftime("%B %d, %Y %I:%M %p")
            
        return local_datetime

    @property
    def registration_date_local_date(self):
        if self.registration_date is not None:
            local_datetime = self.registration_date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
            date_string = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
            registration_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return registration_date

        return None

    @property
    def oriented_date_local(self):
        local_datetime = ''
        if self.date_oriented is not None:
            local_datetime = self.date_oriented.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
            return local_datetime.strftime("%B %d, %Y %I:%M %p")
            
        return local_datetime

    @property
    def full_name(self):
        if self.mname:
            return self.fname + " " + self.mname + " " + self.lname
        
        return self.fname + " " + self.lname


class Branch(Base, Admin):
    meta = {
        'collection': 'lms_branches',
        'strict': False,
    }

    __tablename__ = 'lms_branches'
    __amname__ = 'branch'
    __amdescription__ = 'Branches'
    __amicon__ = 'pe-7s-network'
    __view_url__ = 'lms.branches'

    name = db.StringField()
    address = db.StringField()
    maintaining_balance = db.DecimalField()


class Batch(Base, Admin):
    meta = {
        'collection': 'lms_batches',
        'strict': False,
    }

    __tablename__ = 'lms_batches'
    __amname__ = 'batch'
    __amdescription__ = 'Batch Numbers'
    __amicon__ = 'pe-7s-date'
    __view_url__ = 'lms.batches'

    number = db.StringField(unique=True)
    branch = db.ReferenceField('Branch')
    start_date = db.DateTimeField()


class Partner(Admin):
    __tablename__ = 'auth_user'
    __amname__ = 'partner'
    __amdescription__ = 'Partners'
    __amicon__ = 'pe-7s-user'
    __view_url__ = 'lms.contact_persons'

class Orientator(Base, Admin):
    meta = {
        'collection': 'lms_orientators',
        'strict': False,
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


class InboundOutbound(db.EmbeddedDocument):
    # custom_id = db.StringField(primary_key=True)
    _id = db.ObjectIdField( required=True, default=lambda: ObjectId())
    brand = db.StringField()
    price = db.DecimalField()
    quantity = db.IntField()
    total_amount = db.DecimalField()
    remarks = db.StringField()
    date = db.DateTimeField()
    withdraw_by =db.StringField()
    confirm_by = db.ReferenceField('User')

    @property
    def id(self):
        if not self._id:
            return ''

        return str(self._id)

class Inventory(Base, Admin):
    meta = {
        'collection': 'lms_inventories',
        'strict': False,
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
    uom = db.StringField()
    qty = db.StringField()
    purchase_date = db.DateTimeField()
    transactions = db.EmbeddedDocumentListField(InboundOutbound)
    is_for_sale = db.BooleanField()

    @property
    def name(self):
        return self.description


class Marketer(Admin):
    __tablename__ = 'auth_users'
    __amname__ = 'marketer'
    __amdescription__ = 'Marketers'
    __amicon__ = 'pe-7s-user'
    __view_url__ = 'lms.marketers'

class Member(Admin):
    __tablename__ = 'lms_members'
    __amname__ = 'member'
    __amdescription__ = 'Student Records'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'lms.members'


class Earning(Admin):
    __tablename__ = 'lms_earnings'
    __amname__ = 'earning'
    __amdescription__ = 'Earnings'
    __amicon__ = 'pe-7s-cash'
    __view_url__ = 'lms.earnings'


class Secretary(Admin):
    __tablename__ = 'auth_users'
    __amname__ = 'secretary'
    __amdescription__ = 'Secretary'
    __amicon__ = 'pe-7s-user'
    __view_url__ = 'lms.secretaries'


class OrientationAttendance(Admin):
    __tablename__ = 'lms_orientation_attendance'
    __amname__ = 'orientation_attendance'
    __amdescription__ = 'Orientation Attendance'
    __amicon__ = 'pe-7s-note2'
    __view_url__ = 'lms.orientation_attendance'



class Dashboard(Admin):
    __amname__ = 'dashboard'
    __amdescription__ = 'Dashboard'
    __amicon__ = 'pe-7s-graph2'
    __view_url__ = 'lms.dashboard'


class Equipment(Admin):
    __tablename__ = 'lms_inventories'
    __amname__ = 'equipment'
    __amdescription__ = 'Equipments'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.equipments'


class CashFlow(Base, Admin):
    meta = {
        'collection': 'lms_bank_statements',
        'strict': False,

    }
    
    __tablename__ = 'lms_bank_statements'
    __amname__ = 'cash_flow'
    __amdescription__ = 'Cash Flow'
    __amicon__ = 'pe-7s-refresh-2'
    __view_url__ = 'lms.cash_flow'
    
    date_deposit = db.DateField()
    bank_name = db.StringField()
    account_no = db.StringField()
    account_name = db.StringField()
    amount = db.DecimalField()
    from_what = db.StringField()
    by_who = db.StringField()
    type = db.StringField()
    branch = db.ReferenceField('Branch')
    balance = db.DecimalField()
    group = db.IntField()
    payments = db.EmbeddedDocumentListField(Payment)
    remarks = db.StringField()

    def set_deposit_date(self):
        date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
        naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        local_dt = TIMEZONE.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        self.date_deposit = utc_dt

    @property
    def deposit_date_local_string(self):
        local_datetime = ''
        if self.date_deposit is not None:
            local_datetime = self.date_deposit.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
            return local_datetime.strftime("%B %d, %Y %I:%M %p")
            
        return local_datetime

    # @property
    # def registration_date_local_date(self):
    #     if self.registration_date is not None:
    #         local_datetime = self.registration_date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    #         date_string = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
    #         registration_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    #         return registration_date

    #     return None

class Accounting(Base):
    meta = {
        'collection': 'lms_accounting',
        'strict': False,
    }
    
    branch = db.ReferenceField('Branch')
    total_gross_sale = db.DecimalField()
    final_fund1 = db.DecimalField()
    final_fund2 = db.DecimalField()
    profits = db.ListField()
    active_group = db.IntField()

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


class CashOnHand(Admin):
    __tablename__ = 'lms_cash_on_hand'
    __amname__ = 'cash_on_hand'
    __amdescription__ = 'Cash On Hand'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.cash_on_hand'


class FundWallet(Admin, Base):
    meta = {
        'collection': 'lms_fund_wallet_transactions',
        'strict': False,
    }

    __tablename__ = 'lms_fund_wallet_transactions'
    __amname__ = 'fund_wallet'
    __amdescription__ = 'Fund Wallet'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.fund_wallet'

    date = db.DateTimeField()
    branch = db.ReferenceField('Branch')
    bank_name = db.StringField()
    transaction_no = db.StringField()
    sender = db.StringField()
    receiver = db.StringField()
    amount_received = db.DecimalField()
    remarks = db.StringField()



class Expenses(Base, Admin):
    meta = {
        'collection': 'lms_expenses_transactions',
        'strict': False,
    }
    
    __tablename__ = 'lms_expenses_transactions'
    __amname__ = 'expenses'
    __amdescription__ = 'Operating Expenses'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.expenses'

    date = db.DateTimeField()
    branch = db.ReferenceField('Branch')
    category = db.StringField()
    account_no = db.StringField()
    billing_month = db.StringField()
    settled_by = db.StringField()
    total_amount_due = db.DecimalField()
    remarks = db.StringField()


class Item(db.EmbeddedDocument):
    meta = {
        'strict': False,
    }

    item = db.ReferenceField("Inventory")
    qty = db.IntField()
    price = db.DecimalField()
    amount = db.DecimalField()


class StoreRecords(Base, Admin):
    meta = {
        'collection': 'lms_store_buyed_items',
        'strict': False,
    }

    __tablename__ = 'lms_store_buyed_items'
    __amname__ = 'store_records'
    __amdescription__ = 'Store Records'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.store_records'

    branch : Branch = db.ReferenceField('Branch')
    client_id : Registration = db.ReferenceField('Registration')
    items = db.EmbeddedDocumentListField(Item)
    total_amount = db.DecimalField()
    uniforms = db.IntField()
    id_lace = db.IntField()
    id_card =db.IntField()
    module_1 = db.IntField()
    module_2 = db.IntField()
    reviewer_l = db.IntField()
    reviewer_r = db.IntField()
    deposited = db.StringField()

    @property
    def local_datetime(self):
        if type(self.created_at) == datetime:
            local_datetime = self.created_at.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(self.created_at == str):
            to_date = datetime.strptime(self.created_at, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''

        return local_datetime



class BuyItems(Admin):
    __tablename__ = 'lms_buy_items'
    __amname__ = 'buy_items'
    __amdescription__ = 'Buy Items'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.buy_items'


class Accommodation(Base, Admin):
    meta = {
        'collection': 'lms_accommodations',
        'strict': False
    }

    __tablename__ = 'lms_accommodations'
    __amname__ = 'accommodation'
    __amdescription__ = 'Accommodation'
    __amicon__ = 'pe-7s-tools'
    __view_url__ = 'lms.accommodation'

    client_id = db.ReferenceField('Registration')
    branch = db.ReferenceField('Branch')
    date_from = db.DateField()
    date_to = db.DateField()
    days = db.IntField()
    total_amount = db.DecimalField()
    remarks = db.StringField()
    deposited = db.StringField()

    @property
    def local_datetime(self):
        if type(self.created_at) == datetime:
            local_datetime = self.created_at.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime("%B %d, %Y")
        elif type(self.created_at == str):
            to_date = datetime.strptime(self.created_at, "%Y-%m-%d")
            local_datetime = to_date.strftime("%B %d, %Y")
        else: 
            local_datetime = ''

        return local_datetime