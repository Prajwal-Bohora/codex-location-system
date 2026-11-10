from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_required,current_user
from models import BusRoute
from extensions import db
from routes import roles_required
bp=Blueprint("student",__name__,url_prefix="/student")
@bp.get("/")
@login_required
@roles_required("student")
def dashboard():
    routes=BusRoute.query.filter_by(active=True).order_by(BusRoute.name).all()
    profile=current_user.student_profile
    return render_template("dashboard.html",title="Student Dashboard",routes=routes,profile=profile,student=True)

@bp.post("/route")
@login_required
@roles_required("student")
def select_route():
    profile=current_user.student_profile
    route_id=request.form.get("route_id",type=int)
    route=BusRoute.query.filter_by(id=route_id,active=True).first() if route_id else None
    if not profile:
        from models import StudentProfile
        profile=StudentProfile(user_id=current_user.id);db.session.add(profile)
    if route_id and not route: flash("Select a valid active route.","error")
    else: profile.route_id=route.id if route else None;db.session.commit();flash("Route selection saved.","success")
    return redirect(url_for("student.dashboard"))
