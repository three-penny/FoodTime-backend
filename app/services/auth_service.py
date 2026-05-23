"""
文件名：app/services/auth_service.py
功能描述：用户认证业务编排层，负责注册、登录、验证码等业务流程。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
import re
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from app.repositories.auth_repository import AuthRepository

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^\d+@bjtu\.edu\.cn$')
DEFAULT_VERIFICATION_CODE = '000000'


class AuthService:
    """用户认证业务服务，编排注册、登录与验证码发送流程。"""

    def __init__(self, repository: AuthRepository | None = None):
        self.repository = repository or AuthRepository()

    def register(self, email: str, password: str, nickname: str, verification_code: str, role: str = 'user') -> dict:
        """
        用户注册。
        参数说明：
            email: 邮箱，必须满足 <数字>@bjtu.edu.cn 格式。
            password: 明文密码。
            nickname: 用户昵称。
            verification_code: 邮箱验证码。
            role: 用户角色，默认为 'user'。
        返回值说明：
            返回创建成功的用户数据字典（不含密码哈希）。
        异常抛出：
            ValueError: 参数校验失败或邮箱已存在。
        """
        email = email.strip().lower()
        password = password.strip()
        nickname = nickname.strip()
        verification_code = verification_code.strip()

        if not email or not password or not nickname:
            raise ValueError('邮箱、密码和昵称不能为空。')

        if not EMAIL_REGEX.match(email):
            raise ValueError('邮箱格式不正确，必须为 <数字>@bjtu.edu.cn。')

        if len(password) < 6:
            raise ValueError('密码长度不能少于 6 位。')

        if verification_code != DEFAULT_VERIFICATION_CODE:
            raise ValueError('验证码错误。')

        if self.repository.find_by_email(email):
            raise ValueError('该邮箱已被注册。')

        account = email.split('@')[0]

        password_hash = generate_password_hash(password)
        user = self.repository.create_user(
            account=account,
            email=email,
            password_hash=password_hash,
            nickname=nickname,
            role=role,
        )

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
            返回登录成功的用户数据字典。
        异常抛出：
            ValueError: 账号不存在或密码错误。
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

        return {
            'id': user.id,
            'account': user.account,
            'email': user.email,
            'nickname': user.nickname,
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
