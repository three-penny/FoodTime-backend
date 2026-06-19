import io
import uuid
import pytest
from app.extensions import db
from app.entities.models import Dish, Stall, Canteen


class TestDining:
    def test_get_canteens(self, client, seeded_canteen):
        resp = client.get('/api/v1/canteens')
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data['data']) >= 1
        assert any(c['id'] == 'test_canteen' for c in data['data'])

    def test_get_canteen_by_id(self, client, seeded_canteen):
        resp = client.get('/api/v1/canteens/test_canteen')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['data']['name'] == '测试食堂'

    def test_get_canteen_not_found(self, client):
        resp = client.get('/api/v1/canteens/nonexistent')
        assert resp.status_code == 404

    def test_get_canteen_spots(self, client, seeded_canteen):
        resp = client.get('/api/v1/canteens/spots')
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data['data']) >= 1

    def test_get_stalls(self, client, seeded_canteen):
        resp = client.get('/api/v1/canteens/test_canteen/stalls')
        data = resp.get_json()
        assert resp.status_code == 200
        assert any(s['id'] == 'test_canteen-测试档口' for s in data['data'])

    def test_get_dishes_by_canteen(self, client, seeded_canteen, seeded_dish):
        resp = client.get('/api/v1/canteens/test_canteen/dishes')
        data = resp.get_json()
        assert resp.status_code == 200
        names = [d['name'] for d in data['data']]
        assert '测试菜品' in names

    def test_get_dish_by_id(self, client, seeded_dish):
        resp = client.get(f'/api/v1/dishes/{seeded_dish.id}')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['data']['name'] == '测试菜品'

    def test_get_dish_not_found(self, client):
        resp = client.get('/api/v1/dishes/nonexistent')
        assert resp.status_code == 404

    def test_get_rankings(self, client, seeded_dish):
        resp = client.get('/api/v1/rankings')
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data['data']) >= 1

    def test_get_top_dishes(self, client, seeded_dish):
        resp = client.get('/api/v1/dishes/top')
        data = resp.get_json()
        assert resp.status_code == 200
        assert len(data['data']) >= 1

    def test_create_canteen(self, client, admin_headers):
        resp = client.post('/api/v1/canteens', json={
            'id': 'new_canteen',
            'name': '新食堂',
            'short_name': '新',
            'location': '新位置',
        }, headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 201
        assert data['data']['id'] == 'new_canteen'

    def test_create_canteen_not_admin(self, client, user_headers):
        resp = client.post('/api/v1/canteens', json={
            'id': 'new_canteen',
            'name': '新食堂',
        }, headers=user_headers)
        assert resp.status_code == 403

    def test_update_canteen(self, client, seeded_canteen, admin_headers):
        resp = client.put('/api/v1/canteens/test_canteen', json={
            'name': '已更新食堂',
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_delete_canteen(self, client, seeded_canteen, admin_headers):
        resp = client.delete('/api/v1/canteens/test_canteen', headers=admin_headers)
        assert resp.status_code == 200

    def test_create_stall(self, client, seeded_canteen, admin_headers):
        resp = client.post('/api/v1/canteens/test_canteen/stalls', json={
            'id': 'test_canteen-新档口',
            'name': '新档口',
        }, headers=admin_headers)
        data = resp.get_json()
        assert resp.status_code == 201
        assert data['data']['id'] == 'test_canteen-新档口'

    def test_update_stall(self, client, seeded_canteen, admin_headers):
        resp = client.put('/api/v1/stalls/test_canteen-测试档口', json={
            'name': '已更新档口',
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_delete_stall(self, client, seeded_canteen, admin_headers):
        resp = client.delete('/api/v1/stalls/test_canteen-测试档口', headers=admin_headers)
        assert resp.status_code == 200

    def test_create_dish_without_id(self, client, seeded_canteen, admin_headers):
        stall_id = 'test_canteen-测试档口'
        payload = {
            'stall_id': stall_id,
            'canteen_id': 'test_canteen',
            'name': '新菜品_无ID',
            'price': 15.0,
            'rating': 4.0,
            'description': '自动生成ID的菜品',
            'value_note': '好吃',
        }
        response = client.post('/api/v1/dishes', json=payload, headers=admin_headers)
        data = response.get_json()
        assert response.status_code == 201, f'Failed to create dish without id: {data}'
        assert data['code'] == 0
        dish_id = data['data']['id']
        assert dish_id is not None
        with client.application.app_context():
            dish = db.session.get(Dish, dish_id)
            assert dish is not None
            assert dish.name == '新菜品_无ID'

    def test_create_dish_with_id(self, client, seeded_canteen, admin_headers):
        dish_id = 'test_canteen-特定ID菜品'
        payload = {
            'id': dish_id,
            'stall_id': 'test_canteen-测试档口',
            'canteen_id': 'test_canteen',
            'name': '有ID的菜品',
            'price': 20.0,
            'rating': 5.0,
            'description': '手动指定ID',
            'value_note': '超赞',
        }
        response = client.post('/api/v1/dishes', json=payload, headers=admin_headers)
        data = response.get_json()
        assert response.status_code == 201
        assert data['data']['id'] == dish_id

    def test_create_dish_not_admin(self, client, seeded_canteen, user_headers):
        resp = client.post('/api/v1/dishes', json={
            'stall_id': 'test_canteen-测试档口',
            'canteen_id': 'test_canteen',
            'name': '未授权菜品',
            'price': 10.0,
        }, headers=user_headers)
        assert resp.status_code == 403

    def test_update_dish(self, client, seeded_dish, admin_headers):
        resp = client.put(f'/api/v1/dishes/{seeded_dish.id}', json={
            'name': '已更新菜品',
            'price': 99.0,
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_delete_dish(self, client, seeded_dish, admin_headers):
        resp = client.delete(f'/api/v1/dishes/{seeded_dish.id}', headers=admin_headers)
        assert resp.status_code == 200

    def test_delete_dish_not_found(self, client, admin_headers):
        resp = client.delete('/api/v1/dishes/nonexistent', headers=admin_headers)
        assert resp.status_code == 404

    def test_recommend_dish(self, client, seeded_dish, user_headers, app):
        resp = client.post(f'/api/v1/dishes/{seeded_dish.id}/recommend', headers=user_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 0
        with app.app_context():
            dish = db.session.get(Dish, seeded_dish.id)
            assert dish.recommend_votes == 11

    def test_avoid_dish(self, client, seeded_dish, user_headers):
        resp = client.post(f'/api/v1/dishes/{seeded_dish.id}/avoid', headers=user_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 0

    def test_upload_image(self, client, admin_headers):
        resp = client.post('/api/v1/uploads/dish_img', data={
            'file': (io.BytesIO(b'fake-image-data'), 'test.png'),
        }, headers={'Authorization': admin_headers['Authorization']},
           content_type='multipart/form-data')
        if resp.status_code == 201:
            data = resp.get_json()
            assert 'url' in data['data']

    def test_get_daily_recommendations(self, client):
        resp = client.get('/api/v1/recommendations/daily')
        data = resp.get_json()
        assert resp.status_code == 200

    def test_get_weekly_recommendations(self, client):
        resp = client.get('/api/v1/recommendations/weekly')
        data = resp.get_json()
        assert resp.status_code == 200
