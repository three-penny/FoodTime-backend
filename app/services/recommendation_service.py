"""
文件名：app/services/recommendation_service.py
功能描述：每日/每周推荐刷新服务，通过 APScheduler 定时任务自动更新。
作者：FoodTime Backend Team
创建时间：2026-05-27
"""
import random
import logging
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.extensions import db
from app.entities.models import Dish, Canteen, Stall, Review, DailyRecommendation, WeeklyRecommendation
from sqlalchemy import func


def _img(url):
    return url or current_app.config.get('DEFAULT_IMG_URL', '/api/v1/uploads/default_img/default.jpg')

logger = logging.getLogger(__name__)

CST = timezone(timedelta(hours=8))


def refresh_daily_recommendations():
    """每日凌晨 0 点执行：随机选取均分 > 3.7 的 10 道菜品。"""
    logger.info('[DailyRec] 开始刷新每日推荐')

    candidates = (
        db.session.query(Dish, Canteen.name, Stall.name)
        .join(Canteen, Dish.canteen_id == Canteen.id)
        .outerjoin(Stall, Dish.stall_id == Stall.id)
        .filter(Dish.rating > 3.7)
        .all()
    )
    if not candidates:
        logger.warning('[DailyRec] 无符合条件的菜品 (rating > 3.7)，跳过刷新')
        return

    selected = random.sample(candidates, min(10, len(candidates)))

    DailyRecommendation.query.delete()
    for dish, canteen_name, stall_name in selected:
        item = DailyRecommendation(
            dish_id=dish.id,
            canteen_id=dish.canteen_id,
            dish_name=dish.name,
            canteen_name=canteen_name,
            stall_name=stall_name,
            price=dish.price,
            rating=dish.rating,
            image_url=dish.image_url,
            tags=dish.tags,
        )
        db.session.add(item)

    db.session.commit()
    logger.info('[DailyRec] 每日推荐刷新完成，共 %d 条', len(selected))


TARGET_RECOMMEND_COUNT = 10


def refresh_weekly_recommendations():
    """每周日凌晨 0 点执行：基于最近 200 条已审核评论，计算均分最高的前 10 道菜品。
    
    如果评论数据不足 10 条，剩余名额从评分 > 3.7 的菜品中随机补充。
    """
    logger.info('[WeeklyRec] 开始刷新每周推荐')

    # Step 1: 获取最近 200 条已审核评论的 ID（按创建时间降序）
    recent_review_ids = (
        db.session.query(Review.id)
        .filter(Review.status == 'approved')
        .order_by(Review.created_at.desc())
        .limit(200)
        .subquery()
    )

    # Step 2: 对这 200 条评论按菜品分组，计算均分和评论数
    dish_agg = (
        db.session.query(
            Review.dish_id,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count'),
        )
        .filter(Review.id.in_(recent_review_ids))
        .group_by(Review.dish_id)
        .subquery()
    )

    # Step 3: 关联菜品/食堂/档口信息，按均分降序取前 10
    review_rows = (
        db.session.query(
            dish_agg.c.dish_id,
            dish_agg.c.avg_rating,
            dish_agg.c.review_count,
            Dish.canteen_id,
            Dish.name.label('dish_name'),
            Dish.price,
            Dish.rating.label('dish_rating'),
            Dish.image_url,
            Dish.tags,
            Dish.description,
            Canteen.name.label('canteen_name'),
            Stall.name.label('stall_name'),
        )
        .join(Dish, dish_agg.c.dish_id == Dish.id)
        .join(Canteen, Dish.canteen_id == Canteen.id)
        .outerjoin(Stall, Dish.stall_id == Stall.id)
        .order_by(dish_agg.c.avg_rating.desc())
        .limit(TARGET_RECOMMEND_COUNT)
        .all()
    )

    # Step 4: 如果不足 10 个，从其他高评分菜品中随机补充
    existing_ids = {row.dish_id for row in review_rows}
    needed = TARGET_RECOMMEND_COUNT - len(review_rows)

    if needed > 0:
        logger.info('[WeeklyRec] 评论数据不足 %d 条，将从高评分菜品中随机补充 %d 条',
                     TARGET_RECOMMEND_COUNT, needed)

        fill_candidates = (
            db.session.query(
                Dish.id.label('dish_id'),
                Dish.canteen_id,
                Dish.name.label('dish_name'),
                Dish.price,
                Dish.rating.label('dish_rating'),
                Dish.image_url,
                Dish.tags,
                Dish.description,
                Dish.rating.label('avg_rating'),
                Canteen.name.label('canteen_name'),
                Stall.name.label('stall_name'),
            )
            .join(Canteen, Dish.canteen_id == Canteen.id)
            .outerjoin(Stall, Dish.stall_id == Stall.id)
            .filter(Dish.rating > 3.7, Dish.id.notin_(existing_ids))
            .all()
        )

        if fill_candidates:
            fill_count = min(needed, len(fill_candidates))
            fill_selected = random.sample(fill_candidates, fill_count)

            for fill_row in fill_selected:
                review_rows.append(fill_row)
            logger.info('[WeeklyRec] 随机补充了 %d 道菜品', fill_count)

    if not review_rows:
        logger.warning('[WeeklyRec] 无符合条件的菜品数据，跳过刷新')
        return

    WeeklyRecommendation.query.delete()
    for row in review_rows:
        item = WeeklyRecommendation(
            dish_id=row.dish_id,
            canteen_id=row.canteen_id,
            dish_name=row.dish_name,
            canteen_name=row.canteen_name,
            stall_name=row.stall_name,
            price=row.price,
            rating=round(float(row.avg_rating), 1),
            image_url=row.image_url,
            tags=row.tags,
            review_count=getattr(row, 'review_count', 0),
        )
        db.session.add(item)

    db.session.commit()
    logger.info('[WeeklyRec] 每周推荐刷新完成，共 %d 条', len(review_rows))


