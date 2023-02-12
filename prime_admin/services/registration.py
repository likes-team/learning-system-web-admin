import decimal
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128
from flask_login import current_user
from prime_admin.models import Registration, Branch, Batch
from prime_admin.forms import RegistrationForm
from prime_admin.globals import SECRETARYREFERENCE, convert_to_utc, get_date_now
from prime_admin.services.inventory import InventoryService



class RegistrationService:
    def __init__(self, student: Registration):
        self.student = student
        self.earnings = None
        self.savings = None
        self.payment = None
        self.marketer_earning = None
    
    @classmethod
    def fill_up_form(
        cls, student_id, form: RegistrationForm,
        last_registration_number, registration_generated_number,
        payment_mode
    ):
        student: Registration = Registration.objects.get(id=student_id)
        student.mname = form.mname.data
        student.suffix = form.suffix.data
        student.address = form.address.data
        student.contact_number = form.contact_number.data
        student.email = form.email.data
        student.birth_date = form.birth_date.data
        student.e_registration = form.e_registration.data
        student.registration_number = last_registration_number.registration_number + 1 if last_registration_number is not None else 1
        student.full_registration_number = registration_generated_number
        student.schedule = form.schedule.data
        student.branch = Branch.objects.get(id=form.branch.data)
        student.batch_number = Batch.objects.get(id=form.batch_number.data)
        student.passport = form.passport.data
        student.amount = form.amount.data
        student.payment_mode = payment_mode
        student.created_by = "{} {}".format(current_user.fname,current_user.lname)
        student.civil_status = form.civil_status.data
        student.gender = form.gender.data
        student.session = form.session.data
        student.set_registration_date()
        return cls(student)


    def get_student(self):
        return self.student
    
    
    def set_books(self, books):
        self.student.books = {
            'book_none': True if 'book_none' in books else False,
            'volume1': True if 'volume1' in books else False,
            'volume2': True if 'volume2' in books else False,
        }
        
    def set_uniform(self, uniforms):
        self.student.uniforms = {
            'uniform_none': True if 'uniform_none' in uniforms else False,
            'uniform_xs': True if 'uniform_xs' in uniforms else False,
            'uniform_s': True if 'uniform_s' in uniforms else False,
            'uniform_m': True if 'uniform_m' in uniforms else False,
            'uniform_l': True if 'uniform_l' in uniforms else False,
            'uniform_xl': True if 'uniform_xl' in uniforms else False,
            'uniform_xxl': True if 'uniform_xxl' in uniforms else False,
        }
        
    def set_id_materials(self, id_materials):
        self.student.id_materials = {
            'id_card': True if 'id_card' in id_materials else False,
            'id_lace': True if 'id_lace' in id_materials else False,
        }
        
    def set_reviewers(self, reviewers):
        self.student.reviewers = {
            'reading': True if 'reading' in reviewers else False,
            'listening': True if 'listening' in reviewers else False,
        }
        
    def compute_marketer_earnings(self):
        earnings = 0
        savings = 0
        if self.student.level == "first":
            earnings_percent = decimal.Decimal(0.14)
            savings_percent = decimal.Decimal(0.00286)
        elif self.student.level == "second":
            earnings_percent = decimal.Decimal(0.0286)
            savings_percent = decimal.Decimal(0.00)
        else:
            earnings_percent = decimal.Decimal(0.00)
            savings_percent = decimal.Decimal(0.00)

        if self.student.payment_mode == "full_payment":
            self.student.balance = 8500 - self.student.amount
            earnings = 8500 * earnings_percent
            savings = 8500 * savings_percent
        elif self.student.payment_mode == "installment":
            self.student.balance = 9000 - self.student.amount
            earnings = self.student.amount * earnings_percent
            savings = self.student.amount * savings_percent
        elif self.student.payment_mode == 'premium':
            self.student.balance = 10000 - self.student.amount
            earnings = 10000 * earnings_percent
            savings = 10000 * savings_percent
        elif self.student.payment_mode == "full_payment_promo":
            self.student.balance = 5500 - self.student.amount
            earnings = 5500 * earnings_percent
            savings = 5500 * savings_percent
        elif self.student.payment_mode == "installment_promo":
            self.student.balance = 6300 - self.student.amount
            earnings = self.student.amount * earnings_percent
            savings = self.student.amount * savings_percent
        elif self.student.payment_mode == 'premium_promo':
            self.student.balance = 7000 - self.student.amount
            earnings = 7000 * earnings_percent
            savings = 7000 * savings_percent

        if self.student.level == "first":
            self.student.fle = earnings
            self.student.sle = decimal.Decimal(0.00)
        elif self.student.level == "second":
            self.student.sle = earnings
            self.student.fle = decimal.Decimal(0.00)
        else:
            self.student.fle = decimal.Decimal(0.00)
            self.student.sle = decimal.Decimal(0.00)

        self.earnings = earnings
        self.savings = savings

    def set_payment(self):
        self.payment = {
            "_id": ObjectId(),
            "deposited": "Pre Deposit",
            "payment_mode": self.student.payment_mode,
            "amount": Decimal128(str(self.student.amount)),
            "current_balance": Decimal128(str(self.student.balance)),
            "confirm_by": current_user.id,
            "date": get_date_now(),
            "payment_by": ObjectId(self.student.id),
            "earnings": Decimal128(str(self.earnings)),
            "savings": Decimal128(str(self.savings)),
            "branch": ObjectId(self.student.branch.id)
        }
        
    def get_payment_dict(self):
        return self.payment
    
    def set_marketer_earning(self):
        self.marketer_earning = {
            "_id": ObjectId(),
            "payment_mode": self.student.payment_mode,
            "savings": Decimal128(str(self.savings)),
            "earnings": Decimal128(str(self.earnings)),
            "branch": self.student.branch.id,
            "client": self.student.id,
            "date": get_date_now(),
            "registered_by": current_user.id,
            "payment_id": self.payment['_id']
        }
         
    def get_marketer_earning_dict(self):
        return self.marketer_earning

    def get_earnings(self):
        return self.earnings
    
    def get_savings(self):
        return self.savings
    
    
    def process_supplies(self, session):
        if self.student.books['volume1']:
            InventoryService.minus_stocks(self.student.branch.id, 'volume1', 1, session)

        if self.student.books['volume2']:
            InventoryService.minus_stocks(self.student.branch.id, 'volume2', 1, session)

        if not self.student.uniforms['uniform_none']:
            InventoryService.minus_stocks(self.student.branch.id, 'uniform', 1, session)
         
        if self.student.id_materials['id_card']:
            InventoryService.minus_stocks(self.student.branch.id, 'id_card', 1, session)
       
        if self.student.id_materials['id_lace']:
            InventoryService.minus_stocks(self.student.branch.id, 'id_lace', 1, session)
      
        if self.student.reviewers['reading']:
            InventoryService.minus_stocks(self.student.branch.id, 'reading', 1, session)
     
        if self.student.reviewers['listening']:
            InventoryService.minus_stocks(self.student.branch.id, 'listening', 1, session)
   
    # def process_enrollment():
        # TODO
