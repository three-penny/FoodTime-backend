from flask import Blueprint, jsonify, request, g
from app.services.points_service import PointsService
from app.utils.auth_utils import login_required

points_bp = Blueprint('points', __name__, url_prefix='/api/v1')
points_service = PointsService()


@points_bp.get('/points')
@login_required
def get_points():
    user_id = request.args.get('userId', '')
    if not user_id:
        return jsonify({'code': 'POINTS_400_001', 'message': '缺少用户ID', 'trace_id': g.trace_id}), 400
    data = points_service.get_user_points(user_id)
    if not data:
        return jsonify({'code': 'POINTS_404_001', 'message': '用户不存在', 'trace_id': g.trace_id}), 404
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@points_bp.get('/points/history')
@login_required
def get_points_history():
    user_id = request.args.get('userId', '')
    if not user_id:
        return jsonify({'code': 'POINTS_400_001', 'message': '缺少用户ID', 'trace_id': g.trace_id}), 400
    data = points_service.get_points_history(user_id)
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@points_bp.post('/points/checkin')
@login_required
def daily_checkin():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', '')
    if not user_id:
        return jsonify({'code': 'POINTS_400_001', 'message': '缺少用户ID', 'trace_id': g.trace_id}), 400

    try:
        result = points_service.daily_checkin(user_id)
        return jsonify({
            'code': 0,
            'message': '签到成功' if result else '今天已签到',
            'data': {'checkedIn': result},
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'POINTS_422_001',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@points_bp.post('/points/consume')
@login_required
def consume_points():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', '')
    amount = data.get('amount', 0)
    reason = data.get('reason', '')

    if not user_id:
        return jsonify({'code': 'POINTS_400_001', 'message': '缺少用户ID', 'trace_id': g.trace_id}), 400

    try:
        result = points_service.consume_points(user_id, int(amount), reason)
        return jsonify({
            'code': 0,
            'message': '消费成功',
            'data': result,
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'POINTS_422_002',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422
