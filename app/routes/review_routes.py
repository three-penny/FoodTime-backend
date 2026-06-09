"""
文件名：app/routes/review_routes.py
功能描述：菜品点评相关路由，处理评价创建、查询与审核请求。
作者：FoodTime Backend Team
创建时间：2026-05-24
"""
from flask import Blueprint, request, jsonify, g
from app.services.review_service import ReviewService
from app.utils.auth_utils import login_required, admin_required

review_bp = Blueprint('review', __name__, url_prefix='/api/v1/reviews')


@review_bp.get('/admin')
@admin_required
def list_all_reviews():
    """
    接口说明：查询全部评价（管理员审核台专用）。
    权限要求：需要管理员登录。
    返回说明：返回全部评价记录列表（含待审/已通过/已驳回）。
    """
    service = ReviewService()
    reviews = service.get_all_reviews()

    return jsonify({
        'code': 0,
        'message': 'success',
        'data': reviews,
        'trace_id': g.trace_id,
    }), 200


@review_bp.get('')
def list_reviews():
    """
    接口说明：查询指定菜品的已审核通过评价列表。
    权限要求：需要用户登录。
    请求参数：dish_id（必填，菜品 ID）。
    返回说明：返回该菜品的已审核通过评价记录列表。
    """
    dish_id = request.args.get('dish_id', '')
    if not dish_id:
        return jsonify({
            'code': 'REVIEW_422_001',
            'message': '菜品 ID 不能为空。',
            'trace_id': g.trace_id,
        }), 422

    service = ReviewService()
    reviews = service.get_reviews_by_dish(dish_id)

    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'items': reviews,
            'total': len(reviews),
        },
        'trace_id': g.trace_id,
    }), 200


@review_bp.post('')
@login_required
def create_review():
    """
    接口说明：创建菜品评价（提交后待管理员审核）。
    权限要求：需要用户登录（从 JWT 获取用户 ID）。
    请求参数（JSON）：
        dish_id: 菜品 ID（必填）。
        rating: 星级评分（必填，1-5）。
        comment: 评论内容（必填）。
    返回说明：返回创建成功的评价记录。
    """
    data = request.get_json(silent=True) or {}

    service = ReviewService()

    try:
        review = service.create_review(
            dish_id=data.get('dish_id', ''),
            user_id=g.user_id,
            rating=float(data.get('rating', 0)),
            comment=data.get('comment', ''),
        )
        return jsonify({
            'code': 0,
            'message': '点评已提交，审核通过后将公开展示。',
            'data': review,
            'trace_id': g.trace_id,
        }), 201
    except (ValueError, TypeError) as e:
        return jsonify({
            'code': 'REVIEW_422_002',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@review_bp.put('/<review_id>/audit')
@admin_required
def audit_review(review_id):
    """
    接口说明：审核评价（管理员通过或驳回）。
    权限要求：需要管理员登录。
    请求参数（JSON）：
        status: 审核结果（approved / rejected，必填）。
        reason: 审核意见（必填）。
    返回说明：返回审核结果。
    """
    data = request.get_json(silent=True) or {}

    service = ReviewService()

    try:
        service.audit_review(
            review_id=review_id,
            status=data.get('status', ''),
            audit_reason=data.get('reason', ''),
        )
        return jsonify({
            'code': 0,
            'message': '审核完成',
            'data': {},
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'REVIEW_422_003',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422
