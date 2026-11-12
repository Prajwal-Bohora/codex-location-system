from flask import Blueprint,render_template
from flask_login import login_required,current_user
from models import DriverAssignment, DriverProfile
from routes import roles_required
bp=Blueprint("driver",__name__,url_prefix="/driver")
@bp.get("/")
@login_required
@roles_required("driver")
def dashboard():
    assignments=DriverAssignment.query.filter_by(driver_id=current_user.id,active=True).all()
    driver_profile=DriverProfile.query.filter_by(user_id=current_user.id).first()
    return render_template("dashboard.html",title="Driver Dashboard",assignments=assignments,routes=[a.route for a in assignments],driver_profile=driver_profile,driver=True)
