import os
from flask import Blueprint, jsonify, request, g, send_from_directory, current_app
from app.services.dining_display_service import DiningDisplayService
from app.utils.auth_utils import login_required, admin_required
from app.extensions import db

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
@login_required
def recommend_dish(dish_id):
    success = service.recommend_dish(dish_id)
    if not success:
        return jsonify({'code': 'DINING_404_002', 'message': '菜品不存在', 'trace_id': g.trace_id}), 404
    return jsonify({'code': 0, 'message': '推荐成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.post('/dishes/<dish_id>/avoid')
@login_required
def avoid_dish(dish_id):
    success = service.avoid_dish(dish_id)
    if not success:
        return jsonify({'code': 'DINING_404_002', 'message': '菜品不存在', 'trace_id': g.trace_id}), 404
    return jsonify({'code': 0, 'message': '操作成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.post('/canteens')
@admin_required
def create_canteen():
    data = request.get_json(silent=True) or {}
    try:
        canteen = service.dining_repo.create_canteen(**{k: v for k, v in data.items() if v is not None})
        db.session.commit()
        return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': canteen.id}, 'trace_id': g.trace_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 'DINING_422_001', 'message': str(e), 'trace_id': g.trace_id}), 422


@dining_bp.put('/canteens/<canteen_id>')
@admin_required
def update_canteen(canteen_id):
    data = request.get_json(silent=True) or {}
    success = service.dining_repo.update_canteen(canteen_id, **{k: v for k, v in data.items() if v is not None})
    if not success:
        return jsonify({'code': 'DINING_404_001', 'message': '食堂不存在', 'trace_id': g.trace_id}), 404
    db.session.commit()
    return jsonify({'code': 0, 'message': '更新成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.delete('/canteens/<canteen_id>')
@admin_required
def delete_canteen(canteen_id):
    success = service.dining_repo.delete_canteen(canteen_id)
    if not success:
        return jsonify({'code': 'DINING_404_001', 'message': '食堂不存在', 'trace_id': g.trace_id}), 404
    db.session.commit()
    return jsonify({'code': 0, 'message': '删除成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.post('/canteens/<canteen_id>/stalls')
@admin_required
def create_stall(canteen_id):
    data = request.get_json(silent=True) or {}
    data['canteen_id'] = canteen_id
    try:
        stall = service.dining_repo.create_stall(**{k: v for k, v in data.items() if v is not None})
        db.session.commit()
        return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': stall.id}, 'trace_id': g.trace_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 'DINING_422_002', 'message': str(e), 'trace_id': g.trace_id}), 422


@dining_bp.put('/stalls/<stall_id>')
@admin_required
def update_stall(stall_id):
    data = request.get_json(silent=True) or {}
    success = service.dining_repo.update_stall(stall_id, **{k: v for k, v in data.items() if v is not None})
    if not success:
        return jsonify({'code': 'DINING_404_003', 'message': '档口不存在', 'trace_id': g.trace_id}), 404
    db.session.commit()
    return jsonify({'code': 0, 'message': '更新成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.delete('/stalls/<stall_id>')
@admin_required
def delete_stall(stall_id):
    success = service.dining_repo.delete_stall(stall_id)
    if not success:
        return jsonify({'code': 'DINING_404_003', 'message': '档口不存在', 'trace_id': g.trace_id}), 404
    db.session.commit()
    return jsonify({'code': 0, 'message': '删除成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.post('/dishes')
@admin_required
def create_dish():
    data = request.get_json(silent=True) or {}
    try:
        dish = service.dining_repo.create_dish(**{k: v for k, v in data.items() if v is not None})
        db.session.commit()
        return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': dish.id}, 'trace_id': g.trace_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 'DINING_422_004', 'message': str(e), 'trace_id': g.trace_id}), 422


@dining_bp.put('/dishes/<dish_id>')
@admin_required
def update_dish(dish_id):
    data = request.get_json(silent=True) or {}
    success = service.dining_repo.update_dish(dish_id, **{k: v for k, v in data.items() if v is not None})
    if not success:
        return jsonify({'code': 'DINING_404_002', 'message': '菜品不存在', 'trace_id': g.trace_id}), 404
    db.session.commit()
    return jsonify({'code': 0, 'message': '更新成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.delete('/dishes/<dish_id>')
@admin_required
def delete_dish(dish_id):
    success = service.dining_repo.delete_dish(dish_id)
    if not success:
        return jsonify({'code': 'DINING_404_002', 'message': '菜品不存在', 'trace_id': g.trace_id}), 404
    db.session.commit()
    return jsonify({'code': 0, 'message': '删除成功', 'data': {}, 'trace_id': g.trace_id}), 200


@dining_bp.get('/recommendations/daily')
def get_daily_recommendations():
    from app.services.recommendation_service import get_daily_recommendations as get_daily
    data = get_daily()
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/recommendations/weekly')
def get_weekly_recommendations():
    from app.services.recommendation_service import get_weekly_recommendations as get_weekly
    data = get_weekly()
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@dining_bp.get('/uploads/<folder>/<filename>')
def serve_upload(folder, filename):
    allowed_folders = {'canteen_img', 'dish_img', 'stall_img', 'submission_img', 'default_img'}
    if folder not in allowed_folders:
        return jsonify({'code': 'DINING_400_001', 'message': '不允许的目录', 'trace_id': g.trace_id}), 400
    data_dir = os.path.join(current_app.root_path, '..', 'data')
    return send_from_directory(os.path.join(data_dir, folder), filename)
