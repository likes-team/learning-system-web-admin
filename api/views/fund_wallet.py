import decimal
from bson import ObjectId, Decimal128
from flask import jsonify
from app import mongo
from api import bp_api
from prime_admin.globals import D128_CTX, get_date_now
from prime_admin.services.fund_wallet import add_fund, add_expenses


@bp_api.route('/fund-wallet-transactions/<string:transaction_id>', methods=['DELETE'])
def fund_wallet_transaction_delete(transaction_id):
    """Deletes a fund wallet transaction
    then add new adjustment transaction
    """

    document = mongo.db.lms_fund_wallet_transactions.find_one(
        {'_id': ObjectId(transaction_id)}
    )
    transaction_type = document['type']

    if transaction_type not in ['add_fund', 'expenses']:
        return jsonify({
            'status': 'error',
            'message': "Wrong transaction's type"
        })

    branch_id = str(document['branch'])

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            mongo.db.lms_fund_wallet_transactions.update_one(
                {'_id': ObjectId(transaction_id)},
                {'$set': {
                    'is_deleted': True,
                    'remarks': f"System Deleted, ID: {transaction_id}"
                }},
                session=session
            )
            
            remarks = f"System adjustment, ref: {transaction_id}"
            if transaction_type == "add_fund":
                add_expenses(
                    branch_id=branch_id,
                    total_amount_due=str(document['amount_received']),
                    category="SYSTEM_ADJUSTMENT",
                    description="System adjustment",
                    remarks=remarks
                )
            elif transaction_type == "expenses":
                add_fund(
                    branch_id=branch_id,
                    amount_received=str(document['total_amount_due']),
                    remarks=remarks,
                    session=session
                )
    return jsonify({
        'status': 'success',
        'message': "Deleted Successfully!"
    })
