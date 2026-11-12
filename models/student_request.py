from datetime import datetime
from extensions import db


class StudentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    category = db.Column(db.String(30), nullable=False)
    subject = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    student = db.relationship("User", foreign_keys=[user_id])
    resolver = db.relationship("User", foreign_keys=[resolved_by])
