from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Role, AuditLog
from routes import roles_required
bp=Blueprint("teacher",__name__,url_prefix="/teacher")
@bp.get("/")
@login_required
@roles_required("teacher")
def dashboard():
    students=User.query.join(Role).filter(Role.name=="student",User.active.is_(True)).order_by(User.full_name).all()
    departments=sorted({u.student_profile.department for u in students if u.student_profile and u.student_profile.department})
    return render_template("dashboard.html",title="Teacher Dashboard",users=students,teacher=True,departments=departments)

@bp.get("/students/<int:user_id>")
@login_required
@roles_required("teacher")
def student_profile(user_id):
    student=User.query.join(Role).filter(User.id==user_id,Role.name=="student",User.active.is_(True)).first_or_404()
    db.session.add(AuditLog(actor_id=current_user.id,action="profile.viewed",target=f"student:{student.id}",ip_address=request.remote_addr));db.session.commit()
    return render_template("teacher/student_profile.html",title=f"{student.full_name} · Student profile",student=student)
