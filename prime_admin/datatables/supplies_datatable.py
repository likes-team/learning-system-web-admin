import decimal
import pymongo
from bson import ObjectId, Decimal128
from flask import request, jsonify
from flask_cors import cross_origin
from app import mongo
from prime_admin import bp_lms
from prime_admin.globals import D128_CTX
from prime_admin.utils.date import convert_utc_to_local, format_utc_to_local
from prime_admin.services.inventory import InventoryService



@bp_lms.route('/datatables/supplies/monthly-transactions')
@cross_origin()
def dt_monthly_transactions():
    draw = request.args.get('draw')
    filter_year = request.args.get('year', 'all')
    filter_month = request.args.get('month', 'all')
    supplies_type = request.args.get('supplies_type')
    branch_id = request.args.get('branch')
    
    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
        }
        return jsonify(response)

    total_records: int
    filtered_records: int
        
    _filter = {'branch': ObjectId(branch_id)}
    
    mongo_table = None
    if supplies_type == "office_supplies":
        mongo_table =  mongo.db.lms_office_supplies
    elif supplies_type == "student_supplies":
        mongo_table =  mongo.db.lms_student_supplies

    query = mongo_table.find(_filter)
    
    fund_request_total = 0
    table_data = []
    for supply in query:
        one, two, three, four, five = 0, 0, 0, 0, 0
        six, seven, eight, nine, ten = 0, 0, 0, 0, 0
        eleven, twelve, thirteen, fourteen, fifteen = 0, 0, 0, 0, 0
        sixteen, seventeen, eighteen, nineteen, twenty = 0, 0, 0, 0, 0
        tone, ttwo, tthree, tfour, tfive = 0, 0, 0, 0, 0
        tsix,tseven,teight, tnine, thirty = 0, 0, 0, 0, 0
        thone = 0
        total_used = 0
        
        transactions = InventoryService.find_supply_transactions(supply['_id'], 'outbound', supplies_type)
        for trans in transactions:
            date = trans.get('date', None)
            local_date = convert_utc_to_local(date)
            if local_date is None:
                continue
            
            year = local_date.year
            month = local_date.month

            if filter_year != "all":
                if year != int(filter_year):
                    continue
                
            if filter_month != "all":
                if month != int(filter_month):
                    continue
            
            quantity = trans.get('quantity', 0)
            if local_date.day == 1:
                one += quantity
            elif local_date.day == 2:
                two += quantity
            elif local_date.day == 3:
                three += quantity
            elif local_date.day == 4:
                four += quantity
            elif local_date.day == 5:
                five += quantity
            elif local_date.day == 6:
                six += quantity
            elif local_date.day == 7:
                seven += quantity
            elif local_date.day == 8:
                eight += quantity
            elif local_date.day == 9:
                nine += quantity
            elif local_date.day == 10:
                ten += quantity
            elif local_date.day == 11:
                eleven += quantity
            if local_date.day == 12:
                twelve += quantity
            elif local_date.day == 13:
                thirteen += quantity
            if local_date.day == 14:
                fourteen += quantity
            elif local_date.day == 15:
                fifteen += quantity
            if local_date.day == 16:
                sixteen += quantity
            elif local_date.day == 17:
                seventeen += quantity
            if local_date.day == 18:
                eighteen += quantity
            elif local_date.day == 19:
                nineteen += quantity
            if local_date.day == 20:
                twenty += quantity
            elif local_date.day == 21:
                tone += quantity
            if local_date.day == 22:
                ttwo += quantity
            elif local_date.day == 23:
                tthree += quantity
            if local_date.day == 24:
                tfour += quantity
            elif local_date.day == 25:
                tfive += quantity
            elif local_date.day == 26:
                tsix += quantity
            elif local_date.day == 27:
                tseven += quantity
            elif local_date.day == 28:
                teight += quantity
            elif local_date.day == 29:
                tnine += quantity
            elif local_date.day == 30:
                thirty += quantity
            elif local_date.day == 31:
                thone += quantity
            total_used += quantity
            
        fund_request_total += total_used
        
        if supplies_type == "office_supplies":
            row = [
                str(supply['_id']),
                supply['description'],
                supply.get('maintaining', ''),
                supply.get('remaining', ''),
                supply.get('uom', ''),
                one,two,three,four,five,six,seven,eight,nine,ten,eleven,twelve,thirteen,fourteen,fifteen,sixteen,seventeen,
                eighteen,nineteen,twenty,tone,ttwo,tthree,tfour,tfive,tsix,tseven,teight,tnine,thirty,thone,
                total_used
            ]
        elif supplies_type == "student_supplies":
            row = [
                str(supply['_id']),
                supply['description'],
                supply.get('completing', ''),
                supply.get('maintaining', ''),
                supply.get('uom', ''),
                one,two,three,four,five,six,seven,eight,nine,ten,eleven,twelve,thirteen,fourteen,fifteen,sixteen,seventeen,
                eighteen,nineteen,twenty,tone,ttwo,tthree,tfour,tfive,tsix,tseven,teight,tnine,thirty,thone,
                total_used
            ]
        
        # Replace zeros to empty string
        i = 0
        for x in row:
            if x == 0:
                row[i] = ''
            i += 1

        table_data.append(row)
        
    total_records = mongo_table.find(_filter).count()
    filtered_records = query.count()

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
        'fundRequestTotal': fund_request_total
    }

    return jsonify(response)


