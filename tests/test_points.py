import uuid
import pytest
from app.extensions import db
from app.entities.models import User


class TestPoints:
    def test_get_points(self, client, user_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
        if not user:
            pytest.skip("testuser not found")
        resp = client.get(f'/api/v1/points?userId={user.id}', headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'currentPoints' in data['data']

    def test_get_points_missing_user_id(self, client, user_headers):
        resp = client.get('/api/v1/points', headers=user_headers)
        assert resp.status_code == 400

    def test_checkin(self, client, user_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
        if not user:
            pytest.skip("testuser not found")
        resp = client.post('/api/v1/points/checkin', json={
            'userId': user.id,
        }, headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['code'] == 0

    def test_checkin_duplicate(self, client, user_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
        if not user:
            pytest.skip("testuser not found")
        uid = user.id
        client.post('/api/v1/points/checkin', json={'userId': uid}, headers=user_headers)
        resp = client.post('/api/v1/points/checkin', json={'userId': uid}, headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['data']['checkedIn'] is False

    def test_consume_points(self, client, user_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if user:
                user.current_points = 100
                db.session.commit()
                uid = user.id
        if not user:
            pytest.skip("testuser not found")
        resp = client.post('/api/v1/points/consume', json={
            'userId': uid,
            'amount': 30,
            'reason': '兑换优惠券',
        }, headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200, f'consume failed: {data}'
        assert data['data']['currentPoints'] == 70

    def test_consume_insufficient_points(self, client, user_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
            if user:
                user.current_points = 5
                db.session.commit()
                uid = user.id
        if not user:
            pytest.skip("testuser not found")
        resp = client.post('/api/v1/points/consume', json={
            'userId': uid,
            'amount': 100,
            'reason': '消费过多',
        }, headers=user_headers)
        assert resp.status_code == 422

    def test_get_points_history(self, client, user_headers, app):
        with app.app_context():
            user = User.query.filter_by(account='testuser').first()
        if not user:
            pytest.skip("testuser not found")
        resp = client.get(f'/api/v1/points/history?userId={user.id}', headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert isinstance(data['data'], list)
