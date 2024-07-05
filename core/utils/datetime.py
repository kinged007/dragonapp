from datetime import *

def utc_datetime(d:datetime):
    return d.replace(tzinfo=timezone.utc)

def utc_now():
    return datetime.now(timezone.utc)

def nice_time():
    # UTC Time
    return utc_now().strftime("%Y-%m-%d %H:%M:%S")