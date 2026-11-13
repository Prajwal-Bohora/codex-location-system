from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, Response, send_file, current_app
from io import StringIO, BytesIO
import csv
import sqlite3
import zipfile
from pathlib import Path
from datetime import datetime
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Role, AuditLog, Location, LocationConsent, BusRoute, DriverAssignment
from routes import roles_required
from models import SystemSetting
from services.privacy import get_location_retention_days, purge_expired_locations
from services.timezone import to_nepal_time

bp = Blueprint("super_admin", __name__, url_prefix="/super-admin")

@bp.get("/")
@login_required
@roles_required("super_admin")
def dashboard():
    purge_expired_locations(get_location_retention_days());db.session.commit()
    users = User.query.order_by(User.created_at.desc()).all()
    counts = {r.name: User.query.join(Role).filter(Role.name == r.name).count() for r in Role.query.all()}
    shared = len(_latest_consented_locations())
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template("dashboard.html", title="Super Admin Dashboard", users=users, counts=counts, shared=shared, logs=logs, admin=True, retention_days=get_location_retention_days())

@bp.get("/users/<int:user_id>")
@login_required
@roles_required("super_admin")
def user_profile(user_id):
    user=User.query.get_or_404(user_id)
    if user.id==current_user.id or user.role_name=="super_admin":abort(404)
    latest_location=None
    if user.active and user.consent and user.consent.granted:
        latest_location=Location.query.filter_by(user_id=user.id).order_by(Location.recorded_at.desc()).first()
    assignments=DriverAssignment.query.filter_by(driver_id=user.id,active=True).all() if user.role_name=="driver" else []
    routes=BusRoute.query.filter_by(active=True).order_by(BusRoute.name).all()
    db.session.add(AuditLog(actor_id=current_user.id,action="profile.viewed",target=f"{user.role_name}:{user.id}",ip_address=request.remote_addr));db.session.commit()
    return render_template("super_admin/profile.html",title=f"{user.full_name} · Profile",user=user,latest_location=latest_location,assignments=assignments,routes=routes)

@bp.get("/routes")
@login_required
@roles_required("super_admin")
def route_list():
    routes=BusRoute.query.order_by(BusRoute.name).all()
    db.session.add(AuditLog(actor_id=current_user.id,action="route.directory_viewed",target=f"{len(routes)} routes",ip_address=request.remote_addr));db.session.commit()
    return render_template("super_admin/routes.html",title="University routes",routes=routes)

@bp.get("/routes/<int:route_id>")
@login_required
@roles_required("super_admin")
def route_detail(route_id):
    route=BusRoute.query.get_or_404(route_id)
    assignments=DriverAssignment.query.filter_by(route_id=route.id,active=True).all()
    drivers=[];map_drivers=[]
    for assignment in assignments:
        driver=assignment.driver
        if not driver or not driver.active or driver.role_name!="driver":continue
        location=None
        if driver.consent and driver.consent.granted:
            location=Location.query.filter_by(user_id=driver.id).order_by(Location.recorded_at.desc()).first()
        drivers.append({"user":driver,"assignment":assignment,"location":location})
        if location:
            map_drivers.append({"name":driver.full_name,"lat":location.latitude,"lng":location.longitude,"time":location.recorded_at.isoformat()})
    checkpoints=[{"name":c.name,"description":c.description,"lat":c.latitude,"lng":c.longitude,"position":c.position} for c in route.checkpoints]
    db.session.add(AuditLog(actor_id=current_user.id,action="route.viewed",target=route.name,ip_address=request.remote_addr));db.session.commit()
    return render_template("super_admin/route_detail.html",title=f"{route.name} · Route",route=route,drivers=drivers,map_data={"checkpoints":checkpoints,"drivers":map_drivers})

@bp.get("/activity")
@login_required
@roles_required("super_admin")
def activity():
    role=request.args.get("role","all")
    if role not in {"all","student","teacher","driver","admin","super_admin"}:abort(400)
    query=AuditLog.query.outerjoin(User,AuditLog.actor_id==User.id).outerjoin(Role,User.role_id==Role.id)
    if role!="all":query=query.filter(Role.name==role)
    logs=query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return render_template("super_admin/activity.html",title="University activity",logs=logs,selected_role=role)

