"""
文件名：app/repositories/auth_repository.py
功能描述：用户认证相关数据库访问层。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
from app.entities.models import User
from app.extensions import db


class AuthRepository:
    """用户认证数据访问层，负责用户查询与创建。"""

    def find_by_email(self, email: str) -> User | None:
        """根据邮箱查询用户。"""
        return User.query.filter_by(email=email).first()

    def find_by_account(self, account: str) -> User | None:
        """根据账号查询用户。"""
        return User.query.filter_by(account=account).first()

    def create_user(self, account: str, email: str, password_hash: str, nickname: str, role: str = 'user') -> User:
        """创建新用户（不提交事务，由调用方统一提交或回滚）。"""
        user = User(
            account=account,
            email=email,
            password_hash=password_hash,
            nickname=nickname,
            role=role,
        )
        db.session.add(user)
        db.session.flush()
        return user

    def update_user(self, user_id: str, **kwargs) -> User | None:
        """更新用户信息。"""
        user = User.query.get(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        db.session.commit()
        return user
