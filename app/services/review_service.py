"""
文件名：app/services/review_service.py
功能描述：菜品点评业务编排层，负责评价创建与按菜品查询。
作者：FoodTime Backend Team
创建时间：2026-05-24
"""
import logging
from app.repositories.review_repository import ReviewRepository

logger = logging.getLogger(__name__)


class ReviewService:
    """菜品点评业务服务，编排评价创建与查询流程。"""

    def __init__(self, repository: ReviewRepository | None = None):
        self.repository = repository or ReviewRepository()

    def create_review(
        self,
        dish_id: str,
        user_id: str,
        rating: float,
        comment: str,
    ) -> dict:
        """
        创建菜品评价。
        参数说明：
            dish_id: 菜品 ID（必填）。
            user_id: 评价用户 ID（必填，UUID）。
            rating: 星级评分（必填，1-5）。
            comment: 评论内容（必填）。
        返回值说明：
            返回创建成功的评价记录字典。
        异常抛出：
            ValueError: 参数校验失败。
        """
        comment = comment.strip()
        rating = float(rating)

        if not dish_id:
            raise ValueError('菜品 ID 不能为空。')
        if not user_id:
            raise ValueError('用户 ID 不能为空。')
        if not (1 <= rating <= 5):
            raise ValueError('评分必须在 1 到 5 之间。')
        if not comment:
            raise ValueError('评论内容不能为空。')

        review = self.repository.create_review(
            dish_id=dish_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )

        return {
            'id': review.id,
            'dish_id': review.dish_id,
            'user_id': review.user_id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat() if review.created_at else None,
        }

    def get_reviews_by_dish(self, dish_id: str) -> list[dict]:
        """查询指定菜品的所有评价（按创建时间倒序）。"""
        reviews = self.repository.get_reviews_by_dish(dish_id)
        return [self._to_dict(r) for r in reviews]

    def _to_dict(self, review) -> dict:
        return {
            'id': review.id,
            'dish_id': review.dish_id,
            'user_id': review.user_id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat() if review.created_at else None,
            'updated_at': review.updated_at.isoformat() if review.updated_at else None,
        }
