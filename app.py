import os
import hmac
from pathlib import Path
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import event
from sqlalchemy.engine import Engine
from config import Config
from extensions import db, login_manager, csrf

@event.listens_for(Engine,"connect")
def _sqlite_fk(dbapi_connection, connection_record):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cur=dbapi_connection.cursor();cur.execute("PRAGMA foreign_keys=ON");cur.close()

def create_app(config_override=None):
    app=Flask(__name__,instance_relative_config=True)
    app.config.from_object(Config)
    if config_override: app.config.update(config_override)
    Path(app.instance_path).mkdir(parents=True,exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True,exist_ok=True)
    db.init_app(app);login_manager.init_app(app);csrf.init_app(app)
    from models import User,Role
    from routes.auth import bp as auth_bp
    from routes.super_admin import bp as super_bp
    from routes.hod import bp as hod_bp
    from routes.teacher import bp as teacher_bp
    from routes.driver import bp as driver_bp
    from routes.student import bp as student_bp
    from routes.location import bp as location_bp
    for bp in (auth_bp,super_bp,hod_bp,teacher_bp,driver_bp,student_bp,location_bp):app.register_blueprint(bp)
    @login_manager.user_loader
    def load_user(user_id):return db.session.get(User,int(user_id))
    @app.get("/")
    def home():
        if current_user.is_authenticated:
            endpoints={"super_admin":"super_admin.dashboard","admin":"hod.dashboard","teacher":"teacher.dashboard","driver":"driver.dashboard","student":"student.dashboard"}
            return redirect(url_for(endpoints.get(current_user.role_name,"auth.login")))
        return render_template("home.html")
    @app.get("/setup")
    def setup_page():
        if not app.config.get("INITIAL_ADMIN_SETUP_TOKEN"):
            return "Initial setup is disabled until INITIAL_ADMIN_SETUP_TOKEN is configured.",503
        if User.query.join(Role).filter(Role.name=="super_admin").first():return "Initial setup is already complete.",403
        return render_template("setup.html")
    @app.post("/setup")
    def setup():
        setup_token=app.config.get("INITIAL_ADMIN_SETUP_TOKEN", "")
        if not setup_token or not hmac.compare_digest(request.form.get("setup_token", ""),setup_token):
            return "Invalid or missing initial setup token.",403
        if User.query.join(Role).filter(Role.name=="super_admin").first():return "Initial setup is already complete.",403
        from flask_wtf.csrf import validate_csrf
        try:validate_csrf(request.form.get("csrf_token"))
        except Exception:return "Invalid form token",400
        name=request.form.get("full_name", "").strip();phone=request.form.get("phone", "").strip();password=request.form.get("password", "")
        if not name or not phone or len(password)<12 or User.query.filter_by(phone=phone).first():
            flash("Enter a name, unique phone number, and password of at least 12 characters.","error");return render_template("setup.html"),400
        role=Role.query.filter_by(name="super_admin").first();user=User(full_name=name,phone=phone,role=role);user.set_password(password);db.session.add(user);db.session.commit()
        from flask_login import login_user
        login_user(user);flash("Super Admin created. Keep this account secure.","success");return redirect(url_for("home"))
    @app.get("/uploads/<path:filename>")
    @login_required
    def uploads(filename):
        from flask import send_from_directory
        from models import StudentProfile
        profile=StudentProfile.query.filter_by(id_photo=filename).first()
        if current_user.role_name not in ("admin","super_admin") and (not profile or profile.user_id!=current_user.id):return "Forbidden",403
        return send_from_directory(app.config["UPLOAD_FOLDER"],filename)
    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith("/api/"):return jsonify(error="Permission denied."),403
        return render_template("error.html",code=403,message="You do not have permission to view this page."),403
    @app.errorhandler(413)
    def too_large(e):return render_template("error.html",code=413,message="Upload too large. Maximum image size is 5 MB."),413
    with app.app_context():
        db.create_all()
        for name in ("super_admin","admin","teacher","driver","student"):
            if not Role.query.filter_by(name=name).first():db.session.add(Role(name=name))
        db.session.commit()
    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "0") == "1"
    )
