"""
文件名：app/routes/auth_routes.py
功能描述：用户认证相关路由，处理注册、登录与验证码发送请求。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
from flask import Blueprint, request, jsonify, g
from app.services.auth_service import AuthService
from app.utils.auth_utils import rate_limit, login_required, admin_required

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
        email = data.get('email', '')
        password = data.get('password', '')
        nickname = data.get('nickname', '')
        verification_code = data.get('verification_code', '')
        role = data.get('role', 'user')
        invite_code = data.get('invite_code', '')

        if not isinstance(email, str) or not isinstance(password, str) or not isinstance(nickname, str):
            return jsonify({
                'code': 'AUTH_422_005',
                'message': '请求参数格式不正确。',
                'trace_id': g.trace_id,
            }), 422

        user = service.register(
            email=email,
            password=password,
            nickname=nickname,
            verification_code=verification_code,
            role=role,
            invite_code=invite_code,
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
        login_id = data.get('login_id', '')
        password = data.get('password', '')

        if not isinstance(login_id, str):
            return jsonify({
                'code': 'AUTH_422_005',
                'message': '账号格式不正确。',
                'trace_id': g.trace_id,
            }), 422
        if not login_id:
            return jsonify({
                'code': 'AUTH_422_005',
                'message': '账号不能为空。',
                'trace_id': g.trace_id,
            }), 422
        if not isinstance(password, str):
            return jsonify({
                'code': 'AUTH_422_005',
                'message': '密码格式不正确。',
                'trace_id': g.trace_id,
            }), 422
        if not password:
            return jsonify({
                'code': 'AUTH_422_005',
                'message': '密码不能为空。',
                'trace_id': g.trace_id,
            }), 422

        user = service.login(
            login_id=login_id,
            password=password,
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
    接口说明：发送6位数字邮箱验证码。
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
    except RuntimeError as e:
        return jsonify({
            'code': 'AUTH_500_001',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 500


@auth_bp.put('/profile')
@login_required
def update_profile():
    """
    接口说明：更新当前登录用户资料。
    权限要求：需要用户登录。
    请求参数（JSON）：nickname（可选）, email（可选）。
    返回说明：返回更新后的用户信息。
    """
    data = request.get_json(silent=True) or {}
    service = AuthService()

    try:
        user = service.update_profile(
            user_id=g.user_id,
            nickname=data.get('nickname'),
            email=data.get('email'),
        )
        return jsonify({
            'code': 0,
            'message': '资料更新成功',
            'data': user,
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'AUTH_422_003',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@auth_bp.post('/invite-code/generate')
@admin_required
def generate_invite_code():
    """
    接口说明：生成或获取当前管理员的有效邀请码。
             如果已有有效邀请码则直接返回，否则生成新的邀请码。
    权限要求：管理员。
    返回说明：返回邀请码信息（包含过期时间）。
    """
    service = AuthService()
    try:
        result = service.generate_invite_code(admin_user_id=g.user_id)
        return jsonify({
            'code': 0,
            'message': '邀请码获取成功',
            'data': result,
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'AUTH_422_004',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@auth_bp.get('/invite-code')
@admin_required
def get_invite_code():
    """
    接口说明：获取当前管理员的有效邀请码。
    权限要求：管理员。
    返回说明：有有效邀请码则返回邀请码信息，否则返回空数据。
    """
    service = AuthService()
    result = service.get_active_invite_code(admin_user_id=g.user_id)
    if result:
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': result,
            'trace_id': g.trace_id,
        }), 200
    return jsonify({
        'code': 0,
        'message': '暂无有效邀请码',
        'data': None,
        'trace_id': g.trace_id,
    }), 200
