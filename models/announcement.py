from datetime import datetime
from extensions import db


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(20), nullable=False, default="all", index=True)
    event_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, index=True)
    urgent = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    author = db.relationship("User")
