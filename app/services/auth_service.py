"""
文件名：app/services/auth_service.py
功能描述：用户认证业务编排层，负责注册、登录、验证码等业务流程。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
import re
import random
import string
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import current_app
from app.repositories.auth_repository import AuthRepository
from app.utils.auth_utils import generate_token
from app.entities.models import InviteCode
from app.extensions import db

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^\d+@bjtu\.edu\.cn$')
DEFAULT_VERIFICATION_CODE = '000000'
ALLOWED_ROLES = {'user', 'admin', 'superadmin'}
INVITE_CODE_LENGTH = 6
INVITE_CODE_DAYS_VALID = 3
INVITE_CODE_CHARS = string.ascii_uppercase + string.digits
DEBUG_INVITE_CODE = 'ABCDEF'

MAX_FIELD_LENGTHS = {
    'email': 120,
    'password': 128,
    'nickname': 50,
    'account': 50,
}


class AuthService:
    """用户认证业务服务，编排注册、登录与验证码发送流程。"""

    def __init__(self, repository: AuthRepository | None = None):
        self.repository = repository or AuthRepository()

    def _validate_field_length(self, field_name: str, value: str):
        """校验字段长度不超过数据库定义的最大值。"""
        max_len = MAX_FIELD_LENGTHS.get(field_name)
        if max_len and len(value) > max_len:
            raise ValueError(f'{field_name} 长度不能超过 {max_len} 个字符。')

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

        self._validate_field_length('email', email)
        self._validate_field_length('password', password)
        self._validate_field_length('nickname', nickname)

        if not EMAIL_REGEX.match(email):
            raise ValueError('邮箱格式不正确，必须为 <数字>@bjtu.edu.cn。')

        if len(password) < 6:
            raise ValueError('密码长度不能少于 6 位。')

        if verification_code != DEFAULT_VERIFICATION_CODE:
            raise ValueError('验证码错误。')

        if role not in ALLOWED_ROLES:
            raise ValueError('无效的用户角色。')

        if role == 'admin':
            if not invite_code:
                raise ValueError('管理员注册需要提供邀请码。')
            if not self._validate_invite_code(invite_code):
                raise ValueError('管理员邀请码不正确。')

        if self.repository.find_by_email(email):
            raise ValueError('该邮箱已被注册。')

        account = email.split('@')[0]

        self._validate_field_length('account', account)

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

            if role == 'admin' and invite_code != DEBUG_INVITE_CODE:
                self._consume_invite_code(invite_code, user.id)

            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logger.warning('注册冲突: email=%s, account=%s', email, account)
            raise ValueError('该账号或邮箱已被注册，请勿重复提交。')
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('注册数据库异常: email=%s', email)
            raise ValueError('注册失败，请稍后重试。')

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

        self._validate_field_length('password', password)

        user = self.repository.find_by_email(login_id)
        if not user:
            user = self.repository.find_by_account(login_id)
        if not user:
            logger.info('登录失败: 未找到用户 login_id=%s', login_id[:20])
            raise ValueError('账号或密码错误。')

        if not check_password_hash(user.password_hash, password):
            logger.info('登录失败: 密码错误 account=%s', user.account)
            raise ValueError('账号或密码错误。')

        if user.account_status != 'active':
            logger.warning('登录失败: 账号已禁用 account=%s', user.account)
            raise ValueError('该账号已被禁用，请联系管理员。')

        token = generate_token(
            user_id=user.id,
            account=user.account,
            role=user.role,
        )

        return {
            'id': user.id,
            'account': user.account,
            'email': user.email or '',
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

    def _generate_code_string(self) -> str:
        """生成6位随机字母+数字组合的邀请码。"""
        return ''.join(random.choices(INVITE_CODE_CHARS, k=INVITE_CODE_LENGTH))

    def _validate_invite_code(self, code: str) -> bool:
        """校验邀请码是否有效（调试码ABCDEF 或 数据库中有效的邀请码）。"""
        if code == DEBUG_INVITE_CODE:
            return True
        invite_code = InviteCode.query.filter_by(code=code, is_active=True).first()
        if not invite_code:
            return False
        if invite_code.expires_at < datetime.utcnow():
            return False
        if invite_code.used_by is not None:
            return False
        return True

    def _consume_invite_code(self, code: str, user_id: str):
        """将邀请码标记为已使用（不提交事务，由调用方统一提交或回滚）。"""
        if code == DEBUG_INVITE_CODE:
            return
        invite_code = InviteCode.query.filter_by(code=code).first()
        if invite_code:
            invite_code.used_by = user_id
            invite_code.is_active = False
            db.session.flush()

    def generate_invite_code(self, admin_user_id: str) -> dict:
        """
        为管理员生成邀请码。
        如果该管理员已有有效的邀请码（未过期、未使用），则直接返回已有邀请码。
        否则生成新的邀请码（有效期3天）。
        """
        existing = InviteCode.query.filter(
            InviteCode.created_by == admin_user_id,
            InviteCode.is_active == True,
            InviteCode.used_by == None,
            InviteCode.expires_at > datetime.utcnow(),
        ).first()

        if existing:
            return {
                'code': existing.code,
                'expires_at': existing.expires_at.isoformat(),
                'is_active': existing.is_active,
            }

        new_code = self._generate_code_string()
        while InviteCode.query.filter_by(code=new_code).first():
            new_code = self._generate_code_string()

        expires_at = datetime.utcnow() + timedelta(days=INVITE_CODE_DAYS_VALID)
        invite_code = InviteCode(
            code=new_code,
            created_by=admin_user_id,
            expires_at=expires_at,
        )
        try:
            db.session.add(invite_code)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError('邀请码生成失败，请重试。')

        return {
            'code': invite_code.code,
            'expires_at': invite_code.expires_at.isoformat(),
            'is_active': invite_code.is_active,
        }

    def get_active_invite_code(self, admin_user_id: str) -> dict | None:
        """
        获取当前管理员的有效邀请码。
        返回当前有效的邀请码信息，如果没有则返回 None。
        """
        existing = InviteCode.query.filter(
            InviteCode.created_by == admin_user_id,
            InviteCode.is_active == True,
            InviteCode.used_by == None,
            InviteCode.expires_at > datetime.utcnow(),
        ).first()

        if not existing:
            return None

        return {
            'code': existing.code,
            'expires_at': existing.expires_at.isoformat(),
            'is_active': existing.is_active,
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
