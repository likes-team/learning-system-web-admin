from bson import ObjectId
from flask_login import current_user
from prime_admin.utils.date import convert_date_input_to_utc



class StudentQueryFilter:
    def __init__(
        self, branch=None, batch_no=None, schedule=None,
        payment_status=None, payment_mode=None, session=None,
        date_from=None, date_to=None, search_value=None, start=None, length=None
    ):
        self.match = None
        self.start = start
        self.length = length
        self.branch = branch
        self.batch_no = batch_no
        self.session = session
        match = {
            'status': {'$in': ['registered', 'refunded']},
            'is_archived': {'$ne': True}
        }
        
        if branch and branch != 'all':
            match['branch'] = ObjectId(branch)
        else:
            if current_user.role.name in ["Marketer", 'Partner']:
                match['branch'] = {'$in': [ObjectId(branch) for branch in current_user.branches]}
        
        if session and session != 'all':
            match['session'] = session
        
        if batch_no and batch_no != 'all':
            match['batch_number'] = ObjectId(batch_no)
        
        if schedule and schedule != 'all':
            match['schedule'] = schedule
            
        if search_value and search_value != '':
            match['lname'] = {'$regex': search_value}
        
        if date_from and date_from != "":
            match['registration_date'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from')}
        
        if date_to and date_to != '':
            match['registration_date'] = {'$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if date_from and date_from != '' and date_to and date_to != '':
            match['date'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from'), '$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if payment_mode and payment_mode != 'all':
            match['payment_mode'] = payment_mode

        if payment_status == 'PAID':
            match['balance'] = {'$lte': 0}
        elif payment_status == 'NOT PAID':
            match['balance'] = {'$gt': 0}
        elif payment_status == 'REFUNDED':
            match['payment_mode'] = 'refund'
        self.match = match
        
        if start:
            self.start = int(start)
        if length:
            self.length = int(length)


    @classmethod
    def from_request(cls, request):
        return cls(
            search_value = request.args.get("search[value]"),
            branch = request.args.get('branch'),
            batch_no = request.args.get('batch_no'),
            schedule = request.args.get('schedule'),
            date_from = request.args.get('date_from'),
            date_to = request.args.get('date_to'),
            payment_status = request.args.get('payment_status'),
            payment_mode = request.args.get('payment_mode'),
            session = request.args.get('session'),
            start = request.args.get('start'),
            length = request.args.get('length'),
        )


    def get_filter(self):
        return self.match
    
    def get_start(self):
        return self.start
    
    def get_length(self):
        return self.length