@bp_lms.route('/datatables/supplies/summary')
@cross_origin()
def dt_summary():
    draw = request.args.get('draw')
    filter_year = request.args.get('year', 'all')
    filter_month = request.args.get('month', 'all')
    supplies_type = request.args.get('supplies_type')
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
        }
        return jsonify(response)
        
    total_records: int
    filtered_records: int

    _filter = {'branch': ObjectId(branch_id)}
    
    mongo_table = None
    if supplies_type == "office_supplies":
        mongo_table =  mongo.db.lms_office_supplies
    elif supplies_type == "student_supplies":
        mongo_table =  mongo.db.lms_student_supplies
    query = mongo_table.find(_filter)

    table_data = []
    
    with decimal.localcontext(D128_CTX):
        for supply in query:
            one, two, three, four, five = 0, 0, 0, 0, 0
            six, seven, eight, nine, ten = 0, 0, 0, 0, 0
            eleven, twelve, thirteen, fourteen, fifteen = 0, 0, 0, 0, 0
            sixteen, seventeen, eighteen, nineteen, twenty = 0, 0, 0, 0, 0
            tone, ttwo, tthree, tfour, tfive = 0, 0, 0, 0, 0
            tsix,tseven,teight, tnine, thirty = 0, 0, 0, 0, 0
            thone = 0
            total_used = 0
            
            transactions = InventoryService.find_supply_transactions(supply['_id'], 'inbound', supplies_type)
            for trans in transactions:
                local_date = convert_utc_to_local(trans.get('date', None))
                if local_date is None:
                    continue
                
                year = local_date.year
                month = local_date.month
         
                if filter_year != "all":
                    if year != int(filter_year):
                        continue
                    
                if filter_month != "all":
                    if month != int(filter_month):
                        continue

                quantity = trans.get('quantity', 0)
                if local_date.day == 1:
                    one += quantity
                elif local_date.day == 2:
                    two += quantity
                elif local_date.day == 3:
                    three += quantity
                elif local_date.day == 4:
                    four += quantity
                elif local_date.day == 5:
                    five += quantity
                elif local_date.day == 6:
                    six += quantity
                elif local_date.day == 7:
                    seven += quantity
                elif local_date.day == 8:
                    eight += quantity
                elif local_date.day == 9:
                    nine += quantity
                elif local_date.day == 10:
                    ten += quantity
                elif local_date.day == 11:
                    eleven += quantity
                if local_date.day == 12:
                    twelve += quantity
                elif local_date.day == 13:
                    thirteen += quantity
                if local_date.day == 14:
                    fourteen += quantity
                elif local_date.day == 15:
                    fifteen += quantity
                if local_date.day == 16:
                    sixteen += quantity
                elif local_date.day == 17:
                    seventeen += quantity
                if local_date.day == 18:
                    eighteen += quantity
                elif local_date.day == 19:
                    nineteen += quantity
                if local_date.day == 20:
                    twenty += quantity
                elif local_date.day == 21:
                    tone += quantity
                if local_date.day == 22:
                    ttwo += quantity
                elif local_date.day == 23:
                    tthree += quantity
                if local_date.day == 24:
                    tfour += quantity
                elif local_date.day == 25:
                    tfive += quantity
                elif local_date.day == 26:
                    tsix += quantity
                elif local_date.day == 27:
                    tseven += quantity
                elif local_date.day == 28:
                    teight += quantity
                elif local_date.day == 29:
                    tnine += quantity
                elif local_date.day == 30:
                    thirty += quantity
                elif local_date.day == 31:
                    thone += quantity
                total_used += quantity
                        
            if supplies_type == "office_supplies":
                unit_price = Decimal128(str(supply.get('price', 0)))
                replacement = InventoryService.supply_total_used(
                    supply_id=supply['_id'],
                    from_what=supplies_type,
                    year=filter_year,
                    month=filter_month
                )
                total_price = replacement * unit_price.to_decimal()
                row = [
                    str(supply['_id']),
                    supply['description'],
                    supply.get('remaining', ''),
                    replacement,
                    str(unit_price),
                    str(total_price)
                ]
            elif supplies_type == "student_supplies":
                row = [
                    str(supply['_id']),
                    '',
                    supply['description'],
                    one,two,three,four,five,six,seven,eight,nine,ten,eleven,twelve,thirteen,fourteen,fifteen,sixteen,seventeen,
                    eighteen,nineteen,twenty,tone,ttwo,tthree,tfour,tfive,tsix,tseven,teight,tnine,thirty,thone,
                    supply.get('reserve', ''),
                    '',
                    supply.get('remaining', ''),
                    supply.get('replacement', ''),
                ]
                
            # Replace zeros to empty string
            i = 0
            for x in row:
                if x == 0:
                    row[i] = ''
                i += 1
            table_data.append(row)
        
    total_records = mongo_table.find(_filter).count()
    filtered_records = query.count()

    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data,
    }
    return jsonify(response)