@bp.post("/privacy/retention")
@login_required
@roles_required("super_admin")
def set_location_retention():
    try:days=int(request.form.get("days", ""))
    except ValueError:days=0
    if not 1<=days<=3650:
        flash("Choose a location retention period from 1 to 3,650 days.","error")
    else:
        setting=SystemSetting.query.filter_by(key="location_retention_days").first()
        if not setting:setting=SystemSetting(key="location_retention_days",value=str(days));db.session.add(setting)
        else:setting.value=str(days)
        deleted=purge_expired_locations(days)
        db.session.add(AuditLog(actor_id=__import__('flask_login').current_user.id,action="location.retention_updated",target=f"{days} days; {deleted} old records removed",ip_address=request.remote_addr));db.session.commit()
        flash(f"Location retention set to {days} days. Removed {deleted} older location records.","success")
    return redirect(url_for("super_admin.dashboard"))

def _latest_consented_locations():
    rows = Location.query.join(LocationConsent, LocationConsent.user_id == Location.user_id).join(User,User.id==Location.user_id).filter(LocationConsent.granted.is_(True),User.active.is_(True)).order_by(Location.recorded_at.desc()).all()
    latest = {}
    for loc in rows:
        latest.setdefault(loc.user_id, loc)
    return latest.values()

@bp.get("/users")
@login_required
@roles_required("super_admin")
def user_list():
    role_name = request.args.get("role", "all")
    query = User.query.join(Role)
    if role_name != "all":
        if role_name not in {"student", "teacher", "driver", "admin", "super_admin"}:
            abort(400)
        query = query.filter(Role.name == role_name)
    users = query.order_by(User.full_name).all()
    return jsonify([{"id": u.id, "name": u.full_name, "phone": u.phone, "role": u.role_name, "active": u.active} for u in users])

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
        if not user.active and user.role_name=="driver":
            if user.consent:user.consent.granted=False;user.consent.withdrawn_at=datetime.utcnow()
            Location.query.filter_by(user_id=user.id).delete()
        db.session.add(AuditLog(actor_id=__import__('flask_login').current_user.id, action="user.status_changed", target=user.phone, ip_address=request.remote_addr)); db.session.commit()
        flash("Account status updated.", "success")
    return redirect(url_for("super_admin.dashboard"))

@bp.get("/locations")
@login_required
@roles_required("super_admin")
def locations():
    latest = _latest_consented_locations()
    return jsonify([{"id": l.user_id, "name": l.user.full_name, "role": l.user.role_name, "lat": l.latitude, "lng": l.longitude, "accuracy": l.accuracy, "time": l.recorded_at.isoformat()} for l in latest])

@bp.get("/audit.csv")
@login_required
@roles_required("super_admin")
def export_audit():
    output=StringIO();writer=csv.writer(output)
    writer.writerow(["Timestamp (NPT)","Actor","Action","Target","IP address"])
    for entry in AuditLog.query.order_by(AuditLog.created_at.desc()).all():
        writer.writerow([to_nepal_time(entry.created_at).isoformat(timespec="seconds"),entry.actor.full_name if entry.actor else "System",entry.action,entry.target or "",entry.ip_address or ""])
    return Response("\ufeff"+output.getvalue(),mimetype="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=midwest-audit-log.csv"})

@bp.get("/backup.sqlite.zip")
@login_required
@roles_required("super_admin")
def download_backup():
    if db.engine.dialect.name!="sqlite":abort(400,description="This backup download supports SQLite databases only.")
    database=db.engine.url.database
    if not database or database==":memory:":abort(400,description="No file-backed SQLite database is configured.")
    db_path=Path(database)
    if not db_path.is_absolute():db_path=Path(current_app.instance_path)/db_path
    if not db_path.exists():abort(404,description="SQLite database file was not found.")
    db.session.add(AuditLog(actor_id=__import__('flask_login').current_user.id,action="system.backup_downloaded",target="SQLite database and uploads",ip_address=request.remote_addr));db.session.commit()
    memory_db=sqlite3.connect(":memory:")
    try:
        with sqlite3.connect(str(db_path)) as source:source.backup(memory_db)
        database_bytes=memory_db.serialize()
    finally:memory_db.close()
    archive=BytesIO();stamp=datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("midwest_app.sqlite3",database_bytes)
        upload_dir=Path(current_app.config["UPLOAD_FOLDER"])
        if upload_dir.exists():
            for path in upload_dir.rglob("*"):
                if path.is_file():bundle.write(path,Path("uploads")/path.relative_to(upload_dir))
    archive.seek(0)
    return send_file(archive,mimetype="application/zip",as_attachment=True,download_name=f"midwest-backup-{stamp}.zip")
