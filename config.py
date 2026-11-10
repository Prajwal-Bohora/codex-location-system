import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-before-deployment")
    INITIAL_ADMIN_SETUP_TOKEN = os.getenv("INITIAL_ADMIN_SETUP_TOKEN", "")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'midwest_app.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "instance" / "uploads"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
