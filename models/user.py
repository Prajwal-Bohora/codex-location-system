from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    users = db.relationship("User", back_populates="role")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    role = db.relationship("Role", back_populates="users")
    student_profile = db.relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consent = db.relationship("LocationConsent", back_populates="user", uselist=False, cascade="all, delete-orphan")

    @property
    def role_name(self):
        return self.role.name if self.role else ""

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_number = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(100))
    year_level = db.Column(db.String(30))
    id_photo = db.Column(db.String(255))
    route_id = db.Column(db.Integer, db.ForeignKey("bus_route.id", ondelete="SET NULL"))
    user = db.relationship("User", back_populates="student_profile")
    route = db.relationship("BusRoute", back_populates="students")
