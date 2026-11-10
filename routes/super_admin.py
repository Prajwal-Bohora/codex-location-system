from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Role, AuditLog, Location, LocationConsent
from routes import roles_required

bp = Blueprint("super_admin", __name__, url_prefix="/super-admin")

@bp.get("/")
@login_required
@roles_required("super_admin")
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    counts = {r.name: User.query.join(Role).filter(Role.name == r.name).count() for r in Role.query.all()}
    shared = LocationConsent.query.filter_by(granted=True).count()
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template("dashboard.html", title="Super Admin Dashboard", users=users, counts=counts, shared=shared, logs=logs, admin=True)

@bp.post("/users")
@login_required
@roles_required("super_admin")
def create_user():
    phone, name, role_name, password = (request.form.get(k, "").strip() for k in ("phone", "full_name", "role", "password"))
    role = Role.query.filter_by(name=role_name).first()
    if not phone or not name or not role or len(password) < 10 or User.query.filter_by(phone=phone).first():
        flash("Enter a unique phone, name, valid role, and password of at least 10 characters.", "error")
    else:
        u = User(phone=phone, full_name=name, role=role); u.set_password(password); db.session.add(u)
        db.session.add(AuditLog(actor_id=__import__('flask_login').current_user.id, action="user.created", target=f"{role.name}:{phone}", ip_address=request.remote_addr)); db.session.commit()
        flash("Account created.", "success")
    return redirect(url_for("super_admin.dashboard"))

@bp.post("/users/<int:user_id>/toggle")
@login_required
@roles_required("super_admin")
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == __import__('flask_login').current_user.id:
        flash("You cannot deactivate your own account.", "error")
    else:
        user.active = not user.active
        db.session.add(AuditLog(actor_id=__import__('flask_login').current_user.id, action="user.status_changed", target=user.phone, ip_address=request.remote_addr)); db.session.commit()
        flash("Account status updated.", "success")
    return redirect(url_for("super_admin.dashboard"))

@bp.get("/locations")
@login_required
@roles_required("super_admin")
def locations():
    rows = Location.query.join(LocationConsent, LocationConsent.user_id == Location.user_id).filter(LocationConsent.granted.is_(True)).order_by(Location.recorded_at.desc()).all()
    latest = {}
    for loc in rows: latest.setdefault(loc.user_id, loc)
    return jsonify([{"name": l.user.full_name, "role": l.user.role_name, "lat": l.latitude, "lng": l.longitude, "accuracy": l.accuracy, "time": l.recorded_at.isoformat()} for l in latest.values()])
