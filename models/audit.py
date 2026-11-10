from datetime import datetime, timezone
from extensions import db


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(160))
    ip_address = db.Column(db.String(48))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    actor = db.relationship("User")
