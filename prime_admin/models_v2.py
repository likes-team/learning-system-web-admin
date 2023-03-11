from prime_admin.utils.date import format_utc_to_local, convert_utc_to_local
from prime_admin.utils.currency import convert_decimal128_to_decimal, format_to_str_php



class Document(object):
    def __init__(self, document):
        self.document = document
        self.__dict__.update(document)


    def get_id(self):
        return self.document['_id']


class UserV2(Document):
    # def __init__(self, document):
    #     super().__init__(document)
    
    def get_full_name(self):
        return "{} {}".format(self.document.get('fname'), self.document.get('lname'))
    

class PaymentV2(Document):
    def __init__(self, document):
        super().__init__(document)
        self.student: StudentV2 = None
        self.branch: BranchV2 = None

        if 'student' in document:
            self.student = StudentV2(document['student'])
        if 'branch' in document:
            self.branch = BranchV2(document['branch'])
        if 'batch_no' in document:
            self.student.batch_no = BatchV2(document['batch_no'])
            
    def get_earnings(self, currency=False):
        if currency:
            return format_to_str_php(self.document.get('earnings'))
        return convert_decimal128_to_decimal(self.document.get('earnings'))

    def get_status(self):
        return self.document.get('status')
    
    def get_date(self):
        return format_utc_to_local(self.document['date'], date_format="%B %d, %Y %H:%M %p")

            
class BranchV2(Document):
    def __init__(self, document):
        super().__init__(document)
        
    def get_name(self):
        return self.document.get('name')


class BatchV2(Document):
    def __init__(self, document):
        super().__init__(document)
        
    def get_no(self):
        return self.document.get('number')
    
    def get_start_date(self):
        return convert_utc_to_local(self.document.get('start_date'))


class StudentV2(Document):
    def __init__(self, document):
        super().__init__(document)
        self.branch: BranchV2 = None
        self.batch_no: BatchV2 = None
        # self.branch = branch if branch else None
        # self.batch_no = batch_no if batch_no else None


    def get_registration_date(self, date_format="%B %d, %Y %I:%M %p"):
        return format_utc_to_local(self.document.get('registration_date'), date_format=date_format)
    
    def get_session(self):
        return self.document.get('session', '')
    
    def get_fle(self):
        return convert_decimal128_to_decimal(self.document.get('fle'))

    def get_sle(self):
        return convert_decimal128_to_decimal(self.document.get('sle'))

    def get_payment_mode(self):
        payment_mode = ""
        if self.payment_mode == 'full_payment':
            payment_mode = "Full Payment"
        elif self.payment_mode == 'installment':
            payment_mode = "Installment"
        elif self.payment_mode == 'premium':
            payment_mode = "Premium Payment"
        elif self.payment_mode == 'full_payment_promo':
            payment_mode = "Full Payment - Promo"
        elif self.payment_mode == 'installment_promo':
            payment_mode = "Installment - Promo"
        elif self.payment_mode == 'premium_promo':
            payment_mode = "Premium Payment - Promo"
        elif self.payment_mode == "refund":
            payment_mode = "Refunded"
        return payment_mode

    def get_is_deposited(self):
        if self.amount == self.get_amount_deposit():
            deposit = "Yes"
        else:
            deposit = "No"
        return deposit
    
    def get_balance(self, currency=False):
        if currency:
            return format_to_str_php(self.document.get('balance'))
        return convert_decimal128_to_decimal(self.document.get('balance'))

    def get_amount(self, currency=False):
        if currency:
            return format_to_str_php(self.document.get('amount'))
        return convert_decimal128_to_decimal(self.document.get('amount'))

    def get_amount_deposit(self):
        return convert_decimal128_to_decimal(self.document.get('amount_deposit'))
    
    def get_payment_status(self):
        if self.get_balance() <= 0.00:
            return 'PAID'
        return 'NOT PAID'
    
    def get_full_name(self, reverse=False):
        if reverse:
            if self.mname:
                return self.fname + " " + self.mname + " " + self.lname
            else:
                return self.fname + " " + self.lname
        else:
            if self.mname:
                return self.lname + " " + self.mname + " " + self.fname
            else:
                return self.lname + " " + self.fname
            

    def get_reviewers(self):
        reviewers: list = []
        if self.reviewers.get('reading', False):
            reviewers.append("Reading")
        if self.reviewers.get('listening', False):
            reviewers.append("Listening")
        if len(reviewers) == 0:
            return "None"
        return ','.join(reviewers)

    def get_batch_no(self):
        # TODO: change to object class
        if 'batch_no' not in self.document:
            return ''
        if len(self.document['batch_no']) == 0:
            return ''
        return self.document['batch_no'][0]['number']

    def get_branch_name(self):
        # TODO: change to object class
        if 'branch' not in self.document:
            return ''
        if len(self.document['branch']) == 0:
            return ''
        return self.document['branch'][0]['name']
        
    def get_contact_person_name(self):
        # TODO: change to object class
        if 'contact_person' not in self.document:
            return ''
        if len(self.document['contact_person']) == 0:
            return ''
        return self.document['contact_person'][0]['fname'] + " " + self.document['contact_person'][0]['fname']
              