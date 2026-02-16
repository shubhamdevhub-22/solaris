import datetime
import pytz


def utc_to_localtime(timezone, utc_time, include_date=False):
    if not timezone:
        timezone = pytz.timezone("UTC")
    else:
        timezone = pytz.timezone(timezone)
    if isinstance(utc_time, str):
        if len(utc_time)==5:utc_time+= ':00'
        utc_time = datetime.datetime.strptime(utc_time, "%H:%M:%S")
    else:
        dt_format = " %Y-%m-%d %H:%M:%S" if include_date else "%H:%M:%S"
        utc_time = datetime.datetime.strptime(utc_time.strftime(dt_format), dt_format)

    utc_datetime = datetime.datetime.now(tz=pytz.timezone("UTC")).replace(hour=utc_time.hour,minute=utc_time.minute)
    return utc_datetime.astimezone(timezone)
