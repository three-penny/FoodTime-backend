import uuid
import pytest
from app.extensions import db
from app.entities.models import Dish


class TestSubmissions:
    def test_create_submission(self, client, user_headers, mock_redis):
        resp = client.post('/api/v1/submissions', data={
            'dish_name': '用户提报菜品',
            'canteen_name': '测试食堂',
            'stall_name': '测试档口',
            'price': '18.0',
            'description': '用户提交的测试菜品',
            'submitter_account': 'testuser',
        }, headers={
            'Authorization': user_headers['Authorization'],
        })
        data = resp.get_json()
        assert resp.status_code == 201, f'create submission failed: {data}'
        assert data['code'] == 0
        assert data['data']['status'] == 'pending'

    def test_create_submission_missing_fields(self, client, user_headers):
        resp = client.post('/api/v1/submissions', data={
            'dish_name': '',
            'canteen_name': '',
        }, headers={
            'Authorization': user_headers['Authorization'],
        })
        data = resp.get_json()
        assert resp.status_code == 422

    def test_create_submission_no_auth(self, client):
        resp = client.post('/api/v1/submissions', data={
            'dish_name': '未登录提报',
            'canteen_name': '测试食堂',
            'stall_name': '测试档口',
            'submitter_account': 'testuser',
        })
        assert resp.status_code == 401

    def test_list_user_submissions(self, client, user_headers):
        resp = client.get('/api/v1/submissions?account=testuser', headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'items' in data['data']

    def test_list_all_submissions(self, client, admin_headers):
        resp = client.get('/api/v1/submissions', headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'items' in data['data']

    def test_admin_create_submission(self, client, seeded_canteen, admin_headers):
        resp = client.post('/api/v1/submissions/admin', json={
            'dish_name': '管理员创建菜品',
            'canteen_name': '测试食堂',
            'stall_name': '测试档口',
            'price': 25.0,
            'description': '管理员直接创建的菜品',
            'submitter_account': 'admin',
        }, headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 201, f'admin create failed: {data}'
        assert data['code'] == 0

    def test_admin_create_submission_creates_dish(self, client, seeded_canteen, admin_headers):
        resp = client.post('/api/v1/submissions/admin', json={
            'dish_name': '审核自动创建菜品',
            'canteen_name': '测试食堂',
            'stall_name': '测试档口',
            'price': 30.0,
        }, headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 201
        with client.application.app_context():
            dish = Dish.query.filter_by(name='审核自动创建菜品').first()
            assert dish is not None
            assert dish.stall_id is not None

    def test_audit_submission_approve(self, client, user_headers, admin_headers, seeded_canteen, mock_redis):
        resp = client.post('/api/v1/submissions', data={
            'dish_name': '待审核菜品',
            'canteen_name': '测试食堂',
            'stall_name': '测试档口',
            'price': '12.0',
            'submitter_account': 'testuser',
            'description': '等待审核',
        }, headers={
            'Authorization': user_headers['Authorization'],
        })
        data = resp.get_json()
        submission_id = data['data']['id']
        resp = client.put(f'/api/v1/submissions/{submission_id}/audit', json={
            'status': 'approved',
            'reason': '审核通过',
            'auditor': 'admin',
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_audit_submission_reject(self, client, user_headers, admin_headers, seeded_canteen, mock_redis):
        resp = client.post('/api/v1/submissions', data={
            'dish_name': '将被驳回的菜品',
            'canteen_name': '测试食堂',
            'stall_name': '测试档口',
            'price': '8.0',
            'submitter_account': 'testuser',
        }, headers={
            'Authorization': user_headers['Authorization'],
        })
        data = resp.get_json()
        submission_id = data['data']['id']
        resp = client.put(f'/api/v1/submissions/{submission_id}/audit', json={
            'status': 'rejected',
            'reason': '图片不清晰',
            'auditor': 'admin',
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_edit_submission(self, client, admin_headers):
        resp = client.get('/api/v1/submissions', headers=admin_headers)
        submissions = resp.get_json()['data'].get('items', [])
        if not submissions:
            pytest.skip("no submissions to edit")
        sid = submissions[0]['id']
        resp = client.put(f'/api/v1/submissions/{sid}', json={
            'dish_name': '已编辑的提报',
        }, headers=admin_headers)
        assert resp.status_code == 200