def get_daily_recommendations():
    """获取当前每日推荐列表，并使用 Dish 表中的实时图片 URL。"""
    items = DailyRecommendation.query.order_by(DailyRecommendation.created_at.desc()).all()
    if not items:
        return []

    # 批量获取实时菜品数据，确保图片 URL 是最新的
    dish_ids = [item.dish_id for item in items]
    dish_map = {d.id: d for d in Dish.query.filter(Dish.id.in_(dish_ids)).all()}
    return [_daily_to_dict(item, dish_map.get(item.dish_id)) for item in items]


def get_weekly_recommendations():
    """获取当前每周推荐列表，并使用 Dish 表中的实时图片 URL。"""
    items = WeeklyRecommendation.query.order_by(WeeklyRecommendation.rating.desc()).all()
    if not items:
        return []

    dish_ids = [item.dish_id for item in items]
    dish_map = {d.id: d for d in Dish.query.filter(Dish.id.in_(dish_ids)).all()}
    return [_weekly_to_dict(item, dish_map.get(item.dish_id)) for item in items]


def _daily_to_dict(item, dish=None):
    """序列化每日推荐项。如果提供了 dish 对象，则使用其最新的 image_url。"""
    effective_image_url = dish.image_url if dish and dish.image_url else item.image_url
    return {
        'id': item.dish_id,
        'dishId': item.dish_id,
        'canteenId': item.canteen_id,
        'name': item.dish_name,
        'canteenName': item.canteen_name,
        'stall': item.stall_name,
        'price': item.price,
        'rating': item.rating,
        'imageUrl': _img(effective_image_url),
        'tags': item.tags or [],
    }


def _weekly_to_dict(item, dish=None):
    """序列化每周推荐项。如果提供了 dish 对象，则使用其最新的 image_url 和 description。"""
    effective_image_url = dish.image_url if dish and dish.image_url else item.image_url
    effective_description = dish.description if dish and dish.description else ''
    return {
        'id': item.dish_id,
        'dishId': item.dish_id,
        'canteenId': item.canteen_id,
        'dishName': item.dish_name,
        'canteenName': item.canteen_name,
        'score': item.rating,
        'rating': item.rating,
        'price': item.price,
        'imageUrl': _img(effective_image_url),
        'description': effective_description,
        'stall': item.stall_name,
        'tags': item.tags or [],
        'reviewCount': item.review_count,
        'recommendVotes': 0,
        'avoidVotes': 0,
    }
