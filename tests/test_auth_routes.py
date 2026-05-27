import unittest

from werkzeug.security import generate_password_hash

from app import create_app
from app.entities.models import User
from app.extensions import db
from config import TestingConfig


class AuthRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            db.session.add(
                User(
                    account="admin",
                    password_hash=generate_password_hash("123456"),
                    nickname="Admin",
                    role="admin",
                    account_status="active",
                    current_points=0,
                    total_earned_points=0,
                    total_used_points=0,
                )
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_success(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"login_id": "admin", "password": "123456"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["account"], "admin")
        self.assertEqual(body["data"]["role"], "admin")
        self.assertNotIn("password_hash", body["data"])

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"login_id": "admin", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 401)
        body = response.get_json()
        self.assertEqual(body["code"], "AUTH_401_001")

    def test_unknown_route_returns_404_not_500(self):
        response = self.client.post("/api/v1/auth/missing")

        self.assertEqual(response.status_code, 404)
        body = response.get_json()
        self.assertEqual(body["code"], "HTTP_404")


if __name__ == "__main__":
    unittest.main()
