from bson import ObjectId
from flask_login import current_user
from app import mongo
from prime_admin.utils.currency import convert_decimal128_to_decimal, format_to_str_php



class SavingService:
    def __init__(self, **kwargs):
        self.total_approved = kwargs.get('total_approved', 0)
        self.total_for_approval = kwargs.get('total_for_approval', 0)
        self.total_nyc = kwargs.get('total_nyc', 0)


    @classmethod
    def find_savings(cls, contact_person):
        match = {}
        if contact_person != 'all':
            match['contact_person'] = ObjectId(contact_person)

        if current_user.role.name in ['Secretary']:
            match['branch'] = current_user.branch.id
        elif current_user.role.name in ['Partner', 'Manager']:
            match['branch'] = {'$in': [ObjectId(branch) for branch in current_user.branches]}

        aggregate_query = list(mongo.db.lms_registration_payments.aggregate([
            {'$match': match},
            {'$group': {
                '_id': {"status": "$status"},
                'total': {'$sum': '$savings'}
            }}
        ]))
        if len(aggregate_query) <= 0:
            return cls()
        
        total_approved = 0
        total_nyc = 0
        total_for_approval = 0
        
        for document in aggregate_query:
            status = document['_id']['status']
            if status == 'for_approval':
                total_for_approval = document.get('total')
            elif status == 'approved':
                total_approved = document.get('total')
            elif status is None:
                total_nyc = document.get('total')
        return cls(
            total_approved=total_approved,
            total_for_approval=total_for_approval,
            total_nyc=total_nyc,
        )

    
    def get_total_savings(self, currency=False):
        if currency:
            return format_to_str_php(self.total_for_approval)
        return convert_decimal128_to_decimal(self.total_for_approval)
    

    def get_total_nyc(self, currency=False):
        if currency:
            return format_to_str_php(self.total_nyc)
        return convert_decimal128_to_decimal(self.total_nyc)
        
        
    def get_total_savings_approved(self, currency=False):
        if currency:
            return format_to_str_php(self.total_approved)
        return convert_decimal128_to_decimal(self.total_approved)
