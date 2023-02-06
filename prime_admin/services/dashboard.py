from decimal import Decimal
from datetime import timedelta
from bson import ObjectId
from flask_login import current_user
from app import mongo
from prime_admin.utils.date import (
    get_utc_today_end_date, get_utc_today_start_date, get_last_7_days
)
from prime_admin.utils.currency import format_to_str_php
from prime_admin.models import Branch



class DashboardService:
    def __init__(self, branch=None):
        self.reset_match()
        
        if branch:
            self.set_branch(branch)


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
        self.match['date'] = {"$gte": start_date, "$lte": end_date}

        if branch:
            self.set_branch(branch)
        return format_to_str_php(self._calculate())


    def get_total_installment(self):
        self.reset_match()
        self.match['payment_mode'] = 'installment'
        self.total_installment = self._calculate()
        return format_to_str_php(self.total_installment)


    def get_total_full_payment(self):
        self.reset_match()
        self.match['payment_mode'] = 'full_payment'
        self.total_full_payment = self._calculate()
        return format_to_str_php(self.total_full_payment)
    
    
    def get_total_premium_payment(self):
        self.reset_match()
        self.match['payment_mode'] = 'premium'
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
    def fetch_chart_sales_today():
        dashboard_service = DashboardService()

        if current_user.role.name == 'Secretary':
            last_7_days = get_last_7_days()
            labels = [day.strftime("%B %d") for day in last_7_days]
            datasets = [{
                'label': "Last 7 days",
                'data': [],
                'backgroundColor': 'rgb(75, 192, 192)'
            }]
            
            for day in last_7_days:
                sales_today = dashboard_service.get_sales_today(date=day)
                datasets[0]['data'].append(sales_today)
            return {
                'labels': labels,
                'datasets': datasets
            }
        
        if current_user.role.name == 'Admin':
            branches = Branch.objects
        elif current_user.role.name == 'Partner':
            branches = Branch.objects(id__in=current_user.branches)
        else:
            raise ValueError("InceptionError: current_user role is not supported yet")

        labels = [branch.city for branch in branches]
        datasets = [{
            'label': "Branches",
            'data': [],
            'backgroundColor': 'rgb(75, 192, 192)'
        }]
        for branch in branches:
            sales_today = dashboard_service.get_sales_today(branch=branch.id)
            datasets[0]['data'].append(sales_today)
        return {
            'labels': labels,
            'datasets': datasets
        }
