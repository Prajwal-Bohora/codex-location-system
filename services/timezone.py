from datetime import timedelta, timezone

NEPAL_TZ=timezone(timedelta(hours=5,minutes=45),name="NPT")


def to_nepal_time(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value=value.replace(tzinfo=timezone.utc)
    return value.astimezone(NEPAL_TZ)


def nepal_time_to_utc_naive(value):
    if value.tzinfo is None:
        value=value.replace(tzinfo=NEPAL_TZ)
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def format_nepal_time(value,fmt="%Y-%m-%d %I:%M:%S %p NPT"):
    converted=to_nepal_time(value)
    return converted.strftime(fmt) if converted else "—"
