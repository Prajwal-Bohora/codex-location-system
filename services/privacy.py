from datetime import datetime, timedelta
from models import Location, SystemSetting
from extensions import db

DEFAULT_LOCATION_RETENTION_DAYS = 30


def get_location_retention_days():
    setting=SystemSetting.query.filter_by(key="location_retention_days").first()
    if not setting:
        setting=SystemSetting(key="location_retention_days",value=str(DEFAULT_LOCATION_RETENTION_DAYS))
        db.session.add(setting);db.session.commit()
    try:
        days=int(setting.value)
    except (TypeError,ValueError):
        days=DEFAULT_LOCATION_RETENTION_DAYS
    return min(max(days,1),3650)


def purge_expired_locations(days=None):
    keep_days=days or get_location_retention_days()
    cutoff=datetime.utcnow()-timedelta(days=keep_days)
    return Location.query.filter(Location.recorded_at<cutoff).delete(synchronize_session=False)
