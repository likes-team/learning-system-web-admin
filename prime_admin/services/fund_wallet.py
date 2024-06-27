from bson import ObjectId
import decimal
from bson import Decimal128
from flask_login import current_user
from flask import jsonify
from app import mongo
from prime_admin.utils.date import convert_date_input_to_utc
from prime_admin.utils.currency import format_to_str_php, convert_decimal128_to_decimal
from prime_admin.globals import D128_CTX, get_date_now


class BusinessExpensesService:
    def __init__(self, branch='all', year='all'):
        self.grand_total = None
        self.table = None
        match = {'type': 'expenses'}

        if branch == 'all':
            if current_user.role.name == "Admin":
                pass
            elif current_user.role.name == "Manager":
                match['branch'] = {"$in": current_user.branches}
            elif current_user.role.name == "Partner":
                match['branch'] = {"$in": current_user.branches}
            elif current_user.role.name == "Secretary":
                match['branch'] = current_user.branch.id
        else:
            if current_user.role.name == "Admin":
                match['branch'] = ObjectId(branch)
            elif current_user.role.name == "Manager":
                match['branch'] = ObjectId(branch)
            elif current_user.role.name == "Partner":
                match['branch'] = ObjectId(branch)
            elif current_user.role.name == "Secretary":
                match['branch'] = current_user.branch.id

        if year != "all":
            match['date'] = {
                "$gte": convert_date_input_to_utc(f'{year}-01-01', 'date_from'),
                "$lte": convert_date_input_to_utc(f'{year}-12-31', 'date_to'),
            }
        self.match = match
        
        initial = ['' for _ in range(13)]
        
        self.data = {
            'utilities': initial.copy(),
            'office_supply': initial.copy(),
            'salary': initial.copy(),
            'rebates': initial.copy(),
            'refund': initial.copy(),
            'bookeeper': initial.copy(),
            'other_expenses': initial.copy(),
            'BIR': initial.copy(),
            'Business Permit': initial.copy(),
            'Employee Benefits': initial.copy(), # Deprecated
            'Bookeeper Retainer Fee': initial.copy(), # Deprecated
            'Bookeeper': initial.copy(),
            'SNPL Fee': initial.copy(),
            'total': initial.copy(),
        }
        self.data_conversion = {
            'utilities': 'UTILITIES',
            'office_supply': 'OFFICE SUPPLIES',
            'salary': 'SALARY',
            'rebates': 'REBATES',
            'refund': 'REFUND',
            'bookeeper': 'BOOKEEPER',
            'other_expenses': 'OTHER EXPENSES',
            'BIR': 'BIR',
            'Business Permit': 'BUSINESS PERMIT',
            'Employee Benefits': 'EMPLOYEE BENEFITS', # Deprecated
            'Bookeeper Retainer Fee': 'BOOKEEPERs RETAINERS FEE', # Deprecated
            'Bookeeper': 'BOOKEEPER',
            'SNPL Fee': "SNPL FEE",
            'total': 'TOTAL OF EXPENDITURE'
        }


    def get_table(self):
        query = list(mongo.db.lms_fund_wallet_transactions.aggregate([
           {'$match': self.match},
           {'$group': {
               '_id': {'month': {'$month': {"date": "$date", "timezone": "Asia/Manila"}}, 'category': '$category'},
               'total': {'$sum': '$total_amount_due'}
           }}
        ]))
        for group in query:
            category = group['_id']['category']
            month = group['_id']['month'] - 1
            total = group['total']
            
            if category == "salary_and_rebates":
                # TODO: manual update
                continue
            if category == "Transportation":
                continue

            try:
                self.data[category][month] = total
            except KeyError:
                continue

            self._add_to_total_expenditure(month, total)
            self._add_to_total(category, total)
            
        self._compute_grand_total_expenditure()
        self._format_table()
        return self.table


    def _compute_grand_total_expenditure(self):
        total = 0
        for _, months in self.data.items():
            category_total = months[-1]
            if not isinstance(category_total, str):
                total += category_total
        self.grand_total = total
        self.data['total'][12] = total
        
        
    def _add_to_total_expenditure(self, month, total):
        total_expenditure = self.data['total'][month]
        if isinstance(total_expenditure, str):
            self.data['total'][month] = convert_decimal128_to_decimal(total)
        else:
            self.data['total'][month] += convert_decimal128_to_decimal(total)


    def _add_to_total(self, category, total):
        last_column = self.data[category][12]
        if isinstance(last_column, str):
            self.data[category][12] = convert_decimal128_to_decimal(total)
        else:
            self.data[category][12] += convert_decimal128_to_decimal(total)

    
    def _format_table(self):
        table = []
        for key, months in self.data.items():
            row = [self.data_conversion.get(key)] + [format_to_str_php(val, replacement='') for val in months]
            table.append(row)
        self.table = table


