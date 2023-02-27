import pymongo
from app import mongo
from prime_admin.models import Student, Registration
from prime_admin.helpers.query_filter import StudentQueryFilter
from prime_admin.services.inventory import InventoryService


class StudentService:
    def __init__(self, data, **kwargs):
        self.data = data
        self.query_filter = kwargs.get('query_filter')

    @classmethod
    def find_student(cls, oid):
        client = Registration.objects.get_or_404(id=oid)
        return cls(client)

    @classmethod
    def find_students(cls, query_filter: StudentQueryFilter):
        aggregate_query = [
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
            {'$sort': query_filter.get_sort()}
        ]

        if query_filter.get_start():
            aggregate_query.append({'$skip': query_filter.get_start()})

        if query_filter.get_length():
            aggregate_query.append({'$limit': query_filter.get_length()})

        query = list(mongo.db.lms_registrations.aggregate(aggregate_query))
        data = []

        for row in query:
            data.append(Student(row))
        return cls(data, query_filter=query_filter)

    
    def get_data(self):
        return self.data
    
    def get_student(self):
        if not isinstance(self.data, Registration):
            return None
        return self.data

    def total_count(self):
        return mongo.db.lms_registrations.find().count()
    
    
    def total_filtered(self):
        return mongo.db.lms_registrations.find(self.query_filter.get_filter()).count()

    def process_supplies(self, session):
        if self.data.books['volume1']:
            InventoryService.minus_stocks(branch=self.data.branch.id, description='volume1', quantity=1, session=session)

        if self.data.books['volume2']:
            InventoryService.minus_stocks(branch=self.data.branch.id, description='volume2', quantity=1, session=session)

        if not self.data.uniforms['uniform_none']:
            InventoryService.minus_stocks(branch=self.data.branch.id, description='uniform', quantity=1, session=session)
         
        if self.data.id_materials['id_card']:
            InventoryService.minus_stocks(branch=self.data.branch.id, description='id_card', quantity=1, session=session)
       
        if self.data.id_materials['id_lace']:
            InventoryService.minus_stocks(branch=self.data.branch.id, description='id_lace', quantity=1, session=session)
      
        if self.data.reviewers['reading']:
            InventoryService.minus_stocks(branch=self.data.branch.id, description='reading', quantity=1, session=session)
     
        if self.data.reviewers['listening']:
            InventoryService.minus_stocks(branch=self.data.branch.id, description='listening', quantity=1, session=session)

    # def new_payment(self):
        