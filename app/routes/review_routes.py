"""
文件名：app/routes/review_routes.py
功能描述：菜品点评相关路由，处理评价创建与查询请求。
作者：FoodTime Backend Team
创建时间：2026-05-24
"""
from flask import Blueprint, request, jsonify, g
from app.services.review_service import ReviewService

review_bp = Blueprint('review', __name__, url_prefix='/api/v1/reviews')


@review_bp.get('')
def list_reviews():
    """
    接口说明：查询指定菜品的评价列表。
    权限要求：需要用户登录。
    请求参数：dish_id（必填，菜品 ID）。
    返回说明：返回该菜品的评价记录列表。
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
def create_review():
    """
    接口说明：创建菜品评价。
    权限要求：需要用户登录。
    请求参数（JSON）：
        dish_id: 菜品 ID（必填）。
        user_id: 评价用户 ID（必填，UUID）。
        rating: 星级评分（必填，1-5）。
        comment: 评论内容（必填）。
    返回说明：返回创建成功的评价记录。
    """
    data = request.get_json(silent=True) or {}

    service = ReviewService()

    try:
        review = service.create_review(
            dish_id=data.get('dish_id', ''),
            user_id=data.get('user_id', ''),
            rating=float(data.get('rating', 0)),
            comment=data.get('comment', ''),
        )
        return jsonify({
            'code': 0,
            'message': '点评成功。',
            'data': review,
            'trace_id': g.trace_id,
        }), 201
    except (ValueError, TypeError) as e:
        return jsonify({
            'code': 'REVIEW_422_002',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422
