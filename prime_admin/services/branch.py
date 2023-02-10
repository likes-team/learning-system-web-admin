from bson import ObjectId
from app import mongo



class BranchService:
    @staticmethod
    def get_name_by_id(oid):
        query = mongo.db.lms_branches.find_one({'_id': ObjectId(oid)})
        return query.get('name')