from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models import Location, LocationConsent, User, Role, DriverAssignment, StudentProfile, AuditLog, BusRoute
from routes import roles_required

bp=Blueprint("location",__name__,url_prefix="/api/location")

@bp.get("/status")
@login_required
def status():
    c=current_user.consent
    return jsonify({"granted":bool(c and c.granted),"role":current_user.role_name})

@bp.post("/consent")
@login_required
@roles_required("driver")
def consent():
    granted=request.json.get("granted") if request.is_json else None
    if not isinstance(granted,bool): return jsonify(error="A consent decision is required."),400
    c=current_user.consent or LocationConsent(user_id=current_user.id)
    c.granted=granted
    if granted: c.granted_at=datetime.now(timezone.utc);c.withdrawn_at=None
    else:
        c.withdrawn_at=datetime.now(timezone.utc)
        # Delete retained precise locations when consent is withdrawn.
        Location.query.filter_by(user_id=current_user.id).delete()
    db.session.add(c);db.session.add(AuditLog(actor_id=current_user.id,action="location.consent_granted" if granted else "location.consent_withdrawn",ip_address=request.remote_addr));db.session.commit()
    return jsonify(granted=granted)

@bp.post("")
@login_required
@roles_required("driver")
def update():
    c=current_user.consent
    if not c or not c.granted: abort(403)
    data=request.get_json(silent=True) or {}
    try:
        lat=float(data.get("latitude"));lng=float(data.get("longitude"));accuracy=float(data.get("accuracy"))
        if not (-90<=lat<=90 and -180<=lng<=180 and 0<=accuracy<=100000): raise ValueError()
    except (TypeError,ValueError): return jsonify(error="Invalid GPS coordinates or accuracy."),400
    loc=Location(user_id=current_user.id,latitude=lat,longitude=lng,accuracy=accuracy);db.session.add(loc);db.session.commit();return jsonify(ok=True,recorded_at=loc.recorded_at.isoformat())

def _visible_location(user):
    if not user.consent or not user.consent.granted:return None
    l=Location.query.filter_by(user_id=user.id).order_by(Location.recorded_at.desc()).first()
    if not l:return None
    return {"name":user.full_name,"lat":l.latitude,"lng":l.longitude,"accuracy":l.accuracy,"time":l.recorded_at.isoformat()}

@bp.get("/drivers")
@login_required
def driver_locations():
    role=current_user.role_name
    if role=="teacher":abort(403)
    if role=="super_admin": drivers=User.query.join(Role).filter(Role.name=="driver").all()
    elif role=="admin": drivers=User.query.join(Role).filter(Role.name=="driver").all()
    elif role=="student":
        profile=current_user.student_profile
        if not profile or not profile.route_id:return jsonify([])
        ids=[a.driver_id for a in DriverAssignment.query.filter_by(route_id=profile.route_id,active=True).all()]
        drivers=User.query.filter(User.id.in_(ids)).all() if ids else []
    else:abort(403)
    return jsonify([x for d in drivers if (x:=_visible_location(d))])

@bp.get("/me")
@login_required
@roles_required("driver")
def my_location():
    item=_visible_location(current_user)
    return jsonify(item or {})

@bp.get("/route/<int:route_id>")
@login_required
def route_info(route_id):
    route=BusRoute.query.filter_by(id=route_id,active=True).first_or_404()
    role=current_user.role_name
    allowed=role in ("admin","super_admin") or (role=="student" and current_user.student_profile and current_user.student_profile.route_id==route.id) or (role=="driver" and DriverAssignment.query.filter_by(driver_id=current_user.id,route_id=route.id,active=True).first())
    if not allowed:abort(403)
    assignments=DriverAssignment.query.filter_by(route_id=route.id,active=True).all()
    drivers=[]
    for a in assignments:
        d=a.driver;drivers.append({"name":d.full_name,"location":_visible_location(d)})
    return jsonify({"id":route.id,"name":route.name,"vehicle":route.vehicle,"checkpoints":[{"name":c.name,"description":c.description,"lat":c.latitude,"lng":c.longitude} for c in route.checkpoints],"drivers":drivers})
