"""
文件名：app/repositories/review_repository.py
功能描述：菜品点评（用户生成评价）业务域的底层数据库访问封装。
作者：郝炫斌
"""

from app.entities.models import Review
from app.extensions import db


class ReviewRepository:
    """
    类职责：负责 reviews 表的所有底层 SQL 映射与数据持久化交互。
    使用场景：用户在菜品详情页或提交流水时发表针对具体餐品的评分与评语。
    依赖关系：依赖 SQLAlchemy 的 db.session。
    设计说明：严格遵循 Repository 规范，仅负责将评价数据写入 session 缓存队列，不执行 commit 提交。
    """

    def create_review(
        self,
        dish_id: str,
        user_id: str,
        rating: float,
        comment: str
    ) -> Review:
        """
        功能描述：在 reviews 表中插入一条新的用户菜品评价记录。
        参数说明：
            dish_id: 关联的菜品唯一标识 (String)。
            user_id: 发表评价的用户唯一标识 (UUID String)。
            rating: 用户评定的星级分数（Float，例如 4.5）。
            comment: 用户填写的文本评论内容。
        返回值说明：
            返回插入整行后对应的 Review ORM 模型对象，包含底层自动生成的唯一主键 id。
        使用示例：
            new_review = repo.create_review("dish-001", "user-uuid-abc", 4.8, "阿姨今天给肉给得很实在！")
        """
        new_review = Review(
            dish_id=dish_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        db.session.flush()
        db.session.commit()
        return new_review

    def get_reviews_by_dish(self, dish_id: str) -> list[Review]:
        """
        功能描述：根据菜品 ID 查询所有评价（按创建时间倒序）。
        参数说明：
            dish_id: 目标菜品的唯一标识。
        返回值说明：
            返回符合条件的 Review 模型对象列表。
        """
        return (
            db.session.query(Review)
            .filter(Review.dish_id == dish_id)
            .order_by(Review.created_at.desc())
            .all()
        )