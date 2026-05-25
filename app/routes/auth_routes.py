"""
文件名：app/routes/auth_routes.py
功能描述：用户认证相关路由，处理注册、登录与验证码发送请求。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
from flask import Blueprint, request, jsonify, g
from app.services.auth_service import AuthService
from app.utils.auth_utils import rate_limit

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.post('/register')
def register():
    """
    接口说明：用户注册，需提供邮箱、密码、昵称、验证码。
    权限要求：无。
    请求参数：email, password, nickname, verification_code, role(可选)。
    返回说明：返回创建成功的用户信息。
    """
    data = request.get_json(silent=True) or {}
    service = AuthService()

    try:
        user = service.register(
            email=data.get('email', ''),
            password=data.get('password', ''),
            nickname=data.get('nickname', ''),
            verification_code=data.get('verification_code', ''),
            role=data.get('role', 'user'),
            invite_code=data.get('invite_code', ''),
        )
        return jsonify({
            'code': 0,
            'message': '注册成功',
            'data': user,
            'trace_id': g.trace_id,
        }), 201
    except ValueError as e:
        return jsonify({
            'code': 'AUTH_422_001',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@auth_bp.post('/login')
@rate_limit(max_attempts=10, window_seconds=300)
def login():
    """
    接口说明：用户登录，支持使用邮箱或账号登录。
    权限要求：无。
    请求参数：login_id, password。
    返回说明：返回用户信息与 JWT Token。
    """
    data = request.get_json(silent=True) or {}
    service = AuthService()

    try:
        user = service.login(
            login_id=data.get('login_id', ''),
            password=data.get('password', ''),
        )
        return jsonify({
            'code': 0,
            'message': '登录成功',
            'data': user,
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'AUTH_401_001',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 401


@auth_bp.post('/send-code')
def send_code():
    """
    接口说明：发送邮箱验证码（当前默认使用 000000，后续接入真实邮件服务）。
    权限要求：无。
    请求参数：email。
    返回说明：返回发送结果。
    """
    data = request.get_json(silent=True) or {}
    service = AuthService()

    try:
        service.send_verification_code(email=data.get('email', ''))
        return jsonify({
            'code': 0,
            'message': '验证码已发送',
            'data': {},
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'AUTH_422_002',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422
