"""
文件名：app/services/auth_service.py
功能描述：用户认证业务编排层，负责注册、登录、验证码等业务流程。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
import re
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from flask import current_app
from app.repositories.auth_repository import AuthRepository
from app.utils.auth_utils import generate_token
from app.extensions import db

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^\d+@bjtu\.edu\.cn$')
DEFAULT_VERIFICATION_CODE = '000000'
ALLOWED_ROLES = {'user', 'admin'}


class AuthService:
    """用户认证业务服务，编排注册、登录与验证码发送流程。"""

    def __init__(self, repository: AuthRepository | None = None):
        self.repository = repository or AuthRepository()

    def register(self, email: str, password: str, nickname: str, verification_code: str, role: str = 'user', invite_code: str = '') -> dict:
        """
        用户注册。
        参数说明：
            email: 邮箱，必须满足 <数字>@bjtu.edu.cn 格式。
            password: 明文密码。
            nickname: 用户昵称。
            verification_code: 邮箱验证码。
            role: 用户角色，默认为 'user'。
            invite_code: 管理员邀请码，role=admin 时必填。
        返回值说明：
            返回创建成功的用户数据字典（不含密码哈希）。
        异常抛出：
            ValueError: 参数校验失败或邮箱已存在。
        """
        email = email.strip().lower()
        password = password.strip()
        nickname = nickname.strip()
        verification_code = verification_code.strip()
        role = role.strip().lower()
        invite_code = invite_code.strip()

        if not email or not password or not nickname:
            raise ValueError('邮箱、密码和昵称不能为空。')

        if not EMAIL_REGEX.match(email):
            raise ValueError('邮箱格式不正确，必须为 <数字>@bjtu.edu.cn。')

        if len(password) < 6:
            raise ValueError('密码长度不能少于 6 位。')

        if verification_code != DEFAULT_VERIFICATION_CODE:
            raise ValueError('验证码错误。')

        if role not in ALLOWED_ROLES:
            raise ValueError('无效的用户角色。')

        if role == 'admin':
            expected_code = current_app.config.get('ADMIN_INVITE_CODE', '')
            if not invite_code:
                raise ValueError('管理员注册需要提供邀请码。')
            if invite_code != expected_code:
                raise ValueError('管理员邀请码不正确。')

        if self.repository.find_by_email(email):
            raise ValueError('该邮箱已被注册。')

        account = email.split('@')[0]

        if self.repository.find_by_account(account):
            raise ValueError('该学号已被注册。')

        password_hash = generate_password_hash(password)
        try:
            user = self.repository.create_user(
                account=account,
                email=email,
                password_hash=password_hash,
                nickname=nickname,
                role=role,
            )
        except IntegrityError:
            db.session.rollback()
            raise ValueError('该账号或邮箱已被注册，请勿重复提交。')

        return {
            'id': user.id,
            'account': user.account,
            'email': user.email,
            'nickname': user.nickname,
            'role': user.role,
        }

    def login(self, login_id: str, password: str) -> dict:
        """
        用户登录。
        参数说明：
            login_id: 邮箱或账号。
            password: 明文密码。
        返回值说明：
            返回登录成功的用户数据字典与 JWT Token。
        异常抛出：
            ValueError: 账号不存在、密码错误或账号已被禁用。
        """
        login_id = login_id.strip().lower()
        password = password.strip()

        if not login_id or not password:
            raise ValueError('账号和密码不能为空。')

        user = self.repository.find_by_email(login_id)
        if not user:
            user = self.repository.find_by_account(login_id)
        if not user:
            raise ValueError('账号或密码错误。')

        if not check_password_hash(user.password_hash, password):
            raise ValueError('账号或密码错误。')

        if user.account_status != 'active':
            raise ValueError('该账号已被禁用，请联系管理员。')

        token = generate_token(
            user_id=user.id,
            account=user.account,
            role=user.role,
        )

        return {
            'id': user.id,
            'account': user.account,
            'email': user.email,
            'nickname': user.nickname,
            'role': user.role,
            'token': token,
        }

    def update_profile(self, user_id: str, nickname: str | None = None, email: str | None = None) -> dict:
        """更新用户资料。"""
        updates = {}
        if nickname is not None:
            nickname = nickname.strip()
            if not nickname:
                raise ValueError('昵称不能为空。')
            updates['nickname'] = nickname
        if email is not None:
            email = email.strip().lower()
            if not EMAIL_REGEX.match(email):
                raise ValueError('邮箱格式不正确。')
            existing = self.repository.find_by_email(email)
            if existing and existing.id != user_id:
                raise ValueError('该邮箱已被其他账号使用。')
            updates['email'] = email

        if not updates:
            raise ValueError('没有需要更新的字段。')

        user = self.repository.update_user(user_id, **updates)
        if not user:
            raise ValueError('用户不存在。')

        return {
            'id': user.id,
            'account': user.account,
            'nickname': user.nickname,
            'email': user.email or '',
            'role': user.role,
        }

    def send_verification_code(self, email: str) -> bool:
        """
        发送邮箱验证码（预留方法）。
        当前阶段默认使用固定验证码 000000，后续接入真实邮件服务。
        参数说明：
            email: 接收验证码的邮箱地址。
        返回值说明：
            始终返回 True 表示发送成功。
        """
        email = email.strip().lower()
        if not EMAIL_REGEX.match(email):
            raise ValueError('邮箱格式不正确，必须为 <数字>@bjtu.edu.cn。')
        logger.info('Send verification code to %s (default: %s)', email, DEFAULT_VERIFICATION_CODE)
        return True
