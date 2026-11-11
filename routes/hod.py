from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, Role, StudentProfile, BusRoute, RouteCheckpoint, DriverAssignment, LocationConsent, Location, AuditLog
from routes import roles_required
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint("hod", __name__, url_prefix="/hod")

@bp.get("/")
@login_required
@roles_required("admin")
def dashboard():
    users=User.query.order_by(User.created_at.desc()).all(); routes=BusRoute.query.all()
    locs=Location.query.join(LocationConsent, LocationConsent.user_id==Location.user_id).filter(LocationConsent.granted.is_(True)).order_by(Location.recorded_at.desc()).all()
    latest={}
    for l in locs:
        if l.user.role_name == "driver": latest.setdefault(l.user_id,l)
    return render_template("dashboard.html", title="HOD Administration", users=users, routes=routes, latest=list(latest.values()), admin=True)

@bp.get("/people/<role_name>")
@login_required
@roles_required("admin")
def people(role_name):
    if role_name not in ("student", "teacher", "driver"):
        return "Unknown people section", 404
    role=Role.query.filter_by(name=role_name).first_or_404()
    users=User.query.filter_by(role_id=role.id).order_by(User.full_name).all()
    return render_template("hod/people.html", title=f"{role_name.title()} Section", role_name=role_name, users=users)

@bp.get("/users/<int:user_id>")
@login_required
@roles_required("admin")
def user_profile(user_id):
    user=User.query.get_or_404(user_id)
    if user.role_name not in ("student", "teacher", "driver"):
        return "Profile not available in this section", 404
    assignments=DriverAssignment.query.filter_by(driver_id=user.id,active=True).all() if user.role_name=="driver" else []
    latest_location=None
    if user.role_name=="driver" and user.consent and user.consent.granted:
        latest_location=Location.query.filter_by(user_id=user.id).order_by(Location.recorded_at.desc()).first()
    return render_template("hod/profile.html", title=f"{user.full_name} · Profile", user=user, assignments=assignments, latest_location=latest_location)

@bp.post("/users")
@login_required
@roles_required("admin")
def create_user():
    name=request.form.get("full_name", "").strip(); phone=request.form.get("phone", "").strip(); role_name=request.form.get("role", "")
    password=request.form.get("password", ""); role=Role.query.filter_by(name=role_name).first()
    if role_name not in ("teacher","driver","student") or not role or not name or not phone or len(password)<10 or User.query.filter_by(phone=phone).first():
        flash("Check the account details. Passwords must contain at least 10 characters and phone numbers must be unique.","error")
    else:
        u=User(phone=phone,full_name=name,role=role);u.set_password(password);db.session.add(u);db.session.flush()
        if role_name=="student": db.session.add(StudentProfile(user_id=u.id,student_number=request.form.get("student_number") or None))
        db.session.add(AuditLog(actor_id=current_user.id,action="user.created",target=f"{role_name}:{phone}",ip_address=request.remote_addr));db.session.commit();flash("Account created.","success")
    return redirect(url_for("hod.dashboard"))

@bp.post("/students/<int:user_id>/photo")
@login_required
@roles_required("admin")
def student_photo(user_id):
    user=User.query.get_or_404(user_id)
    if user.role_name!="student" or not user.student_profile: return "Not a student",404
    file=request.files.get("photo"); allowed={"png","jpg","jpeg","webp"}
    if not file or "." not in file.filename or file.filename.rsplit(".",1)[1].lower() not in allowed: flash("Choose a PNG, JPG, or WebP image.","error")
    else:
        ext=file.filename.rsplit(".",1)[1].lower();header=file.stream.read(12);file.stream.seek(0)
        valid=(ext=="png" and header.startswith(b"\x89PNG\r\n\x1a\n")) or (ext in ("jpg","jpeg") and header.startswith(b"\xff\xd8\xff")) or (ext=="webp" and header.startswith(b"RIFF") and header[8:12]==b"WEBP")
        if not valid: flash("The uploaded file does not match a supported image format.","error");return redirect(url_for("hod.dashboard"))
        path=Path(__import__('flask').current_app.config["UPLOAD_FOLDER"]);path.mkdir(parents=True,exist_ok=True)
        name=f"{uuid.uuid4().hex}.{ext}";file.save(path/name);user.student_profile.id_photo=name;db.session.commit();flash("Student photo saved.","success")
    return redirect(url_for("hod.dashboard"))

@bp.post("/routes")
@login_required
@roles_required("admin")
def create_route():
    name=request.form.get("name", "").strip()
    if not name or BusRoute.query.filter_by(name=name).first(): flash("Enter a unique route name.","error")
    else:
        r=BusRoute(name=name,description=request.form.get("description"),vehicle=request.form.get("vehicle"));db.session.add(r);db.session.flush()
        driver_id=request.form.get("driver_id",type=int)
        if driver_id and User.query.filter_by(id=driver_id).join(Role).filter(Role.name=="driver").first(): db.session.add(DriverAssignment(driver_id=driver_id,route_id=r.id,vehicle=r.vehicle))
        db.session.add(AuditLog(actor_id=current_user.id,action="route.created",target=name,ip_address=request.remote_addr));db.session.commit();flash("Route created.","success")
    return redirect(url_for("hod.dashboard"))

@bp.post("/routes/<int:route_id>/checkpoints")
@login_required
@roles_required("admin")
def add_checkpoint(route_id):
    route=BusRoute.query.get_or_404(route_id)
    try:
        lat=float(request.form.get("latitude"));lng=float(request.form.get("longitude"))
        if not (-90<=lat<=90 and -180<=lng<=180): raise ValueError()
    except (TypeError,ValueError): flash("Select a valid point on the map first.","error");return redirect(url_for("hod.dashboard"))
    name=request.form.get("name", "").strip()
    if not name: flash("Checkpoint name is required.","error")
    else: db.session.add(RouteCheckpoint(route_id=route.id,name=name,description=request.form.get("description"),latitude=lat,longitude=lng,position=len(route.checkpoints)));db.session.commit();flash("Checkpoint added.","success")
    return redirect(url_for("hod.dashboard"))

@bp.post("/checkpoints/<int:checkpoint_id>/delete")
@login_required
@roles_required("admin")
def delete_checkpoint(checkpoint_id):
    checkpoint=RouteCheckpoint.query.get_or_404(checkpoint_id);db.session.add(AuditLog(actor_id=current_user.id,action="checkpoint.deleted",target=f"{checkpoint.route.name}:{checkpoint.name}",ip_address=request.remote_addr));db.session.delete(checkpoint);db.session.commit();flash("Checkpoint deleted.","success")
    return redirect(url_for("hod.dashboard"))

@bp.post("/routes/<int:route_id>/delete")
@login_required
@roles_required("admin")
def delete_route(route_id):
    route=BusRoute.query.get_or_404(route_id);db.session.add(AuditLog(actor_id=current_user.id,action="route.deleted",target=route.name,ip_address=request.remote_addr));db.session.delete(route);db.session.commit();flash("Route and its checkpoints deleted. Students assigned to it are now unassigned.","success")
    return redirect(url_for("hod.dashboard"))

@bp.post("/students/<int:user_id>/route")
@login_required
@roles_required("admin")
def assign_student_route(user_id):
    u=User.query.get_or_404(user_id)
    if u.student_profile: u.student_profile.route_id=request.form.get("route_id",type=int) or None;db.session.commit();flash("Student route updated.","success")
    return redirect(url_for("hod.dashboard"))
