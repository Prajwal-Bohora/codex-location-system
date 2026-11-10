from datetime import datetime, timezone
from extensions import db


class LocationConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    granted = db.Column(db.Boolean, nullable=False, default=False)
    granted_at = db.Column(db.DateTime(timezone=True))
    withdrawn_at = db.Column(db.DateTime(timezone=True))
    user = db.relationship("User", back_populates="consent")


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    user = db.relationship("User")
