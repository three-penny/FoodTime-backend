import uuid
import pytest
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.entities.models import User


class TestAuth:
    def test_register_success(self, client, mock_redis):
        email = f'test_{uuid.uuid4().hex[:8]}@test.com'
        mock_redis.setex(f'verification_code:{email}', 300, '123456')
        resp = client.post('/api/v1/auth/register', json={
            'email': email,
            'password': '123456',
            'nickname': f'用户_{uuid.uuid4().hex[:6]}',
            'verification_code': '123456',
        })
        data = resp.get_json()
        assert resp.status_code == 201, f'register failed: {data}'
        assert data['code'] == 0
        assert data['data']['email'] == email
        assert data['data']['role'] == 'user'

    def test_register_missing_fields(self, client):
        resp = client.post('/api/v1/auth/register', json={})
        assert resp.status_code == 422

    def test_register_duplicate_email(self, client, mock_redis, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
        email = user.email if user else 'testuser@test.com'
        resp = client.post('/api/v1/auth/register', json={
            'email': email,
            'password': '123456',
            'nickname': '另一个用户',
            'verification_code': '123456',
        })
        assert resp.status_code == 422

    def test_register_wrong_code(self, client, mock_redis):
        email = f'wrong_{uuid.uuid4().hex[:8]}@test.com'
        mock_redis.setex(f'verification_code:{email}', 300, '654321')
        resp = client.post('/api/v1/auth/register', json={
            'email': email,
            'password': '123456',
            'nickname': '验证码错误用户',
            'verification_code': '000000',
        })
        assert resp.status_code == 422

    def test_login_success(self, client, app):
        with app.app_context():
            u = User(
                id=str(uuid.uuid4()),
                account='loginuser',
                email='loginuser@test.com',
                password_hash=generate_password_hash('testpass'),
                nickname='登录测试',
                role='user',
                account_status='active',
            )
            db.session.add(u)
            db.session.commit()
            uid = u.id
        resp = client.post('/api/v1/auth/login', json={
            'login_id': 'loginuser',
            'password': 'testpass',
        })
        data = resp.get_json()
        assert resp.status_code == 200, f'login failed: {data}'
        assert data['code'] == 0
        assert 'token' in data['data']

    def test_login_wrong_password(self, client):
        resp = client.post('/api/v1/auth/login', json={
            'login_id': 'testuser',
            'password': 'wrongpass',
        })
        assert resp.status_code == 401

    def test_login_empty_fields(self, client):
        resp = client.post('/api/v1/auth/login', json={'login_id': '', 'password': ''})
        data = resp.get_json()
        assert data['code'] == 'AUTH_422_005'

    def test_send_code_invalid_email(self, client):
        resp = client.post('/api/v1/auth/send-code', json={'email': 'notanemail'})
        assert resp.status_code == 422

    def test_update_profile(self, client, user_headers):
        resp = client.put('/api/v1/auth/profile', json={
            'nickname': '新昵称',
        }, headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200, f'update profile failed: {data}'
        assert data['code'] == 0
        assert data['data']['nickname'] == '新昵称'

    def test_update_profile_no_auth(self, client):
        resp = client.put('/api/v1/auth/profile', json={'nickname': '新昵称'})
        assert resp.status_code == 401

    def test_invite_code_generate(self, client, admin_headers):
        resp = client.post('/api/v1/auth/invite-code/generate', headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 200, f'invite code gen failed: {data}'
        assert data['code'] == 0
        assert len(data['data']['code']) == 6

    def test_invite_code_not_admin(self, client, user_headers):
        resp = client.post('/api/v1/auth/invite-code/generate', headers=user_headers)
        assert resp.status_code == 403

    def test_invite_code_get(self, client, admin_headers):
        resp = client.get('/api/v1/auth/invite-code', headers=admin_headers)
        assert resp.status_code == 200
