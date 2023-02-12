from bson import ObjectId
from flask_login import current_user
from app import mongo
from prime_admin.utils.date import get_local_date_now



student_supply_descriptions = {
    'uniform': 'UNIFORM',
    'id_card': 'ID CARD',
    'id_lace': 'ID LACE',
    'volume1': 'BOOK 1',
    'volume2': 'BOOK 2',
    'reading': 'REVIEWER READING',
    'listening': 'REVIEWER LISTENING'
}


class InventoryService:
    @staticmethod
    def is_student_supply_available(branch, description, value):
        query = mongo.db.lms_student_supplies.find_one({'branch': ObjectId(branch), 'description': student_supply_descriptions[description]})
        if query is None:
            return False

        remaining = query.get('remaining', 0)
        if remaining >= value:
            return True
        return False


    @staticmethod
    def inbound_student_supply(supply_id, quantity, brand=None, price=None):
        pass


    @staticmethod
    def minus_stocks(branch, description, quantity, session=None):
        return mongo.db.lms_student_supplies.update_one({
            'branch': ObjectId(branch),
            'description': student_supply_descriptions[description],
        },
        {'$inc': {
            'remaining': 0 - quantity,
            'released': quantity
        },
        '$push': {
            'transactions': {
                '_id': ObjectId(),
                'quantity': quantity,
                'date': get_local_date_now(),
                'remarks': '',
                'withdraw_by': 'Registration',
                'confirm_by': current_user.id
            }
        }}, session=session)
