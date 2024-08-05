from bson import ObjectId
from flask_login import current_user
from app import mongo
from app.auth.models import User
from prime_admin.globals import get_date_now
from prime_admin.services.payment import PaymentService
from prime_admin.helpers.query_filter import PaymentQueryFilter
from prime_admin.models_v2 import PaymentV2



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
                
                current_user_details =  mongo.db.auth_users.find_one({"_id": current_user.id})
                payment_details = mongo.db.lms_registration_payments.find_one({"_id": ObjectId(payment_id)})
                branch = ObjectId(payment_details['branch']) if payment_details.get('branch') is not None else None 

                mongo.db.lms_system_transactions.insert_one({
                    "_id": ObjectId(),
                    "date": get_date_now(),
                    "current_user": current_user.id,
                    "description": current_user_details['fname'] + "- Request for claim",
                    "from_module": "Earnings",
                    "branch": branch
                }, session=session)

    
    @staticmethod
    def approve_marketer_requests(marketer_id, branch_id):
        marketer: User = User.objects.get(id=marketer_id)
        service = PaymentService.find_payments(
            PaymentQueryFilter(contact_person=marketer_id,branch=branch_id, status="for_approval")
        )
        payments = service.get_data()
        
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                for payment in payments:
                    payment: PaymentV2
                    mongo.db.lms_registration_payments.update_one(
                        {"_id": ObjectId(payment.get_id())},
                        {"$set": {
                            "status": "approved",
                            'is_expenses': False
                        }}, session=session)
                    
                    mongo.db.lms_system_transactions.insert_one({
                        "_id": ObjectId(),
                        "date": get_date_now(),
                        "current_user": current_user.id,
                        "description": "Approve claim -" + marketer.fname,
                        "from_module": "Earnings",
                        "branch": ObjectId(branch_id)
                    }, session=session)
