import pytz
from datetime import datetime, timedelta
from config import TIMEZONE



def get_local_date_now():
    """Get local date now from a UTC date

    Returns:
        datetime: Datetime object
    """
    utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    local = utc.astimezone(TIMEZONE)
    return local


def get_utc_today_start_date(date=None):
    if date:
        local = date
    else:
        local = get_local_date_now()

    local_start_date = local.replace(hour=0, minute=0)
    utc_start_date = local_start_date.astimezone(pytz.utc)
    return utc_start_date


def get_utc_today_end_date(date=None):
    if date:
        local = date
    else:
        local = get_local_date_now()

    local_end_date = local.replace(hour=23, minute=59)
    utc_end_date = local_end_date.astimezone(pytz.utc)
    return utc_end_date


def get_last_7_days():
    now = get_local_date_now()
    results = []
    
    for x in range(7):
        day = now - timedelta(days=x)
        results.append(day)
    results.reverse()
    return results


def convert_date_input_to_utc(date_str, date_type):
    naive = datetime.strptime(date_str, "%Y-%m-%d")
    local_dt = TIMEZONE.localize(naive, is_dst=None)

    if date_type == "date_from":
        local_dt = local_dt.replace(hour=0, minute=0, second=0)
    elif date_type == "date_to":
        local_dt = local_dt.replace(hour=23, minute=59, second=59)
    else:
        raise ValueError("InceptionError: invalid date_type value")

    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def format_utc_to_local(date, date_format="%B %d, %Y"):
    if type(date == datetime):
        local_dt = date.replace(tzinfo=pytz.utc).astimezone(TIMEZONE).strftime(date_format)
    elif type(date == str):
        naive = datetime.strptime(date, "%Y-%m-%d")
        local_dt = TIMEZONE.localize(naive, is_dst=None).strftime(date_format)
    else:
        local_dt = ''
    return local_dt