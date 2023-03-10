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
from prime_admin.utils.currency import format_to_str_php, convert_decimal128_to_decimal
from prime_admin.models import Branch


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
        self.match = _match


    def get_sales_today(self, date=None, branch=None):
        start_date = get_utc_today_start_date(date)
        end_date = get_utc_today_end_date(date)
        self.set_date(start_date, end_date)

        if branch:
            self.set_branch(branch)
        return format_to_str_php(self._calculate())


    def get_total_installment(self):
        self.match['payment_mode'] = {'$in': ['installment', 'installment_promo']}
        self.total_installment = self._calculate()
        return format_to_str_php(self.total_installment)


    def get_total_full_payment(self):
        self.match['payment_mode'] = {'$in': ['full_payment', 'full_payment_promo']}
        self.total_full_payment = self._calculate()
        return format_to_str_php(self.total_full_payment)
    
    
    def get_total_premium_payment(self):
        self.match['payment_mode'] = {'$in': ['premium', 'premium_promo']}
        self.total_premium_payment = self._calculate()
        return format_to_str_php(self.total_premium_payment)
    
    
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
        return format_to_str_php(total)


class ChartService:
    @staticmethod
    def get_expenses_per_month(date_from='', date_to='', branch='all'):
        match = {
            'type': 'expenses'
        }
        if date_from != "":
            match['date_deposit'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from')}
        
        if date_to != '':
            match['date_deposit'] = {'$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if date_from != '' and date_to != '':
            match['date_deposit'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from'), '$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if branch != 'all':
            match['branch'] = ObjectId(branch)
        
        query = list(mongo.db.lms_fund_wallet_transactions.aggregate([
            {
                '$match': match
            }, {
                '$project': {
                    'total_amount_due': 1,
                    'branch': 1,
                    'date': 1,
                    'month': {
                        '$month': '$date'
                    }, 
                    'year': {
                        '$year': '$date'
                    }
                }
            }, {
                '$group': {
                    '_id': {
                        'month': '$month',
                        'year': '$year'
                    }, 
                    'total': {
                        '$sum': '$total_amount_due'
                    }
                }
            }
        ]))
        
        if len(query) == 0:
            return []
        
        results = []
        for document in query:
            results.append({
                'date': "{} {}".format(DATES[document['_id']['month'] - 1], document['_id']['year']),
                'amount': convert_decimal128_to_decimal(document['total'])
            })
        return results
            
    
    @staticmethod
    def get_gross_sales_per_month(date_from='', date_to='', branch='all'):
        group = {
            'month': '$month',
            'year': '$year'
        }
        match = {}

        if date_from != "":
            match['date_deposit'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from')}
        
        if date_to != '':
            match['date_deposit'] = {'$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if date_from != '' and date_to != '':
            match['date_deposit'] = {'$gte': convert_date_input_to_utc(date_from, 'date_from'), '$lte': convert_date_input_to_utc(date_to, 'date_to')}

        if branch != 'all':
            match['branch'] = ObjectId(branch)

        query = list(mongo.db.lms_bank_statements.aggregate([
            {'$match': match},
            {
                '$project': {
                    'branch': 1,
                    'date_deposit': 1,
                    'amount': 1,
                    'month': {
                        '$month': '$date_deposit'
                    },
                    'year': {
                        '$year': '$date_deposit'
                    }
                }
            },
            {
                '$group': {
                    '_id': group,
                    'total_gross_sale': {
                        '$sum': '$amount'
                    }
                }
            },
        ]))
        if len(query) == 0:
            return []
        
        # results = [format_to_str_php(0) for _ in range(12)]
        results = []
        for document in query:
            results.append({
                'date': "{} {}".format(DATES[document['_id']['month'] - 1], document['_id']['year']),
                'amount': convert_decimal128_to_decimal(document['total_gross_sale'])
            })
        return results
            
            
    @staticmethod
    def get_month_labels(date_from, date_to):
        if date_from == '':
            date_from = "2021-03-01"
        if date_to == '':
            date_to = get_local_date_now().strftime("%Y-%m-%d")
            
        date_from = convert_date_input_to_utc(date_from, 'date_from')
        date_to = convert_date_input_to_utc(date_to, 'date_to') + relativedelta(months=1)
        
        results = []
        while date_from < date_to:
            results.append(date_from.strftime("%b %Y"))
            date_from += relativedelta(months=1)
        return results
        

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
