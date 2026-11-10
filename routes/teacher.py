from flask import Blueprint, render_template
from flask_login import login_required
from models import User, Role
from routes import roles_required
bp=Blueprint("teacher",__name__,url_prefix="/teacher")
@bp.get("/")
@login_required
@roles_required("teacher")
def dashboard():
    students=User.query.join(Role).filter(Role.name=="student",User.active.is_(True)).order_by(User.full_name).all()
    return render_template("dashboard.html",title="Teacher Dashboard",users=students,teacher=True)
