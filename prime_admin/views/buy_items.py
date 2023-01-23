import decimal
from bson.objectid import ObjectId
from prime_admin.globals import get_date_now
from flask_login import login_required, current_user
from flask_cors import cross_origin
from app.admin.templating import admin_render_template
from prime_admin import bp_lms
from prime_admin.models import BuyItems, StudentSupply, Registration
from flask import redirect, url_for, request, flash, jsonify
from app import mongo
from bson.decimal128 import Decimal128



@bp_lms.route('/store/buy-items', methods=['GET', 'POST'])
@login_required
def buy_items():
    if request.method == "GET":
        _modals = [
            'lms/search_client_last_name_modal.html',
        ]

        items = StudentSupply.objects(is_for_sale=True)
        
        return admin_render_template(
            BuyItems,
            'lms/buy_items.html',
            'learning_management',
            modals=_modals,
            title="Buy Items",
            items=items,
            )
    elif request.method == "POST":
        form = request.form

        if form.get('client_id') == "":
            flash("Please select student first", 'error')
            return redirect(url_for('lms.buy_items'))

        items = []

        item_list = form.getlist('items[]')

        uniforms = 0
        id_lace = 0
        id_card = 0
        module_1 = 0
        module_2 = 0
        reviewer_l = 0
        reviewer_r = 0

        total_amount = decimal.Decimal(0.00)
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                if item_list:
                    for item_id in form.getlist('items[]'):
                        item = mongo.db.lms_student_supplies.find_one({"_id": ObjectId(item_id)})
                        qty = int(form.get("qty_{}".format(item_id)))
                        price = decimal.Decimal(form.get("price_{}".format(item_id)))
                        amount = qty * price
                        items.append({
                            "_id": ObjectId(),
                            'item': ObjectId(item_id),
                            'qty': Decimal128(str(qty)),
                            'price': Decimal128(str(price)),
                            'amount': Decimal128(str(amount))
                        })
                        
                        mongo.db.lms_student_supplies.update_one({
                            "_id": ObjectId(item_id)
                        },
                        {"$inc": {
                            "remaining": 0 - qty
                        }}, session=session)

                        if item['description'] == "UNIFORM":
                            uniforms = qty
                        elif item['description'] == "ID LACE":
                            id_lace = qty
                        elif item['description'] == "ID CARD":
                            id_card = qty
                        elif item['description'] == "MODULE 1":
                            module_1 = qty
                        elif item['description'] == "MODULE 2":
                            module_2 = qty
                        elif item['description'] == "REVIEWER L BOOKBIND":
                            reviewer_l = qty
                        elif item['description'] == "REVIEWER R":
                            reviewer_r = qty

                        total_amount += amount

                client = Registration.objects.get(id=form.get('client_id'))

                mongo.db.lms_store_buyed_items.insert_one({
                    "_id": ObjectId(),
                    "created_at": get_date_now(),
                    "cashier": current_user.id,
                    'branch': client.branch.id,
                    "client_id": client.id,
                    "items": items,
                    "total_amount": Decimal128(total_amount),
                    "uniforms": uniforms,
                    "id_lace": id_lace,
                    "id_card": id_card,
                    "module_1": module_1,
                    "module_2": module_2,
                    "reviewer_l": reviewer_l,
                    "reviewer_r": reviewer_r,
                    'deposited': "Pre Deposit"
                }, session=session)

                flash("Process successfully!", 'success')
        return redirect(url_for('lms.store_records'))


@bp_lms.route('/get-student-supplies')
def get_student_supplies():
    branch_id = request.args.get('branch')
    query = mongo.db.lms_student_supplies.find({'branch': ObjectId(branch_id)})
    result = []
    
    for supply in query:
        result.append({
            'id': str(supply['_id']),
            'description': supply['description'],
            'maintaining': supply.get('maintaining', ''),
            'price': str(supply.get('price', 0))
        })
    
    return jsonify({
        'status': 'success',
        'data': result
    }), 200
    

@bp_lms.route('/update-price', methods=['POST'])
@login_required
@cross_origin()
def update_price():
    item_id = request.json['item_id']
    new_price = Decimal128(request.json['new_price'])

    mongo.db.lms_student_supplies.update_one({'_id': ObjectId(item_id)}, {"$set": {
        'price': new_price
    }})
    
    return jsonify({
        'status': 'success'
    }), 200