"""
文件名：app/services/review_service.py
功能描述：菜品点评业务编排层，负责评价创建与按菜品查询。
作者：FoodTime Backend Team
创建时间：2026-05-24
"""
import logging
from app.repositories.review_repository import ReviewRepository
from app.services.points_service import PointsService

logger = logging.getLogger(__name__)


class ReviewService:
    """菜品点评业务服务，编排评价创建、查询与审核流程。"""

    def __init__(self, repository: ReviewRepository | None = None, points_service=None):
        self.repository = repository or ReviewRepository()
        self.points_service = points_service or PointsService()

    def create_review(
        self,
        dish_id: str,
        user_id: str,
        rating: float,
        comment: str,
    ) -> dict:
        """
        创建菜品评价（提交后状态为 pending，需管理员审核）。
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
        from app.extensions import db
        db.session.commit()

        try:
            self.points_service.add_points(user_id, 3, '发表菜品评价', 'review')
        except Exception:
            pass

        return self._to_dict(review)

    def get_reviews_by_dish(self, dish_id: str) -> list[dict]:
        """查询指定菜品的已审核通过评价（按创建时间倒序）。"""
        reviews = self.repository.get_reviews_by_dish(dish_id)
        return [self._to_dict(r) for r in reviews]

    def get_all_reviews(self) -> list[dict]:
        """查询全部评价（管理员审核台使用），含用户昵称和菜品路径信息。"""
        reviews = self.repository.get_all_reviews()
        if not reviews:
            return []

        from app.extensions import db
        from app.entities.models import User, Dish, Stall, Canteen

        user_ids = list(set(r.user_id for r in reviews))
        dish_ids = list(set(r.dish_id for r in reviews))

        users = {u.id: u for u in db.session.query(User).filter(User.id.in_(user_ids)).all()}
        dishes = {d.id: d for d in db.session.query(Dish).filter(Dish.id.in_(dish_ids)).all()}
        stalls = {s.id: s for s in db.session.query(Stall).all()}
        canteens = {c.id: c for c in db.session.query(Canteen).all()}

        result = []
        for r in reviews:
            d = self._to_dict(r)
            u = users.get(r.user_id)
            d['reviewer_nickname'] = u.nickname if u else ''
            dish = dishes.get(r.dish_id)
            if dish:
                d['dish_name'] = dish.name
                stall = stalls.get(dish.stall_id)
                d['stall_name'] = stall.name if stall else ''
                canteen = canteens.get(dish.canteen_id)
                d['canteen_name'] = canteen.name if canteen else ''
            else:
                d['dish_name'] = ''
                d['stall_name'] = ''
                d['canteen_name'] = ''
            result.append(d)
        return result

    def audit_review(self, review_id: str, status: str, audit_reason: str) -> bool:
        """
        审核评价（通过/驳回）。
        参数说明：
            review_id: 评价 ID。
            status: 审核结果（approved / rejected）。
            audit_reason: 审核意见。
        """
        if status not in ('approved', 'rejected'):
            raise ValueError('审核状态只能是 approved 或 rejected。')
        if not audit_reason or not audit_reason.strip():
            raise ValueError('审核意见不能为空。')

        success = self.repository.update_review_audit_result(
            review_id=review_id,
            status=status,
            audit_reason=audit_reason.strip(),
        )
        if not success:
            raise ValueError('评价记录不存在。')
        from app.extensions import db
        db.session.commit()

        if status == 'approved':
            from app.entities.models import Review, Dish
            review = db.session.query(Review).filter(Review.id == review_id).first()
            if review:
                self._recalc_dish_rating(review.dish_id)
                dish = db.session.query(Dish).filter(Dish.id == review.dish_id).first()
                if dish:
                    self._recalc_canteen_rating(dish.canteen_id)

        return True

    def _recalc_dish_rating(self, dish_id: str) -> None:
        """根据最近 100 条已审核通过的评分重新计算菜品 rating。"""
        from app.extensions import db
        from app.entities.models import Review, Dish
        from sqlalchemy import func

        subq = (
            db.session.query(Review.rating)
            .filter(Review.dish_id == dish_id, Review.status == 'approved')
            .order_by(Review.created_at.desc())
            .limit(100)
            .subquery()
        )
        avg = db.session.query(func.avg(subq.c.rating)).scalar()
        new_rating = round(float(avg), 1) if avg else 0.0
        db.session.query(Dish).filter(Dish.id == dish_id).update(
            {'rating': new_rating}, synchronize_session=False
        )
        db.session.commit()

    def _recalc_canteen_rating(self, canteen_id: str) -> None:
        """根据该餐厅所有菜品最近 1000 条已审核通过的评分重新计算食堂 rating。"""
        from app.extensions import db
        from app.entities.models import Review, Dish, Canteen
        from sqlalchemy import func

        canteen_dish_ids = [
            d.id for d in db.session.query(Dish.id).filter(Dish.canteen_id == canteen_id).all()
        ]
        if not canteen_dish_ids:
            db.session.query(Canteen).filter(Canteen.id == canteen_id).update(
                {'rating': 0.0}, synchronize_session=False
            )
            db.session.commit()
            return

        subq = (
            db.session.query(Review.rating)
            .filter(
                Review.dish_id.in_(canteen_dish_ids),
                Review.status == 'approved',
            )
            .order_by(Review.created_at.desc())
            .limit(1000)
            .subquery()
        )
        avg = db.session.query(func.avg(subq.c.rating)).scalar()
        new_rating = round(float(avg), 1) if avg else 0.0
        db.session.query(Canteen).filter(Canteen.id == canteen_id).update(
            {'rating': new_rating}, synchronize_session=False
        )
        db.session.commit()

    def _to_dict(self, review) -> dict:
        return {
            'id': review.id,
            'dish_id': review.dish_id,
            'user_id': review.user_id,
            'rating': review.rating,
            'comment': review.comment,
            'status': review.status or 'pending',
            'audit_reason': review.audit_reason or '',
            'created_at': review.created_at.isoformat() if review.created_at else None,
            'updated_at': review.updated_at.isoformat() if review.updated_at else None,
        }