@bp_lms.route('datatables/supplies/deposit-transactions', methods=['GET'])
def dt_deposit_transactions():
    draw = request.args.get('draw')
    start, length = int(request.args['start']), int(request.args['length'])
    filter_year = request.args.get('year', 'all')
    filter_month = request.args.get('month', 'all')
    branch_id = request.args.get('branch')

    if branch_id == 'all':
        response = {
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
        }
        return jsonify(response)
    
    _filter = {'supply.branch': ObjectId(branch_id)}
    
    if filter_year != 'all':
        _filter['year'] = int(filter_year)
    if filter_month != 'all':
        _filter['month'] = int(filter_month)
    
    aggregate_query = [
        {
            '$lookup': {
                'from': 'lms_student_supplies',
                'localField': 'supply_id',
                'foreignField': '_id',
                'as': 'supply'
            }
        },
        {
            '$unwind': {
                'path': '$supply'
            }
        },
        {
            '$project': {
                'supply': 1,
                'date': 1,
                'previous_reserve': 1,
                'month': {
                    '$month': '$date'
                },
                'year': {
                    '$year': '$date'
                }
            }
        }, {
            '$match': _filter
        }, {
            '$sort': {'date': pymongo.DESCENDING}
        }
    ]

    total_records = len(list(mongo.db.lms_student_supplies_deposits.aggregate(aggregate_query)))
    
    aggregate_query.append({'$skip': start})
    aggregate_query.append({'$limit': length})
    query = list(mongo.db.lms_student_supplies_deposits.aggregate(aggregate_query))

    table_data = []
    for document in query:
        table_data.append([
            format_utc_to_local(document.get('date')),
            document['supply']['description'],
            document['previous_reserve']
        ])
    
    filtered_records = len(query)
    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': table_data,
    }
    return jsonify(response)
