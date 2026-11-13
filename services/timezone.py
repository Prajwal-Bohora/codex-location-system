from datetime import timedelta, timezone

NEPAL_TZ=timezone(timedelta(hours=5,minutes=45),name="NPT")


def to_nepal_time(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value=value.replace(tzinfo=timezone.utc)
    return value.astimezone(NEPAL_TZ)


def format_nepal_time(value,fmt="%Y-%m-%d %I:%M:%S %p NPT"):
    converted=to_nepal_time(value)
    return converted.strftime(fmt) if converted else "—"
