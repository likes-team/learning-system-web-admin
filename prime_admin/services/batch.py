from bson import ObjectId
from app import mongo



class BatchService:
    @staticmethod
    def get_name_by_id(oid):
        query = mongo.db.lms_batches.find_one({'_id': ObjectId(oid)})
        return query.get('number')
