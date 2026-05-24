from app.entities.models import User, PointRecord
from app.extensions import db
from datetime import datetime


class PointsService:
    def get_user_points(self, user_id):
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return {
            'currentPoints': user.current_points or 0,
            'totalEarned': user.total_earned_points or 0,
            'totalUsed': user.total_used_points or 0,
        }

    def get_points_history(self, user_id):
        records = db.session.query(PointRecord).filter(
            PointRecord.user_id == user_id
        ).order_by(PointRecord.created_at.desc()).all()

        return [
            {
                'id': r.id,
                'amount': f'+{r.amount}' if r.amount > 0 else str(r.amount),
                'reason': r.source_or_dest,
                'type': r.record_type,
                'timestamp': r.created_at.strftime('%Y/%m/%d %H:%M') if r.created_at else '',
            }
            for r in records
        ]

    def add_points(self, user_id, amount, reason, record_type='earn'):
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError('用户不存在。')
        if amount <= 0:
            raise ValueError('积分数量必须大于 0。')

        user.current_points = (user.current_points or 0) + amount
        user.total_earned_points = (user.total_earned_points or 0) + amount

        record = PointRecord(
            user_id=user_id,
            amount=amount,
            record_type=record_type,
            source_or_dest=reason,
        )
        db.session.add(record)
        db.session.commit()
        return {'currentPoints': user.current_points}

    def consume_points(self, user_id, amount, reason):
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError('用户不存在。')
        if amount <= 0:
            raise ValueError('积分数量必须大于 0。')
        if (user.current_points or 0) < amount:
            raise ValueError('积分不足。')

        user.current_points -= amount
        user.total_used_points = (user.total_used_points or 0) + amount

        record = PointRecord(
            user_id=user_id,
            amount=-amount,
            record_type='use',
            source_or_dest=reason,
        )
        db.session.add(record)
        db.session.commit()
        return {'currentPoints': user.current_points}

    def daily_checkin(self, user_id):
        today = datetime.utcnow().date()
        existing = db.session.query(PointRecord).filter(
            PointRecord.user_id == user_id,
            PointRecord.record_type == 'daily',
        ).order_by(PointRecord.created_at.desc()).first()

        if existing and existing.created_at.date() == today:
            return False

        self.add_points(user_id, 5, '每日签到奖励', 'daily')
        return True
