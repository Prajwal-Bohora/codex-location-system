from datetime import datetime, timezone
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from extensions import db
from models import Announcement, AuditLog, StudentRequest
from routes import roles_required

bp = Blueprint("portal", __name__, url_prefix="/portal")
AUDIENCES = {"all", "student", "teacher", "driver", "admin"}


@bp.get("/announcements")
@login_required
@roles_required("admin", "super_admin")
def announcements():
    items=Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template("portal/announcements.html",title="Campus announcements",announcements=items)


@bp.post("/announcements")
@login_required
@roles_required("admin", "super_admin")
def create_announcement():
    title=request.form.get("title", "").strip();body=request.form.get("body", "").strip();audience=request.form.get("audience", "all")
    try:
        event_at=datetime.fromisoformat(request.form["event_at"]) if request.form.get("event_at") else None
        expires_at=datetime.fromisoformat(request.form["expires_at"]) if request.form.get("expires_at") else None
        if event_at and event_at.tzinfo:event_at=event_at.astimezone(timezone.utc).replace(tzinfo=None)
        if expires_at and expires_at.tzinfo:expires_at=expires_at.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        flash("Enter a valid event or expiry date.","error");return redirect(url_for("portal.announcements"))
    if not title or not body or audience not in AUDIENCES:
        flash("Enter a title, message, and valid audience.","error")
    elif expires_at and expires_at <= datetime.utcnow():
        flash("The expiry time must be in the future.","error")
    else:
        announcement=Announcement(author_id=current_user.id,title=title,body=body,audience=audience,event_at=event_at,expires_at=expires_at,urgent=bool(request.form.get("urgent")))
        db.session.add(announcement);db.session.add(AuditLog(actor_id=current_user.id,action="announcement.created",target=title,ip_address=request.remote_addr));db.session.commit()
        flash("Announcement published.","success")
    return redirect(url_for("portal.announcements"))


@bp.post("/announcements/<int:announcement_id>/toggle")
@login_required
@roles_required("admin", "super_admin")
def toggle_announcement(announcement_id):
    item=Announcement.query.get_or_404(announcement_id);item.active=not item.active
    db.session.add(AuditLog(actor_id=current_user.id,action="announcement.status_changed",target=item.title,ip_address=request.remote_addr));db.session.commit()
    flash("Announcement visibility updated.","success")
    return redirect(url_for("portal.announcements"))


@bp.get("/student-requests")
@login_required
@roles_required("admin")
def student_requests():
    items=StudentRequest.query.order_by(StudentRequest.created_at.desc()).all()
    db.session.add(AuditLog(actor_id=current_user.id,action="student_requests.inbox_viewed",target=f"{len(items)} requests",ip_address=request.remote_addr));db.session.commit()
    return render_template("portal/student_requests.html",title="Student support",requests=items)


@bp.post("/student-requests/<int:request_id>")
@login_required
@roles_required("admin")
def update_student_request(request_id):
    item=StudentRequest.query.get_or_404(request_id);status=request.form.get("status", "open")
    if status not in {"open", "in_progress", "resolved"}:
        flash("Choose a valid request status.","error")
    else:
        item.status=status;item.admin_note=request.form.get("admin_note", "").strip() or None
        item.resolved_by=current_user.id if status=="resolved" else None
        db.session.add(AuditLog(actor_id=current_user.id,action="student_request.updated",target=f"{item.id}:{status}",ip_address=request.remote_addr));db.session.commit()
        flash("Student request updated.","success")
    return redirect(url_for("portal.student_requests"))
