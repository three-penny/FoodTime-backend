from app.repositories.review_repository import ReviewRepository
from app.services.points_service import PointsService


class ReviewService:
    def __init__(self, repository=None, points_service=None):
        self.repository = repository or ReviewRepository()
        self.points_service = points_service or PointsService()

    def create_review(self, dish_id, user_id, rating, comment):
        if not dish_id or not user_id:
            raise ValueError('菜品ID和用户ID不能为空。')
        if not rating or not (1 <= float(rating) <= 5):
            raise ValueError('评分必须在 1 到 5 之间。')
        if not comment or not comment.strip():
            raise ValueError('评论内容不能为空。')

        review = self.repository.create_review(
            dish_id=dish_id,
            user_id=user_id,
            rating=float(rating),
            comment=comment.strip(),
        )
        from app.extensions import db
        db.session.commit()

        try:
            self.points_service.add_points(user_id, 3, '发表菜品评价', 'review')
        except Exception as e:
            pass

        return {
            'id': review.id,
            'dishId': review.dish_id,
            'rating': review.rating,
            'comment': review.comment,
            'reviewer': '匿名同学',
            'createdAt': review.created_at.strftime('%Y-%m-%d %H:%M') if review.created_at else '',
        }
