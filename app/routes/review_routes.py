from flask import Blueprint, jsonify, request, g
from app.services.review_service import ReviewService
from app.repositories.auth_repository import AuthRepository

review_bp = Blueprint('reviews', __name__, url_prefix='/api/v1')
review_service = ReviewService()
auth_repo = AuthRepository()


@review_bp.post('/reviews')
def create_review():
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', '')
    dish_id = data.get('dishId', '')
    rating = data.get('rating', 0)
    comment = data.get('comment', '')

    try:
        review = review_service.create_review(
            dish_id=dish_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )
        return jsonify({
            'code': 0,
            'message': '评价成功',
            'data': review,
            'trace_id': g.trace_id,
        }), 201
    except ValueError as e:
        return jsonify({
            'code': 'REVIEW_422_001',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422
