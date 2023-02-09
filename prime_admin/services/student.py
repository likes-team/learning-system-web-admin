from bson import ObjectId
from pymongo import DESCENDING
from flask_login import current_user
from app import mongo
from prime_admin.utils.date import convert_date_input_to_utc
from prime_admin.models import Student
from prime_admin.helpers.query_filter import StudentQueryFilter



class StudentService:
    def __init__(self, data, **kwargs):
        self.data = data


    @classmethod
    def find_students(cls, query_filter: StudentQueryFilter):
        query = list(mongo.db.lms_registrations.find(query_filter.get_filter()).sort('registration_date', DESCENDING))
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
                'registration_date': DESCENDING
            }}
        ]))

        data = []
        for row in query:
            data.append(Student(row))
        return cls(data)

    
    def get_data(self):
        return self.data


    def total_count(self):
        return mongo.db.lms_registrations.find().count()
    
    
    def total_filtered(self):
        return len(self.data)