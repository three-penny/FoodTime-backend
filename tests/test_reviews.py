import uuid
import pytest
from app.extensions import db
from app.entities.models import Review


class TestReviews:
    def test_create_review(self, client, seeded_dish, user_headers):
        resp = client.post('/api/v1/reviews', json={
            'dish_id': seeded_dish.id,
            'rating': 4.0,
            'comment': '味道不错！',
        }, headers=user_headers)
        data = resp.get_json()
        assert resp.status_code == 201
        assert data['code'] == 0

    def test_create_review_invalid_rating(self, client, seeded_dish, user_headers):
        resp = client.post('/api/v1/reviews', json={
            'dish_id': seeded_dish.id,
            'rating': 6.0,
            'comment': '无效评分',
        }, headers=user_headers)
        assert resp.status_code == 422

    def test_create_review_no_auth(self, client, seeded_dish):
        resp = client.post('/api/v1/reviews', json={
            'dish_id': seeded_dish.id,
            'rating': 4.0,
            'comment': '未登录',
        })
        assert resp.status_code == 401

    def test_get_reviews_by_dish(self, client, seeded_review, seeded_dish):
        with client.application.app_context():
            dish_id = seeded_review.dish_id
        resp = client.get(f'/api/v1/reviews?dish_id={dish_id}')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['data']['total'] >= 1

    def test_get_reviews_missing_dish_id(self, client):
        resp = client.get('/api/v1/reviews')
        assert resp.status_code == 422

    def test_list_all_reviews_admin(self, client, seeded_review, admin_headers):
        resp = client.get('/api/v1/reviews/admin', headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data['data']) >= 1

    def test_list_all_reviews_not_admin(self, client, seeded_review, user_headers):
        resp = client.get('/api/v1/reviews/admin', headers=user_headers)
        assert resp.status_code == 403

    def test_audit_review_approve(self, client, seeded_review, admin_headers):
        resp = client.put(f'/api/v1/reviews/{seeded_review.id}/audit', json={
            'status': 'approved',
            'reason': '内容合规',
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_audit_review_reject(self, client, seeded_review, admin_headers):
        resp = client.put(f'/api/v1/reviews/{seeded_review.id}/audit', json={
            'status': 'rejected',
            'reason': '内容不合规',
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_audit_review_no_reason(self, client, seeded_review, admin_headers):
        resp = client.put(f'/api/v1/reviews/{seeded_review.id}/audit', json={
            'status': 'approved',
            'reason': '',
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_audit_review_not_admin(self, client, seeded_review, user_headers):
        resp = client.put(f'/api/v1/reviews/{seeded_review.id}/audit', json={
            'status': 'approved',
            'reason': '测试',
        }, headers=user_headers)
        assert resp.status_code == 403
