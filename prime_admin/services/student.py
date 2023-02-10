import pymongo
from app import mongo
from prime_admin.models import Student
from prime_admin.helpers.query_filter import StudentQueryFilter



class StudentService:
    def __init__(self, data, **kwargs):
        self.data = data
        self.query_filter = kwargs.get('query_filter')


    @classmethod
    def find_students(cls, query_filter: StudentQueryFilter):
        query = list(mongo.db.lms_registrations.aggregate([
            {'$match': query_filter.get_filter()},
            {"$lookup": {
                'from': 'lms_batches',
                'localField': 'batch_number',
                'foreignField': '_id',
                'as': 'batch_no'
            }},
            {"$lookup": {
                'from': 'lms_branches',
                'localField': 'branch',
                'foreignField': '_id',
                'as': 'branch'
            }},
            {"$lookup": {
                'from': 'auth_users',
                'localField': 'contact_person',
                'foreignField': '_id',
                'as': 'contact_person'
            }},
            {'$sort': {
                'registration_date': pymongo.DESCENDING
            }},
            {'$skip': query_filter.get_start()},
            {'$limit': query_filter.get_length()}
        ]))
        data = []
        for row in query:
            data.append(Student(row))
        return cls(data, query_filter=query_filter)

    
    def get_data(self):
        return self.data


    def total_count(self):
        return mongo.db.lms_registrations.find().count()
    
    
    def total_filtered(self):
        return mongo.db.lms_registrations.find(self.query_filter.get_filter()).count()