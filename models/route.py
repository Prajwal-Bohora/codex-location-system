from extensions import db


class BusRoute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    vehicle = db.Column(db.String(80))
    active = db.Column(db.Boolean, nullable=False, default=True)
    checkpoints = db.relationship("RouteCheckpoint", back_populates="route", cascade="all, delete-orphan", order_by="RouteCheckpoint.position")
    assignments = db.relationship("DriverAssignment", back_populates="route", cascade="all, delete-orphan")
    students = db.relationship("StudentProfile", back_populates="route")


class RouteCheckpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("bus_route.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    route = db.relationship("BusRoute", back_populates="checkpoints")


class DriverAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    route_id = db.Column(db.Integer, db.ForeignKey("bus_route.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle = db.Column(db.String(80))
    active = db.Column(db.Boolean, nullable=False, default=True)
    driver = db.relationship("User")
    route = db.relationship("BusRoute", back_populates="assignments")
