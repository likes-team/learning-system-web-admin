import decimal
from bson import ObjectId
from bson.decimal128 import Decimal128, create_decimal128_context
from flask_login import current_user
from app import mongo
from app.auth.models import User
from prime_admin.globals import get_date_now
from prime_admin.models import Registration



D128_CTX = create_decimal128_context()


class Earning:
    @staticmethod
    def request_for_claim(payment_id: str):
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.lms_registration_payments.update_one(
                    {"_id": ObjectId(payment_id)},
                    {"$set": {
                        "status": "for_approval"
                    }}, session=session)

                mongo.db.auth_users.update_one(
                    {"_id": current_user.id,
                    "earnings.payment_id": payment_id
                    },
                    {"$set": {
                        "earnings.$.payment_id": ObjectId(payment_id),
                        "earnings.$.status": "for_approval"
                    }}, session=session)

                mongo.db.auth_users.update_one(
                    {"_id": current_user.id,
                    "earnings.payment_id": ObjectId(payment_id)
                    },
                    {"$set": {
                        "earnings.$.payment_id": ObjectId(payment_id),
                        "earnings.$.status": "for_approval"
                    }}, session=session)

                mongo.db.auth_users.update_one(
                    {"_id": current_user.id,
                    "earnings.payment": ObjectId(payment_id)
                    },
                    {"$set": {
                        "earnings.$.payment_id": ObjectId(payment_id),
                        "earnings.$.status": "for_approval"
                    }}, session=session)
                
                current_user_details =  mongo.db.auth_users.find_one({"_id": current_user.id})

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": current_user_details['fname'] + "- Request for claim",
                    "from_module": "Earnings"
                }, session=session)

    
    @staticmethod
    def approve_marketer_requests(marketer_id, branch_id):
        marketer: User = User.objects.get(id=marketer_id)
        
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                with decimal.localcontext(D128_CTX):
                    for earning in marketer.earnings:
                        if earning.payment_mode == "profit_sharing":
                            continue

                        if earning.status == "for_approval":
                            student: Registration = Registration.objects.get(id=earning.client.id)
                            
                            if str(student.branch.id) != branch_id:
                                continue
                            
                            mongo.db.lms_registration_payments.update_one(
                            {"_id": ObjectId(earning.payment_id)},
                            {"$set": {
                                "status": "approved"
                            }}, session=session)

                            mongo.db.auth_users.update_one(
                                {"_id": marketer.id,
                                "earnings.payment_id": earning.payment_id
                                },
                                {"$set": {
                                    "earnings.$.status": "approved"
                                }}, session=session)

                            mongo.db.auth_users.update_one(
                                {"_id": marketer.id,
                                "earnings.payment_id": ObjectId(earning.payment_id)
                                },
                                {"$set": {
                                    "earnings.$.status": "approved"
                                }}, session=session)

                            mongo.db.auth_users.update_one(
                                {"_id": marketer.id,
                                "earnings.payment": ObjectId(earning.payment_id)
                                },
                                {"$set": {
                                    "earnings.$.status": "approved"
                                }}, session=session)

                            mongo.db.lms_system_transactions.insert_one({
                                "_id": ObjectId(),
                                "date": get_date_now(),
                                "current_user": current_user.id,
                                "description": "Approve claim -" + marketer.fname,
                                "from_module": "Earnings"
                            }, session=session)