def add_fund(
    branch_id,
    amount_received,
    thru=None,
    bank_name=None,
    remittance=None,
    account_name=None,
    account_no=None,
    transaction_no=None,
    sender=None,
    receiver=None,
    remarks=None,
    session=None
):
    """Add fund transaction
    """

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
        'remarks': remarks,
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


def add_expenses(
    branch_id,
    total_amount_due,
    category=None,
    description=None,
    bank_name=None,
    remittance=None,
    account_name=None,
    account_no=None,
    sender=None,
    remarks=None,
    session=None
):
    """ Add expenses transaction
    """

    accounting = mongo.db.lms_accounting.find_one({
        "branch": ObjectId(branch_id),
    })

    if accounting:
        with decimal.localcontext(D128_CTX):
            previous_fund_wallet = accounting['total_fund_wallet'] if 'total_fund_wallet' in accounting else Decimal128('0.00')

            if decimal.Decimal(total_amount_due) > previous_fund_wallet.to_decimal():
                return jsonify({
                    'status': 'error',
                    'message': "Insufficient fund wallet balance"
                }), 400
                
            new_total_fund_wallet = previous_fund_wallet.to_decimal() - decimal.Decimal(total_amount_due)
            balance = Decimal128(previous_fund_wallet.to_decimal() - Decimal128(str(total_amount_due)).to_decimal())

            mongo.db.lms_accounting.update_one({
                "branch": ObjectId(branch_id)
            },
            {'$set': {
                "total_fund_wallet": Decimal128(new_total_fund_wallet)
            }},session=session)
    else:
        raise Exception("Likes Error: Accounting data not found")

    status = None
    reference_no = None
    employee_information = None
    billing_month_from = None
    billing_month_to = None
    qty = None
    unit_price = None
    settled_by = None
    contact_no = None
    address = None
    cut_off = None

    mongo.db.lms_fund_wallet_transactions.insert_one({
        'type': 'expenses',
        'running_balance': balance,
        'branch': ObjectId(branch_id),
        'date': get_date_now(),
        'category': category,
        'description': description,
        'bank_name': bank_name,
        'account_name': account_name,
        'account_no': account_no,
        'billing_month_from': billing_month_from,
        'billing_month_to': billing_month_to,
        'qty': qty,
        'unit_price': unit_price,
        'total_amount_due': Decimal128(total_amount_due),
        'settled_by': settled_by,
        'remittance': remittance,
        'sender': sender,
        'contact_no': contact_no,
        'address': address,
        'status': status,
        'reference_no': reference_no,
        'employee_information': employee_information,
        'cut_off': cut_off,
        'remarks': remarks,
        'created_at': get_date_now(),
        'created_by': current_user.fname + " " + current_user.lname
    },session=session)

    mongo.db.lms_system_transactions.insert_one({
        "_id": ObjectId(),
        "date": get_date_now(),
        "current_user": current_user.id,
        "description": "Add expenses - description: {}, category: {}, amount: {}".format(description, category, str(total_amount_due)),
        "from_module": "Fund Wallet"
    }, session=session)
    return True