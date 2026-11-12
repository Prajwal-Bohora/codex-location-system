from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models import User, AuditLog
from extensions import db

bp = Blueprint("auth", __name__)

@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("login.html")

@bp.post("/login")
def login_post():
    phone = request.form.get("phone", "").strip()
    user = User.query.filter_by(phone=phone).first()
    if not user or not user.active or not user.check_password(request.form.get("password", "")):
        flash("Phone number or password is incorrect.", "error")
        return render_template("login.html"), 401
    login_user(user, remember=bool(request.form.get("remember")))
    return redirect(url_for("home"))

@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))

@bp.route("/account/password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password=request.form.get("current_password", "")
        new_password=request.form.get("new_password", "")
        confirm=request.form.get("confirm_password", "")
        if not current_user.check_password(current_password):
            flash("Your current password is incorrect.","error")
        elif len(new_password)<12:
            flash("Choose a new password with at least 12 characters.","error")
        elif new_password!=confirm:
            flash("The new passwords do not match.","error")
        else:
            current_user.set_password(new_password)
            db.session.add(AuditLog(actor_id=current_user.id,action="account.password_changed",ip_address=request.remote_addr))
            db.session.commit()
            flash("Your password has been changed.","success")
            return redirect(url_for("home"))
    return render_template("change_password.html",title="Change password")
