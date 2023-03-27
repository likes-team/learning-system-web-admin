from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from bson import ObjectId
from flask_login import current_user
from app import mongo
from prime_admin.utils.date import (
    get_utc_today_end_date, get_utc_today_start_date, get_last_n_days, 
    convert_date_input_to_utc, get_local_date_now, DATES
)
from prime_admin.models import Branch
from prime_admin.utils import currency


class DashboardService:
    def __init__(self, branch=None, date_from=None, date_to=None):
        self.reset_match()
        
        if branch:
            self.set_branch(branch)
        self.set_date(date_from, date_to)


    def set_date(self, date_from, date_to):
        if isinstance(date_from, str):
            date_from = convert_date_input_to_utc(date_from, 'date_from')
        
        if isinstance(date_to, str):
            date_to = convert_date_input_to_utc(date_to, 'date_to')
        
        if date_from:
            self.match['date'] = {'$gte': date_from}

        if date_to:
            self.match['date'] = {'$lte': date_to}

        if date_from and date_to:
            self.match['date'] = {'$gte': date_from, '$lte': date_to}
            

    def set_branch(self, branch):
        self.match['branch'] = ObjectId(branch)
        
    
    def reset_match(self):
        self.match = {}
        _match = {}
        if current_user.role.name == 'Secretary':
            _match['branch'] = current_user.branch.id
        elif current_user.role.name == 'Partner':
            _match['branch'] = {'$in': [ObjectId(branch) for branch in current_user.branches]}
        _match['payment_mode'] = {'$ne': 'refund'}
        self.match = _match


    def get_sales_today(self, date=None, branch=None):
        start_date = get_utc_today_start_date(date)
        end_date = get_utc_today_end_date(date)
        self.set_date(start_date, end_date)

        if branch:
            self.set_branch(branch)
        return currency.format_to_str_php(self._calculate())


    def get_total_installment(self):
        self.match['payment_mode'] = {'$in': ['installment', 'installment_promo']}
        self.total_installment = self._calculate()
        return currency.format_to_str_php(self.total_installment)


    def get_total_full_payment(self):
        self.match['payment_mode'] = {'$in': ['full_payment', 'full_payment_promo']}
        self.total_full_payment = self._calculate()
        return currency.format_to_str_php(self.total_full_payment)
    
    
    def get_total_premium_payment(self):
        self.match['payment_mode'] = {'$in': ['premium', 'premium_promo']}
        self.total_premium_payment = self._calculate()
        return currency.format_to_str_php(self.total_premium_payment)
    
    
    def _calculate(self):
        query = list(mongo.db.lms_registration_payments.aggregate([
            {"$match": self.match},
            {"$group": {
                '_id': None,
                'total': {"$sum": "$amount"}
            }}
        ]))
        if len(query) <= 0:
            return Decimal('0.00')
        total = query[0].get('total')
        return Decimal(str(total))
    

    def get_total(self):
        total = self.total_installment + self.total_full_payment + self.total_premium_payment 
        return currency.format_to_str_php(total)


class ChartService:
    @staticmethod
    def fetch_chart_sales_today(branch=None):
        dashboard_service = DashboardService()

        last_30_days = get_last_n_days(30)
        labels = [day.strftime("%B %d") for day in last_30_days]
        datasets = [{
            'label': "Last 30 days",
            'data': [],
            'backgroundColor': 'rgb(75, 192, 192)'
        }]
        
        for day in last_30_days:
            sales_today = dashboard_service.get_sales_today(date=day, branch=branch)
            datasets[0]['data'].append(sales_today)
        return {
            'labels': labels,
            'datasets': datasets
        }
        
        # if current_user.role.name == 'Admin':
        #     branches = Branch.objects
        # elif current_user.role.name == 'Partner':
        #     branches = Branch.objects(id__in=current_user.branches)
        # else:
        #     raise ValueError("InceptionError: current_user role is not supported yet")

        # labels = [branch.city for branch in branches]
        # datasets = [{
        #     'label': "Branches",
        #     'data': [],
        #     'backgroundColor': 'rgb(75, 192, 192)'
        # }]
        # for branch in branches:
        #     sales_today = dashboard_service.get_sales_today(branch=branch.id)
        #     datasets[0]['data'].append(sales_today)
        # return {
        #     'labels': labels,
        #     'datasets': datasets
        # }


