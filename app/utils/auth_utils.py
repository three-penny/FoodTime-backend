"""
文件名：app/utils/auth_utils.py
功能描述：JWT Token 生成、校验与鉴权装饰器，为 API 提供统一的认证与授权能力。
作者：FoodTime Backend Team
创建时间：2026-05-25
"""
import time
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, g, current_app

logger = logging.getLogger(__name__)

_RATE_LIMIT_STORE: dict[str, list[float]] = {}


def generate_token(user_id: str, account: str, role: str = 'user') -> str:
    """
    生成 JWT Token。
    参数说明：
        user_id: 用户 ID。
        account: 用户账号。
        role: 用户角色。
    返回值说明：
        返回编码后的 JWT 字符串。
    """
    expiration_hours = current_app.config.get('JWT_EXPIRATION_HOURS', 24)
    payload = {
        'user_id': user_id,
        'account': account,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=expiration_hours),
        'iat': datetime.now(timezone.utc),
    }
    secret = current_app.config['JWT_SECRET_KEY']
    return jwt.encode(payload, secret, algorithm='HS256')


def decode_token(token: str) -> dict | None:
    """
    解码并校验 JWT Token。
    参数说明：
        token: JWT 字符串。
    返回值说明：
        校验通过返回 payload 字典，失败返回 None。
    """
    try:
        secret = current_app.config['JWT_SECRET_KEY']
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning('JWT token expired')
        return None
    except jwt.InvalidTokenError:
        logger.warning('Invalid JWT token')
        return None


def login_required(f):
    """
    JWT 鉴权装饰器。从 Authorization Header 中提取 Bearer Token 并校验，
    通过后将 user_id、account、role 注入 g 对象供后续使用。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'code': 'AUTH_401_001',
                'message': '未提供有效的认证令牌。',
                'trace_id': getattr(g, 'trace_id', ''),
            }), 401

        token = auth_header[7:]
        payload = decode_token(token)
        if payload is None:
            return jsonify({
                'code': 'AUTH_401_001',
                'message': '认证令牌无效或已过期，请重新登录。',
                'trace_id': getattr(g, 'trace_id', ''),
            }), 401

        g.user_id = payload['user_id']
        g.account = payload['account']
        g.role = payload['role']
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    管理员鉴权装饰器。在 login_required 基础上校验角色是否为 admin 或 superadmin。
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.role not in ('admin', 'superadmin'):
            return jsonify({
                'code': 'AUTH_403_001',
                'message': '权限不足，仅管理员可执行此操作。',
                'trace_id': getattr(g, 'trace_id', ''),
            }), 403
        return f(*args, **kwargs)

    return decorated_function


def superadmin_required(f):
    """
    超级管理员鉴权装饰器。在 login_required 基础上校验角色是否为 superadmin。
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.role != 'superadmin':
            return jsonify({
                'code': 'AUTH_403_002',
                'message': '权限不足，仅超级管理员可执行此操作。',
                'trace_id': getattr(g, 'trace_id', ''),
            }), 403
        return f(*args, **kwargs)

    return decorated_function


def rate_limit(max_attempts: int = 5, window_seconds: int = 300):
    """
    基于 IP 的内存频率限制装饰器。
    参数说明：
        max_attempts: 时间窗口内最大请求次数。
        window_seconds: 滑动窗口秒数。
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr or '127.0.0.1'
            now = time.time()
            key = f'{request.path}:{ip}'

            if key not in _RATE_LIMIT_STORE:
                _RATE_LIMIT_STORE[key] = []

            timestamps = [t for t in _RATE_LIMIT_STORE[key] if now - t < window_seconds]
            _RATE_LIMIT_STORE[key] = timestamps

            if len(timestamps) >= max_attempts:
                return jsonify({
                    'code': 'AUTH_429_001',
                    'message': f'操作过于频繁，请 {window_seconds // 60} 分钟后再试。',
                    'trace_id': getattr(g, 'trace_id', ''),
                }), 429

            _RATE_LIMIT_STORE[key].append(now)
            return f(*args, **kwargs)

        return decorated_function

    return decorator
