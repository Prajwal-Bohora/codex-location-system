from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models import User
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
