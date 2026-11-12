from extensions import db


class DriverProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    emergency_contact_name = db.Column(db.String(120))
    emergency_contact_phone = db.Column(db.String(32))
    shift_days = db.Column(db.String(80))
    shift_start = db.Column(db.String(5))
    shift_end = db.Column(db.String(5))
    user = db.relationship("User", back_populates="driver_profile")
