import uuid
import pytest
from app.extensions import db
from app.entities.models import Rant


class TestRants:
    def test_create_rant(self, client, user_headers):
        resp = client.post('/api/v1/rants', json={
            'canteenName': '测试食堂',
            'author': 'testuser',
            'content': '排队太久了！',
            'tag': '吐槽',
        }, headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 201
        assert data['code'] == 0

    def test_create_rant_no_auth(self, client):
        resp = client.post('/api/v1/rants', json={
            'canteenName': '测试食堂',
            'content': '吐槽内容',
        })
        assert resp.status_code == 401

    def test_get_rants_without_auth(self, client):
        resp = client.get('/api/v1/rants')
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'data' in data

    def test_get_rants_with_auth(self, client, user_headers):
        resp = client.get('/api/v1/rants', headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200

    def test_get_rants_by_status(self, client, admin_headers):
        resp = client.get('/api/v1/rants?status=pending', headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 200

    def test_edit_rant(self, client, user_headers, app):
        with app.app_context():
            existing = db.session.query(Rant).filter_by(author_account='testuser').first()
            if not existing:
                pytest.skip("No rant from testuser")
            rid = existing.id
        resp = client.put(f'/api/v1/rants/{rid}', json={
            'content': '已编辑的吐槽内容',
        }, headers=user_headers)
        assert resp.status_code == 200

    def test_edit_rant_not_admin(self, client, user_headers):
        resp = client.put('/api/v1/rants/nonexistent', json={
            'content': 'test',
        }, headers=user_headers)
        assert resp.status_code == 403

    def test_audit_rant(self, client, admin_headers, app):
        with app.app_context():
            rant = Rant(
                id=str(uuid.uuid4()),
                canteen_name='测试食堂',
                author_account='testuser',
                content='待审核吐槽',
                tag='吐槽',
                status='pending',
            )
            db.session.add(rant)
            db.session.commit()
            rid = rant.id
        resp = client.put(f'/api/v1/rants/{rid}/audit', json={
            'status': 'approved',
            'reason': '内容合规',
            'auditor': 'admin',
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_audit_rant_not_admin(self, client, user_headers):
        resp = client.put('/api/v1/rants/some-id/audit', json={
            'status': 'approved',
            'reason': 'test',
            'auditor': 'testuser',
        }, headers=user_headers)
        assert resp.status_code == 403
