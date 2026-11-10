import re
import unittest
from app import create_app
from extensions import db
from models import Role, User


class ApplicationSmokeTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING":True, "WTF_CSRF_ENABLED":False, "SQLALCHEMY_DATABASE_URI":"sqlite://", "INITIAL_ADMIN_SETUP_TOKEN":"test-setup-token"})
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            for name in ("super_admin", "admin", "teacher", "driver", "student"):
                db.session.add(Role(name=name))
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_and_setup_available_before_first_admin(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/setup").status_code, 200)

    def test_login_and_role_protected_location_api(self):
        with self.app.app_context():
            role = Role.query.filter_by(name="teacher").one()
            user = User(phone="5551000", full_name="Teacher Example", role=role)
            user.set_password("demo-password-123")
            db.session.add(user)
            db.session.commit()
        self.assertEqual(self.client.post("/login", data={"phone":"5551000", "password":"demo-password-123"}).status_code, 302)
        self.assertEqual(self.client.get("/api/location/drivers").status_code, 403)

    def test_setup_creates_first_super_admin_once(self):
        page = self.client.get("/setup")
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)
        response = self.client.post("/setup", data={"csrf_token":token, "setup_token":"test-setup-token", "full_name":"First Admin", "phone":"5552000", "password":"long-demo-password"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/setup").status_code, 403)


if __name__ == "__main__":
    unittest.main()
