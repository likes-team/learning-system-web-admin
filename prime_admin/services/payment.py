import pymongo
from app import mongo
from prime_admin.helpers.query_filter import PaymentQueryFilter
from prime_admin.models_v2 import PaymentV2


payment_aggregate_query = [
    {'$lookup': {
        'from': 'lms_registrations',
        'localField': 'payment_by',
        'foreignField': '_id',
        'as': 'student'
    }},
    {'$lookup': {
        'from': 'lms_branches',
        'localField': 'branch',
        'foreignField': '_id',
        'as': 'branch'
    }},
    {'$unwind': {
        'path': '$student'
    }},
    {'$unwind': {
        'path': '$branch'
    }},
    {"$lookup": {
        'from': 'lms_batches',
        'localField': 'student.batch_number',
        'foreignField': '_id',
        'as': 'batch_no'
    }},
    {'$unwind': {
        'path': '$batch_no'
    }},
    {'$match': None},
    {'$sort': {
        'student.registration_date': pymongo.DESCENDING
    }}
]

def _aggregation_query(query_filter):
    clone_query = payment_aggregate_query.copy()
    
    for stage in clone_query:
        stage: dict
        stage.update((key, query_filter.get_filter()) for key, _ in stage.items() if key == '$match')
    return clone_query
        

class PaymentService:
    def __init__(self, data, **kwargs):
        self.data = data
        self.query_filter = kwargs.get('query_filter')

    
    @classmethod
    def find_payments(cls, query_filter: PaymentQueryFilter):
        aggregate_query = _aggregation_query(query_filter)
        print("aggregate_query:::", aggregate_query)
        if query_filter.get_start():
            aggregate_query.append({'$skip': query_filter.get_start()})

        if query_filter.get_length():
            aggregate_query.append({'$limit': query_filter.get_length()})

        query = list(mongo.db.lms_registration_payments.aggregate(
            aggregate_query
        ))
        data = []
        
        for document in query:
            data.append(PaymentV2(document))
        return cls(data, query_filter=query_filter)


    def get_data(self):
        return self.data
    
    def total_filtered(self):
        aggregate_query = _aggregation_query(self.query_filter)
        aggregate_query.append({'$count': 'total_filtered'})
        
        query = list(mongo.db.lms_registration_payments.aggregate(aggregate_query))
        if len(query) > 0:
            return query[0]['total_filtered']
        else:
            return 0
