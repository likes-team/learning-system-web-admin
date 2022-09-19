import pymongo
from flask import request, jsonify
from flask_login import current_user
from app import mongo
from prime_admin import bp_lms
from prime_admin.globals import convert_to_utc



@bp_lms.route('/datatables/supplies/monthly-transactions')
def dt_monthly_transactions():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    filter_year = request.args.get('year', 'all')
    filter_month = request.args.get('month', 'all')
    
    total_records: int
    filtered_records: int
    _filter: dict = {'type': 'supplies'}

    query =  mongo.db.lms_inventories.find(_filter).skip(start).limit(length)

    table_data = []
    
    for supply in query:
        one, two, three, four, five = '', '', '', '', ''
        six, seven, eight, nine, ten = '', '', '', '', ''
        eleven, twelve, thirteen, fourteen, fifteen = '', '', '', '', ''
        sixteen, seventeen, eighteen, nineteen, twenty = '', '', '', '', ''
        tone, ttwo, tthree, tfour, tfive = '', '', '', '', ''
        tsix,tseven,teight, tnine, thirty = '', '', '', '', ''
        thone = ''
        
        transactions = supply.get('transactions', [])
        for trans in transactions:
            date = trans.get('date', None)
            
            if date is None:
                continue
            
            year = date.year
            month = date.month

            if filter_year != "all":
                if year != int(filter_year):
                    continue
                
            if filter_month != "all":
                if month != int(filter_month):
                    continue
            
            quantity = trans.get('quantity', 0)
            if date.day == 1:
                one = quantity
            elif date.day == 2:
                two = quantity
            elif date.day == 3:
                three = quantity
            elif date.day == 4:
                four = quantity
            elif date.day == 5:
                five = quantity
            elif date.day == 6:
                six = quantity
            elif date.day == 7:
                seven = quantity
            elif date.day == 8:
                eight = quantity
            elif date.day == 9:
                nine = quantity
            elif date.day == 10:
                ten = quantity
            elif date.day == 11:
                eleven = quantity
            if date.day == 12:
                twelve = quantity
            elif date.day == 13:
                thirteen = quantity
            if date.day == 14:
                fourteen = quantity
            elif date.day == 15:
                fifteen = quantity
            if date.day == 16:
                sixteen = quantity
            elif date.day == 17:
                seventeen = quantity
            if date.day == 18:
                eighteen = quantity
            elif date.day == 19:
                nineteen = quantity
            if date.day == 20:
                twenty = quantity
            elif date.day == 21:
                tone = quantity
            if date.day == 22:
                ttwo = quantity
            elif date.day == 23:
                tthree = quantity
            if date.day == 24:
                tfour = quantity
            elif date.day == 25:
                tfive = quantity
            elif date.day == 26:
                tsix = quantity
            elif date.day == 27:
                tseven = quantity
            elif date.day == 28:
                teight = quantity
            elif date.day == 29:
                tnine = quantity
            elif date.day == 30:
                thirty = quantity
            elif date.day == 31:
                thone = quantity

        table_data.append([
            str(supply['_id']),
            supply['description'],
            # supply.get('uom', ''),
            # supply.get('qty', ''),
            # supply.get('maintaining', ''),
            one,two,three,four,five,six,seven,eight,nine,ten,eleven,twelve,thirteen,fourteen,fifteen,sixteen,seventeen,
            eighteen,nineteen,twenty,tone,ttwo,tthree,tfour,tfive,tsix,tseven,teight,tnine,thirty,thone,
            supply.get('released', ''),
            supply.get('remaining', ''),
            supply.get('total_replacement', ''),
            str(supply.get('price', '')),
            '',
        ])
        
    total_records = mongo.db.lms_inventories.find(_filter).count()
    filtered_records = query.count()

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }

    return jsonify(response)


@bp_lms.route('/datatables/supplies/summary')
def dt_summary():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    filter_year = request.args.get('year', 'all')
    filter_month = request.args.get('month', 'all')
    
    total_records: int
    filtered_records: int
    _filter: dict = {'type': 'supplies'}

    query =  mongo.db.lms_inventories.find(_filter).skip(start).limit(length)

    table_data = []
    
    for supply in query:
        transactions = supply.get('transactions', [])
        
        
        for trans in transactions:
            date = trans.get('date', None)
            
            if date is None:
                continue
            
            year = date.year
            month = date.month

            if filter_year != "all":
                if year != int(filter_year):
                    continue
                
            if filter_month != "all":
                if month != int(filter_month):
                    continue
                
        table_data.append([
            str(supply['_id']),
            supply['description'],
            supply.get('uom', ''),
            supply.get('remaining', ''),
            supply.get('maintaining', ''),
            str(supply.get('price', '')),
            '',
        ])
        
    total_records = mongo.db.lms_inventories.find(_filter).count()
    filtered_records = query.count()

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }

    return jsonify(response)