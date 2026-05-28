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


def refresh_weekly_recommendations():
    """每周日凌晨 0 点执行：根据最近 200 条评论均分最高的前 10 道菜品。"""
    logger.info('[WeeklyRec] 开始刷新每周推荐')

    subq = (
        db.session.query(
            Review.dish_id,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count'),
        )
        .filter(Review.status == 'approved')
        .group_by(Review.dish_id)
        .order_by(Review.created_at.desc())
        .limit(200)
        .subquery()
    )

    rows = (
        db.session.query(
            subq.c.dish_id,
            subq.c.avg_rating,
            subq.c.review_count,
            Dish.canteen_id,
            Dish.name,
            Dish.price,
            Dish.rating,
            Dish.image_url,
            Dish.tags,
            Canteen.name,
            Stall.name,
        )
        .join(Dish, subq.c.dish_id == Dish.id)
        .join(Canteen, Dish.canteen_id == Canteen.id)
        .outerjoin(Stall, Dish.stall_id == Stall.id)
        .order_by(subq.c.avg_rating.desc())
        .limit(10)
        .all()
    )

    if not rows:
        logger.warning('[WeeklyRec] 无符合条件的评论数据，跳过刷新')
        return

    WeeklyRecommendation.query.delete()
    for row in rows:
        item = WeeklyRecommendation(
            dish_id=row.dish_id,
            canteen_id=row.canteen_id,
            dish_name=row.name,
            canteen_name=row[9],
            stall_name=row[10],
            price=row.price,
            rating=round(float(row.avg_rating), 1),
            image_url=row.image_url,
            tags=row.tags,
            review_count=row.review_count,
        )
        db.session.add(item)

    db.session.commit()
    logger.info('[WeeklyRec] 每周推荐刷新完成，共 %d 条', len(rows))


def get_daily_recommendations():
    """获取当前每日推荐列表。"""
    items = DailyRecommendation.query.order_by(DailyRecommendation.created_at.desc()).all()
    return [_daily_to_dict(i) for i in items]


def get_weekly_recommendations():
    """获取当前每周推荐列表。"""
    items = WeeklyRecommendation.query.order_by(WeeklyRecommendation.rating.desc()).all()
    return [_weekly_to_dict(i) for i in items]


def _daily_to_dict(item):
    return {
        'id': item.dish_id,
        'dishId': item.dish_id,
        'canteenId': item.canteen_id,
        'name': item.dish_name,
        'canteenName': item.canteen_name,
        'stall': item.stall_name,
        'price': item.price,
        'rating': item.rating,
        'imageUrl': _img(item.image_url),
        'tags': item.tags or [],
    }


def _weekly_to_dict(item):
    return {
        'id': item.dish_id,
        'dishId': item.dish_id,
        'canteenId': item.canteen_id,
        'dishName': item.dish_name,
        'canteenName': item.canteen_name,
        'score': item.rating,
        'rating': item.rating,
        'price': item.price,
        'imageUrl': _img(item.image_url),
        'stall': item.stall_name,
        'tags': item.tags or [],
        'reviewCount': item.review_count,
        'recommendVotes': 0,
        'avoidVotes': 0,
    }
