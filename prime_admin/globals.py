import pytz
from config import TIMEZONE
from datetime import datetime
from app.auth.models import Role
from bson.decimal128 import create_decimal128_context


SECRETARYREFERENCE = Role.objects(name="Secretary").get().id
PARTNERREFERENCE = Role.objects(name="Partner").get().id
MARKETERREFERENCE = Role.objects(name="Marketer").get().id
MANAGEREFERENCE = Role.objects(name="Manager").get().id

D128_CTX = create_decimal128_context()


def get_date_now():
    date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
    naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    local_dt = TIMEZONE.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def convert_to_utc(date, t='date_to'):
    if t == 'date_to':
        date_string = date + " 23:59:59"
    else:
        date_string = date + " 00:00:00"

    naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    local_dt = TIMEZONE.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt

def convert_to_local(date):
    local_datetime = ''
    if date is not None:
        local_datetime = date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
        return local_datetime.strftime("%B %d, %Y %I:%M %p")
        
    return local_datetime


def get_sales_today_date():
    local_datetime = get_date_now().replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    # return local_datetime.strftime("%B %d, %Y %I:%M %p")
        
    return local_datetime


