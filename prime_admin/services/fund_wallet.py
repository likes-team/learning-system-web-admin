from bson import ObjectId
from flask_login import current_user
from app import mongo
from prime_admin.utils.date import convert_date_input_to_utc
from prime_admin.utils.currency import format_to_str_php, convert_decimal128_to_decimal



class BusinessExpensesService:
    def __init__(self, branch='all', year='all'):
        match = {}
        
        if branch == 'all':
            if current_user.role.name == "Admin":
                match = {'type': 'expenses'}
            elif current_user.role.name == "Partner":
                match = {'type': 'expenses', 'branch': {"$in": current_user.branches}}
            elif current_user.role.name == "Secretary":
                match = {'type': 'expenses', 'branch': current_user.branch.id}
        else:
            if current_user.role.name == "Secretary":
                match = {'type': 'expenses', 'branch': current_user.branch.id}
            elif current_user.role.name == "Admin":
                match = {'type': 'expenses', 'branch': ObjectId(branch)}
            elif current_user.role.name == "Partner":
                match = {'type': 'expenses', 'branch': ObjectId(branch)}
            
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
            'Employee Benefits': initial.copy(),
            'Bookeeper Retainer Fee': initial.copy(),
            'total': initial.copy()
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
            'Employee Benefits': 'EMPLOYEE BENEFITS',
            'Bookeeper Retainer Fee': 'BOOKEEPERs RETAINERS FEE',
            'total': 'TOTAL OF EXPENDITURE'
        }


    def get_table(self):
        query = list(mongo.db.lms_fund_wallet_transactions.aggregate([
           {'$match': self.match},
           {'$group': {
               '_id': {'month': {'$month': '$date'}, 'category': '$category'},
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
            self.data[category][month] = total

            self._add_to_total_expenditure(month, total)
            self._add_to_total(category, total)
        self._format_table()
        return self.table


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
