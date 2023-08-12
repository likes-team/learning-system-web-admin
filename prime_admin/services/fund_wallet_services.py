import decimal
from bson import Decimal128
from bson.objectid import ObjectId
from flask import jsonify
from flask_login import current_user
from app import mongo
from prime_admin.globals import D128_CTX, get_date_now


def add_fund(
    branch_id,
    thru,
    bank_name,
    remittance,
    account_name,
    account_no,
    transaction_no,
    amount_received,
    sender,
    receiver,
    session=None
):
    accounting = mongo.db.lms_accounting.find_one({
        "branch": ObjectId(branch_id),
    })

    if accounting:
        with decimal.localcontext(D128_CTX):
            previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')
            new_total_fund_wallet = previous_fund_wallet.to_decimal() + decimal.Decimal(amount_received)
            balance = Decimal128(Decimal128(
                str(accounting["total_fund_wallet"] if 'total_fund_wallet' in accounting else 0.00)).to_decimal() + Decimal128(str(amount_received)).to_decimal())
            
            mongo.db.lms_accounting.update_one({
                "branch": ObjectId(branch_id)
            },
            {'$set': {
                "total_fund_wallet": Decimal128(new_total_fund_wallet)
            }},session=session)
    else:
        previous_fund_wallet = Decimal128('0.00')
        new_total_fund_wallet = decimal.Decimal(amount_received)
        balance = Decimal128(str(amount_received))

        mongo.db.lms_accounting.insert_one({
            "_id": ObjectId(),
            "branch": ObjectId(branch_id),
            "active_group": 1,
            "total_gross_sale": Decimal128("0.00"),
            "final_fund1": Decimal128("0.00"),
            "final_fund2": Decimal128("0.00"),
            "total_fund_wallet": Decimal128(str(amount_received))
        }, session=session)

    mongo.db.lms_fund_wallet_transactions.insert_one({
        'type': 'add_fund',
        'thru': thru,
        'remittance': remittance,
        'account_name': account_name,
        'account_no': account_no,
        'running_balance': balance,
        'branch': ObjectId(branch_id),
        'date': get_date_now(),
        'bank_name': bank_name,
        'transaction_no': transaction_no,
        'sender': sender,
        'amount_received': Decimal128(amount_received),
        'receiver': receiver,
        'previous_total_fund_wallet': previous_fund_wallet,
        'new_total_fund_wallet': Decimal128(new_total_fund_wallet),
        'created_at': get_date_now(),
        'created_by': current_user.fname + " " + current_user.lname
    },session=session)
    
    mongo.db.lms_system_transactions.insert_one({
        "_id": ObjectId(),
        "date": get_date_now(),
        "current_user": current_user.id,
        "description": "Add fund - transaction no: {}, account no: {}, amount: {}".format(transaction_no, account_no, str(amount_received)),
        "from_module": "Fund Wallet"
    }, session=session)
    return True