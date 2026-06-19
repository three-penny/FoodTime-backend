import pytest
from app.extensions import db
from app.entities.models import User


class TestSuperadmin:
    def test_list_users(self, client, superadmin_headers):
        resp = client.get('/api/v1/superadmin/users', headers=superadmin_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'items' in data['data']
        assert data['data']['total'] >= 1

    def test_list_users_not_superadmin(self, client, admin_headers):
        resp = client.get('/api/v1/superadmin/users', headers=admin_headers)
        assert resp.status_code == 403

    def test_change_user_role(self, client, superadmin_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if not user:
                pytest.skip("testuser not found")
            uid = user.id
        resp = client.put(f'/api/v1/superadmin/users/{uid}/role', json={
            'role': 'admin',
        }, headers=superadmin_headers)
        data = resp.get_json()
        assert resp.status_code == 200, f'change role failed: {data}'
        assert data['data']['role'] == 'admin'

    def test_change_user_role_invalid(self, client, superadmin_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if not user:
                pytest.skip("testuser not found")
            uid = user.id
        resp = client.put(f'/api/v1/superadmin/users/{uid}/role', json={
            'role': 'invalid_role',
        }, headers=superadmin_headers)
        assert resp.status_code == 422

    def test_set_user_status_banned(self, client, superadmin_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if not user:
                pytest.skip("testuser not found")
            uid = user.id
        resp = client.put(f'/api/v1/superadmin/users/{uid}/status', json={
            'status': 'banned',
        }, headers=superadmin_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['data']['account_status'] == 'banned'

    def test_set_user_status_active(self, client, superadmin_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if not user:
                pytest.skip("testuser not found")
            uid = user.id
        resp = client.put(f'/api/v1/superadmin/users/{uid}/status', json={
            'status': 'active',
        }, headers=superadmin_headers)
        assert resp.status_code == 200

    def test_change_password(self, client, superadmin_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if not user:
                pytest.skip("testuser not found")
            uid = user.id
        resp = client.put(f'/api/v1/superadmin/users/{uid}/password', json={
            'password': 'newpassword123',
        }, headers=superadmin_headers)
        data = resp.get_json()
        assert resp.status_code == 200, f'change password failed: {data}'

    def test_change_password_short(self, client, superadmin_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if not user:
                pytest.skip("testuser not found")
            uid = user.id
        resp = client.put(f'/api/v1/superadmin/users/{uid}/password', json={
            'password': '12',
        }, headers=superadmin_headers)
        assert resp.status_code == 422

    def test_get_dashboard(self, client, superadmin_headers):
        resp = client.get('/api/v1/superadmin/dashboard', headers=superadmin_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'user_count' in data['data']

    def test_get_audit_logs(self, client, superadmin_headers):
        resp = client.get('/api/v1/superadmin/logs', headers=superadmin_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'items' in data['data']
