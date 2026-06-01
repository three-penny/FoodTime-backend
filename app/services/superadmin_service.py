"""
文件名：app/services/superadmin_service.py
功能描述：超级管理员业务逻辑层，提供用户管理、操作日志和数据报表服务。
作者：FoodTime Backend Team
创建时间：2026-05-31
"""
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.entities.models import (
    User, Dish, Review, Rant, DishSubmission,
    Canteen, Stall, PointRecord, AuditLog,
)


class SuperadminService:

    def get_all_users(self, page: int = 1, per_page: int = 20, search: str = '') -> dict:
        query = User.query
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                User.account.ilike(search_term) |
                User.nickname.ilike(search_term) |
                User.email.ilike(search_term)
            )
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            'items': [
                {
                    'id': u.id,
                    'account': u.account,
                    'email': u.email or '',
                    'nickname': u.nickname,
                    'role': u.role,
                    'account_status': u.account_status,
                    'created_at': u.created_at.isoformat() if u.created_at else '',
                }
                for u in pagination.items
            ],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
        }

    def set_user_role(self, user_id: str, new_role: str, operator_account: str, operator_id: str) -> dict:
        if new_role not in ('user', 'admin', 'superadmin'):
            raise ValueError('无效的角色值。')
        user = User.query.get(user_id)
        if not user:
            raise ValueError('用户不存在。')
        old_role = user.role
        user.role = new_role
        self._add_log(
            operator_account=operator_account,
            operator_id=operator_id,
            action='role_change',
            target_type='user',
            target_id=user_id,
            detail=f'角色由 {old_role} 变更为 {new_role}，账号: {user.account}',
        )
        db.session.commit()
        return {
            'id': user.id,
            'account': user.account,
            'role': user.role,
        }

    def set_user_status(self, user_id: str, new_status: str, operator_account: str, operator_id: str) -> dict:
        if new_status not in ('active', 'banned'):
            raise ValueError('无效的状态值。')
        user = User.query.get(user_id)
        if not user:
            raise ValueError('用户不存在。')
        old_status = user.account_status
        user.account_status = new_status
        self._add_log(
            operator_account=operator_account,
            operator_id=operator_id,
            action='status_change',
            target_type='user',
            target_id=user_id,
            detail=f'状态由 {old_status} 变更为 {new_status}，账号: {user.account}',
        )
        db.session.commit()
        return {
            'id': user.id,
            'account': user.account,
            'account_status': user.account_status,
        }

    def get_audit_logs(self, page: int = 1, per_page: int = 20, action: str = '', target_type: str = '') -> dict:
        query = AuditLog.query
        if action:
            query = query.filter_by(action=action)
        if target_type:
            query = query.filter_by(target_type=target_type)
        pagination = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            'items': [
                {
                    'id': log.id,
                    'operator_account': log.operator_account or '',
                    'operator_id': log.operator_id or '',
                    'action': log.action,
                    'target_type': log.target_type,
                    'target_id': log.target_id or '',
                    'detail': log.detail or '',
                    'created_at': log.created_at.isoformat() if log.created_at else '',
                }
                for log in pagination.items
            ],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
        }

    def change_user_password(self, user_id: str, new_password: str, operator_account: str, operator_id: str) -> dict:
        """
        功能描述：超级管理员强制修改指定用户密码。
        参数说明：
            user_id: 目标用户 ID
            new_password: 新明文密码
            operator_account: 操作者账号
            operator_id: 操作者 ID
        异常抛出：
            ValueError: 用户不存在或密码不合法。
        """
        new_password = new_password.strip() if isinstance(new_password, str) else new_password
        if not new_password or not isinstance(new_password, str):
            raise ValueError('新密码不能为空。')
        if len(new_password) < 6:
            raise ValueError('密码长度不能少于 6 位。')
        if len(new_password) > 128:
            raise ValueError('密码长度不能超过 128 个字符。')

        user = User.query.get(user_id)
        if not user:
            raise ValueError('用户不存在或已被删除。')

        try:
            user.password_hash = generate_password_hash(new_password)
        except Exception:
            raise ValueError('密码处理失败，请稍后重试。')

        self._add_log(
            operator_account=operator_account,
            operator_id=operator_id,
            action='password_change',
            target_type='user',
            target_id=user_id,
            detail=f'密码已重置，账号: {user.account}',
        )
        db.session.commit()
        return {
            'id': user.id,
            'account': user.account,
        }

    def get_dashboard_stats(self) -> dict:
        stats = {}
        try:
            stats['user_count'] = User.query.count()
            stats['admin_count'] = User.query.filter_by(role='admin').count()
            stats['superadmin_count'] = User.query.filter_by(role='superadmin').count()
            stats['user_today'] = User.query.filter(
                User.created_at >= datetime.utcnow().date()
            ).count()
            stats['dish_count'] = Dish.query.count()
            stats['canteen_count'] = Canteen.query.count()
            stats['stall_count'] = Stall.query.count()
            stats['pending_reviews'] = Review.query.filter_by(status='pending').count()
            stats['total_reviews'] = Review.query.count()
            stats['pending_rants'] = Rant.query.filter_by(status='pending').count()
            stats['total_rants'] = Rant.query.count()
            stats['pending_submissions'] = DishSubmission.query.filter_by(status='pending').count()
            stats['total_submissions'] = DishSubmission.query.count()
            stats['total_invite_codes'] = db.session.query(func.count()).select_from(
                db.Model.metadata.tables.get('invite_codes')
            ).scalar() or 0
            stats['active_users'] = User.query.filter_by(account_status='active').count()
            stats['banned_users'] = User.query.filter_by(account_status='banned').count()
        except SQLAlchemyError:
            pass
        return stats

    def _add_log(self, operator_account: str, operator_id: str, action: str,
                 target_type: str, target_id: str = '', detail: str = ''):
        log_entry = AuditLog(
            operator_account=operator_account,
            operator_id=operator_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
        db.session.add(log_entry)
        db.session.flush()
