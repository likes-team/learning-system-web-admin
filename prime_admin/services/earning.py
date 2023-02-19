from bson import ObjectId
from app import mongo
from prime_admin.utils.currency import convert_decimal128_to_decimal, format_to_str_php



class EarningService:
    def __init__(self, **kwargs):
        self.total_approved = kwargs.get('total_approved', 0)
        self.total_for_approval = kwargs.get('total_for_approval', 0)
        self.total_nyc = kwargs.get('total_nyc', 0)
        self.branch_total_earnings = kwargs.get('branch_total_earnings', [])
                
    
    @classmethod
    def find_earnings(cls, contact_person):
        match = {}
        if contact_person != 'all':
            match['contact_person'] = ObjectId(contact_person)
            
        aggregate_query = list(mongo.db.lms_registration_payments.aggregate([
            {'$match': match},
            {'$group': {
                '_id': {"status": "$status"},
                'total': {'$sum': '$earnings'}
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

        branch_total_earnings = cls._get_total_branch_earnings(contact_person)
        return cls(
            total_approved=total_approved,
            total_for_approval=total_for_approval,
            total_nyc=total_nyc,
            branch_total_earnings=branch_total_earnings
        )


    @staticmethod
    def _get_total_branch_earnings(contact_person):
        match = {'status': 'for_approval'}
        if contact_person != 'all':
            match['contact_person'] = ObjectId(contact_person)

        aggregate_query = list(mongo.db.lms_registration_payments.aggregate([
            {'$match': match},
            {'$lookup': {
                'from': 'lms_branches',
                'localField': 'branch',
                'foreignField': '_id',
                'as': 'branch'
            }},
            {'$unwind': {
               'path': '$branch'
            }},
            {'$group': {
                '_id': {"branch": "$branch"},
                'total': {'$sum': '$earnings'}
            }}
        ]))
        branch_total_earnings = []
        
        for document in aggregate_query:
            branch_total_earnings.append({
                'id': str(document['_id']['branch']['_id']),
                'name': document['_id']['branch']['name'],
                'totalEarnings': format_to_str_php(document['total'])
            })
        
        if contact_person == 'all':
            contact_person_branches = [str(branch['_id']) for branch in mongo.db.lms_branches.find()]
        else:
            contact_person_branches = mongo.db.auth_users.find_one({'_id': ObjectId(contact_person)}).get('branches', [])
        for other_branch_id in contact_person_branches:
            if not any(d['id'] == str(other_branch_id) for d in branch_total_earnings):
                branch = mongo.db.lms_branches.find_one({'_id': ObjectId(other_branch_id)})
                branch_total_earnings.append(
                    {
                        'id': str(branch['_id']),
                        'name': branch['name'],
                        'totalEarnings': format_to_str_php(0)
                    }
                )
        return branch_total_earnings

    
    def get_total_earnings(self, currency=False):
        if currency:
            return format_to_str_php(self.total_for_approval)
        return convert_decimal128_to_decimal(self.total_for_approval)
    

    def get_total_nyc(self, currency=False):
        if currency:
            return format_to_str_php(self.total_nyc)
        return convert_decimal128_to_decimal(self.total_nyc)
        
        
    def get_total_earnings_approved(self, currency=False):
        if currency:
            return format_to_str_php(self.total_approved)
        return convert_decimal128_to_decimal(self.total_approved)
    

    def get_branch_total_earnings(self):
        return self.branch_total_earnings
         