class SalesAndExpensesChart:
    def __init__(self, date_from='', date_to='', branch='all', per='month'):
        self.gross_sales = []
        self.expenses = []
        self.nets = []
        self.maintaining_sales = []

        self.date_from = date_from
        self.date_to = date_to
        self.branch = branch
        self.date_filter = None
        self.per = per
        if self.per == 'month':
            self.group = {
                'month': '$month',
                'year': '$year'
            }
        elif self.per == 'branch':
            self.group = {
                'branch': '$branch'
            }
        
        match = {}
        if date_from != "":
            self.date_filter = {'$gte': convert_date_input_to_utc(date_from, 'date_from')}
        
        if date_to != '':
            self.date_filter = {'$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if date_from != '' and date_to != '':
            self.date_filter = {'$gte': convert_date_input_to_utc(date_from, 'date_from'), '$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if branch != 'all':
            match['branch'] = ObjectId(branch)
        self.match = match

        
    def get_month_labels(self):
        if self.date_from == '':
            self.date_from = "2021-03-01"
        if self.date_to == '':
            self.date_to = get_local_date_now().strftime("%Y-%m-%d")
            
        date_from = convert_date_input_to_utc(self.date_from, 'date_from')
        date_to = convert_date_input_to_utc(self.date_to, 'date_to') + relativedelta(months=1)
        
        results = []
        while date_from < date_to:
            results.append(date_from.strftime("%b %Y"))
            date_from += relativedelta(months=1)
        return results


    def calculate_net_lose_per_branch(self):
        query_branches = mongo.db.lms_branches.find({})
        
        branches = []
        for branch in query_branches:
            branches.append(branch['name'])
        
        labels_count = len(branches)
        registration_sales = [0 for _ in range(labels_count)]
        accommodation_sales = [0 for _ in range(labels_count)]
        store_sales = [0 for _ in range(labels_count)]
        
        gross_sales = [0 for _ in range(labels_count)]
        expenses = [0 for _ in range(labels_count)]
        nets = [0 for _ in range(labels_count)]
            
        for sale in self.get_registration_sales():
            try:
                index = branches.index(sale['branch'])
            except ValueError:
                continue
            registration_sales[index] = sale['amount']
            
        for sale in self.get_accommodation_sales():
            try:
                index = branches.index(sale['branch'])
            except ValueError:
                continue
            accommodation_sales[index] = sale['amount']

        for sale in self.get_store_sales():
            try:
                index = branches.index(sale['branch'])
            except ValueError:
                continue
            store_sales[index] = sale['amount']
            
        for expense in self._get_expenses():
            try:
                index = branches.index(expense['branch'])
            except ValueError:
                continue
            expenses[index] = expense['amount']
            
        for i in range(labels_count):
            gross_sales[i] = registration_sales[i] + accommodation_sales[i] + store_sales[i]

        for i in range(labels_count):
            nets[i] = currency.format_to_str_php(gross_sales[i] - expenses[i])
        
        return {
            'labels': branches,
            'data': nets
        }


    def calculate_sales_and_expenses_per_month(self, format_to_currency=True):
        labels = self.get_month_labels()
        labels_count = len(labels)
        registration_sales = [0 for _ in range(labels_count)]
        accommodation_sales = [0 for _ in range(labels_count)]
        store_sales = [0 for _ in range(labels_count)]
        
        gross_sales = [0 for _ in range(labels_count)]
        expenses = [0 for _ in range(labels_count)]
        maintaining_sales = [85000 for _ in range(labels_count)]
        nets = [0 for _ in range(labels_count)]
        
        for sale in self.get_registration_sales():
            try:
                index = labels.index(sale['date'])
            except ValueError:
                continue
            registration_sales[index] = sale['amount']
            
        for sale in self.get_accommodation_sales():
            try:
                index = labels.index(sale['date'])
            except ValueError:
                continue
            accommodation_sales[index] = sale['amount']
            
        for sale in self.get_store_sales():
            try:
                index = labels.index(sale['date'])
            except ValueError:
                continue
            store_sales[index] = sale['amount']

        for expense in self._get_expenses():
            try:
                index = labels.index(expense['date'])
            except ValueError:
                continue
            expenses[index] = expense['amount']
            
        for i in range(labels_count):
            gross_sales[i] = registration_sales[i] + accommodation_sales[i] + store_sales[i]
        
        for i in range(labels_count):
            nets[i] = gross_sales[i] - expenses[i]
        
        if format_to_currency:
            for i in range(labels_count):
                nets[i] = currency.format_to_str_php(nets[i])
            
            for i in range(len(expenses)):
                expenses[i] = currency.format_to_str_php(expenses[i])
            
            for i in range(len(gross_sales)):
                gross_sales[i] = currency.format_to_str_php(gross_sales[i])
                
        self.gross_sales = gross_sales
        self.expenses = expenses
        self.nets = nets
        self.maintaining_sales = maintaining_sales
    
    def get_gross_sales(self):
        return self.gross_sales

    def get_expenses(self):
        return self.expenses

    def get_nets(self):
        return self.nets
    
    def get_maintaining_sales(self):
        return self.maintaining_sales

    def get_registration_sales(self):
        if self.date_filter:
            self.match['date'] = self.date_filter
        self.match['payment_mode'] = {'$ne': "refund"}
        
        query = list(mongo.db.lms_registration_payments.aggregate([
            {'$match': self.match},
            {
                '$lookup': {
                    'from': 'lms_branches',
                    'localField': 'branch',
                    'foreignField': '_id',
                    'as': 'branch'
                }
            }, {
                '$unwind': {
                    'path': '$branch'
                }
            }, {
                '$project': {
                    'branch': 1,
                    'date': 1,
                    'amount': 1,
                    'month': {
                        '$month': {"date": "$date", "timezone": "Asia/Manila"}
                    },
                    'year': {
                        '$year': {"date": "$date", "timezone": "Asia/Manila"}
                    }
                }
            },
            {
                '$group': {
                    '_id': self.group,
                    'total': {
                        '$sum': '$amount'
                    }
                }
            },
        ]))
        if 'date' in self.match: self.match.pop('date')
        self.match.pop('payment_mode')
        
        student_payments = []
        for document in query:
            if self.per == 'branch':
                student_payments.append({
                    'branch': document['_id']['branch']['name'],
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
            elif self.per == 'month':
                student_payments.append({
                    'date': "{} {}".format(DATES[document['_id']['month'] - 1], document['_id']['year']),
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
        return student_payments
            

    def get_accommodation_sales(self):
        if self.date_filter:
            self.match['created_at'] = self.date_filter

        query = list(mongo.db.lms_accommodations.aggregate([
            {'$match': self.match},
            {
                '$lookup': {
                    'from': 'lms_branches', 
                    'localField': 'branch', 
                    'foreignField': '_id', 
                    'as': 'branch'
                }
            }, {
                '$unwind': {
                    'path': '$branch'
                }
            },
            {
                '$project': {
                    'branch': 1,
                    'created_at': 1,
                    'total_amount': 1,
                    'month': {
                        '$month': {"date": "$created_at", "timezone": "Asia/Manila"}
                    },
                    'year': {
                        '$year': {"date": "$created_at", "timezone": "Asia/Manila"}
                    }
                }
            },
            {
                '$group': {
                    '_id': self.group,
                    'total': {
                        '$sum': '$total_amount'
                    }
                }
            },
        ]))
        if 'created_at' in self.match: self.match.pop('created_at')
        
        accommodations = []
        for document in query:
            if self.per == 'branch':
                accommodations.append({
                    'branch': document['_id']['branch']['name'],
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
            elif self.per == 'month':
                accommodations.append({
                    'date': "{} {}".format(DATES[document['_id']['month'] - 1], document['_id']['year']),
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
        return accommodations


    def get_store_sales(self):
        if self.date_filter: self.match['created_at'] = self.date_filter

        query = list(mongo.db.lms_store_buyed_items.aggregate([
            {'$match': self.match},
            {
                '$lookup': {
                    'from': 'lms_branches',
                    'localField': 'branch',
                    'foreignField': '_id',
                    'as': 'branch'
                }
            }, {
                '$unwind': {
                    'path': '$branch'
                }
            },
            {
                '$project': {
                    'branch': 1,
                    'created_at': 1,
                    'total_amount': 1,
                    'month': {
                        '$month': {"date": "$created_at", "timezone": "Asia/Manila"}
                    },
                    'year': {
                        '$year': {"date": "$created_at", "timezone": "Asia/Manila"}
                    }
                }
            },
            {
                '$group': {
                    '_id': self.group,
                    'total': {
                        '$sum': '$total_amount'
                    }
                }
            },
        ]))
        if 'created_at' in self.match: self.match.pop('created_at')
        
        store = []
        for document in query:
            if self.per == 'branch':
                store.append({
                    'branch': document['_id']['branch']['name'],
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
            elif self.per == 'month':
                store.append({
                    'date': "{} {}".format(DATES[document['_id']['month'] - 1], document['_id']['year']),
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
        return store
    
    
    def _get_expenses(self):
        if self.date_filter: self.match['date'] = self.date_filter
        self.match['type'] = 'expenses'
        
        query = list(mongo.db.lms_fund_wallet_transactions.aggregate([
            {
                '$match': self.match
            }, 
            {
                '$lookup': {
                    'from': 'lms_branches', 
                    'localField': 'branch', 
                    'foreignField': '_id', 
                    'as': 'branch'
                }
            }, {
                '$unwind': {
                    'path': '$branch'
                }
            },{
                '$project': {
                    'total_amount_due': 1,
                    'branch': 1,
                    'date': 1,
                    'month': {
                        '$month': {"date": "$date", "timezone": "Asia/Manila"}
                    }, 
                    'year': {
                        '$year': {"date": "$date", "timezone": "Asia/Manila"}
                    }
                }
            }, {
                '$group': {
                    '_id': self.group, 
                    'total': {
                        '$sum': '$total_amount_due'
                    }
                }
            }
        ]))
        self.match.pop('type')
        if 'date' in self.match: self.match.pop('date')
        
        if len(query) == 0:
            return []
        
        results = []
        for document in query:
            if self.per == 'branch':
                results.append({
                    'branch': document['_id']['branch']['name'],
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
            elif self.per == 'month':
                results.append({
                    'date': "{} {}".format(DATES[document['_id']['month'] - 1], document['_id']['year']),
                    'amount': currency.convert_decimal128_to_decimal(document['total'])
                })
        return results

    def get_expenses_per_category(self):
        if self.date_filter: self.match['date'] = self.date_filter
        self.match['type'] = 'expenses'
        
        query = list(mongo.db.lms_fund_wallet_transactions.aggregate([
            {
                '$match': self.match
            }, {
                '$project': {
                    'total_amount_due': 1,
                    'branch': 1,
                    'date': 1,
                    'category': 1,
                    'month': {
                        '$month': {"date": "$date", "timezone": "Asia/Manila"}
                    }, 
                    'year': {
                        '$year': {"date": "$date", "timezone": "Asia/Manila"}
                    }
                }
            }, {
                '$group': {
                    '_id': {
                        'category': '$category',
                    }, 
                    'total': {
                        '$sum': '$total_amount_due'
                    }
                }
            }
        ]))
        self.match.pop('type')
        if 'date' in self.match: self.match.pop('date')
        
        if len(query) == 0:
            return []
        
        results = []
        for document in query:
            results.append({
                'category': document['_id']['category'],
                'amount': currency.convert_decimal128_to_decimal(document['total'])
            })
        return results