from app import mongo



class Payment:
    @staticmethod
    def pay_registration(payment: dict, session=None):
        """Pay Registration balance

        Args:
            payment (dict): _description_
            session (_type_, optional): _description_. Defaults to None.
        """
        if session:
            mongo.db.lms_registration_payments.insert_one(payment, session=session)
        else:
            mongo.db.lms_registration_payments.insert_one(payment)
