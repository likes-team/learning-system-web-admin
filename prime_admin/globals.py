import pytz
from config import TIMEZONE
from datetime import datetime
from app.auth.models import Role


SECRETARYREFERENCE = Role.objects(name="Secretary").get().id
PARTNERREFERENCE = Role.objects(name="Partner").get().id
MARKETERREFERENCE = Role.objects(name="Marketer").get().id


def get_date_now():
    date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
    naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    local_dt = TIMEZONE.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def get_sales_today_date():
    local_datetime = get_date_now().replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    # return local_datetime.strftime("%B %d, %Y %I:%M %p")
        
    return local_datetime