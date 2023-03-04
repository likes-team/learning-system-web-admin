import decimal
from bson import ObjectId
from bson.decimal128 import Decimal128
from flask_login import current_user
from app import mongo
from prime_admin.utils.date import get_utc_date_now



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
    def is_student_supply_available(branch=None, description=None, value=None, supply_id=None):
        if supply_id:
            query = mongo.db.lms_student_supplies.find_one({'_id': ObjectId(supply_id)})
        else:
            query = mongo.db.lms_student_supplies.find_one({'branch': ObjectId(branch), 'description': student_supply_descriptions[description]})

        if query is None:
            return False

        remaining = query.get('remaining', 0)
        if remaining >= value:
            return True
        return False


    @staticmethod
    def inbound_student_supply(supply_id, quantity, brand=None, price=0):
        total_amount_due = decimal.Decimal(price) * int(quantity)
        
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.lms_student_supplies.update_one(
                    {'_id': ObjectId(supply_id)},
                    {"$inc": {
                        'reserve':  quantity
                    }},
                    session=session
                )
                mongo.db.lms_student_supplies_transactions.insert_one({
                    'type': 'inbound',
                    'supply_id': ObjectId(supply_id),
                    'date': get_utc_date_now(),
                    'brand': brand,
                    'price': Decimal128(price),
                    'quantity': quantity,
                    'total_amount': Decimal128(total_amount_due),
                    'confirm_by': current_user.id,
                }, session=session)


    @staticmethod
    def minus_stocks(branch=None, description=None, quantity=None, session=None, supply_id=None):
        _filter = None
        if supply_id:
            _filter = {'_id': ObjectId(supply_id)}
        else:
            _filter = {
                'description': student_supply_descriptions[description],
                'branch': ObjectId(branch),
            }
            
        supply = mongo.db.lms_student_supplies.find_one(_filter)
        old_replacement = supply.get('replacement', 0)
        if old_replacement == 0:
            new_replacement = 0
        else:
            new_replacement = int(old_replacement - int(quantity))

        if new_replacement < 0:
            new_replacement = 0

        mongo.db.lms_student_supplies.update_one(_filter,
        {'$set': {
            'replacement': new_replacement
        },
        '$inc': {
            'remaining': 0 - quantity,
            'released': quantity
        }}, session=session)
        
        mongo.db.lms_student_supplies_transactions.insert_one({
            'type': 'outbound',
            'supply_id': ObjectId(supply['_id']),
            'date': get_utc_date_now(),
            'quantity': quantity,
            'remarks': '',
            'withdraw_by': 'Registration',
            'confirm_by': current_user.id
        }, session=session)


    @staticmethod
    def inbound_office_supply(description, branch, qty, unit_price, session=None):
        supply = mongo.db.lms_office_supplies.find_one({
            'description': description,
            'branch': ObjectId(branch),
        })
        old_replacement = supply.get('replacement', 0)
        if old_replacement == 0:
            new_replacement = 0
        else:
            new_replacement = int(old_replacement - int(qty))

        if new_replacement < 0:
            new_replacement = 0
            
        # increment remaining materials value
        mongo.db.lms_office_supplies.update_one({
            'description': description,
            'branch': ObjectId(branch),
        }, {
            '$inc': {'remaining': int(qty)},
            '$set': {'price': Decimal128(unit_price), 'replacement': new_replacement}
        },session=session)
        
        mongo.db.lms_office_supplies_transactions.insert_one({
            'type': 'inbound',
            'supply_id': ObjectId(supply['_id']),
            'date': get_utc_date_now(),
            'quantity': int(qty),
            'remarks': 'from expenses',
            'withdraw_by': current_user.id,
            'confirm_by': current_user.id
        }, session=session)

    @staticmethod
    def outbound_office_supply(supply_id,  quantity, session=None):
        supply = mongo.db.lms_office_supplies.find_one({
            '_id': ObjectId(supply_id),
        })

        old_replacement = supply.get('replacement', 0)
        if old_replacement == 0:
            new_replacement = 0
        else:
            new_replacement = int(old_replacement - int(quantity))

        if new_replacement < 0:
            new_replacement = 0

        mongo.db.lms_office_supplies.update_one({
            '_id': ObjectId(supply['_id']),
        },
        {'$set': {
            'replacement': new_replacement
        },
        '$inc': {
            'remaining': 0 - quantity,
            'released': quantity
        }}, session=session)
        
        mongo.db.lms_office_supplies_transactions.insert_one({
            'type': 'outbound',
            'supply_id': ObjectId(supply['_id']),
            'date': get_utc_date_now(),
            'quantity': quantity,
            'remarks': '',
            'withdraw_by': current_user.id,
            'confirm_by': current_user.id
        }, session=session)


    @staticmethod
    def find_supply_transactions(supply_id, action_type, from_what):
        if from_what == 'student_supplies':
            table = mongo.db.lms_student_supplies_transactions
        elif from_what == 'office_supplies':
            table = mongo.db.lms_office_supplies_transactions
        else:
            raise("Inception Error: invalid from_what value")

        query = list(table.find({
            'supply_id': ObjectId(supply_id),
            'type': action_type
        }))
        data = []
        for document in query:
            # TODO: Convert to class object
            data.append(document)
        return data
    
    
    @staticmethod
    def deposit_stocks(supply_id):
        query = mongo.db.lms_student_supplies.find_one({'_id': ObjectId(supply_id)})
        reserve = query.get('reserve', 0)
        if reserve == 0:
            raise ValueError("0 reserve stocks!")
        
        remaining = query.get('remaining', 0)
        new_remaining = int(reserve + remaining)
        
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.lms_student_supplies_deposits.insert_one({
                    'supply_id': ObjectId(supply_id),
                    'previous_reserve': reserve,
                    'new_reserve': 0,
                    'previous_remaining': remaining,
                    'new_remaining': new_remaining,
                    'date': get_utc_date_now(),
                })
                
                mongo.db.lms_student_supplies.update_one({
                        '_id': ObjectId(supply_id)
                    },
                    {"$set": {
                       'reserve': 0
                    },
                    "$inc": {
                        'remaining': reserve
                    }}, session=session
                )
                
        
    @staticmethod
    def supply_total_used(supply_id=None, from_what=None, year=None, month=None):
        if from_what == 'student_supplies':
            table = mongo.db.lms_student_supplies_transactions
        elif from_what == 'office_supplies':
            table = mongo.db.lms_office_supplies_transactions
        else:
            raise("Inception Error: invalid from_what value")

        _filter = {
            'supply_id': ObjectId(supply_id),
            'type': 'outbound'
        }
        
        if year != 'all':
            _filter['year'] = int(year)
        if month != 'all':
            _filter['month'] = int(month)

        query = list(table.aggregate([
            {'$project': {
                'type': 1,
                'supply_id': 1,
                'quantity': 1,
                'month': {
                    '$month': '$date'
                },
                'year': {
                    '$year': '$date'
                }
            }},
            {'$match': _filter},
            {'$group': {
                '_id': None,
                'total': {
                    '$sum': '$quantity'
                }
            }},
        ]))
        
        if len(query) == 0:
            return 0
        else:
            return query[0]['total']
        