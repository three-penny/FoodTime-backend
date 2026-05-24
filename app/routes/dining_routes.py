from flask import Blueprint, jsonify, request, g
from app.services.dining_display_service import DiningDisplayService

dining_bp = Blueprint('dining', __name__, url_prefix='/api/v1')

service = DiningDisplayService()


@dining_bp.get('/canteens')
def list_canteens():
    data = service.get_all_canteens()
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/canteens/<canteen_id>')
def get_canteen(canteen_id):
    data = service.get_canteen_by_id(canteen_id)
    if not data:
        return jsonify({'code': 'DINING_404_001', 'message': '食堂不存在', 'trace_id': g.trace_id}), 404
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/canteens/<canteen_id>/stalls')
def list_stalls(canteen_id):
    data = service.get_stalls_by_canteen(canteen_id)
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/canteens/<canteen_id>/dishes')
def list_canteen_dishes(canteen_id):
    data = service.get_dishes_by_canteen(canteen_id)
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/canteens/spots')
def list_canteen_spots():
    data = service.get_canteen_spots()
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/rankings')
def list_rankings():
    data = service.get_rankings()
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/dishes')
def list_dishes():
    limit = request.args.get('limit', 50, type=int)
    data = service.get_top_dishes(limit)
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/dishes/top')
def list_top_dishes():
    limit = request.args.get('limit', 10, type=int)
    data = service.get_top_dishes(limit)
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/dishes/<dish_id>')
def get_dish(dish_id):
    data = service.get_dish_by_id(dish_id)
    if not data:
        return jsonify({'code': 'DINING_404_002', 'message': '菜品不存在', 'trace_id': g.trace_id}), 404
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/dishes/<dish_id>/reviews')
def list_dish_reviews(dish_id):
    data = service.get_reviews_by_dish(dish_id)
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.post('/dishes/<dish_id>/recommend')
def recommend_dish(dish_id):
    success = service.recommend_dish(dish_id)
    if not success:
        return jsonify({'code': 'DINING_404_002', 'message': '菜品不存在', 'trace_id': g.trace_id}), 404
    return jsonify({'code': 0, 'message': '推荐成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.post('/dishes/<dish_id>/avoid')
def avoid_dish(dish_id):
    success = service.avoid_dish(dish_id)
    if not success:
        return jsonify({'code': 'DINING_404_002', 'message': '菜品不存在', 'trace_id': g.trace_id}), 404
    return jsonify({'code': 0, 'message': '操作成功', 'data': {}, 'trace_id': g.trace_id}), 200
