"""
文件名：app/routes/superadmin_routes.py
功能描述：超级管理员专属路由，提供用户管理、操作日志查询和数据报表功能。
作者：FoodTime Backend Team
创建时间：2026-05-31
"""
from flask import Blueprint, request, jsonify, g
from app.services.superadmin_service import SuperadminService
from app.utils.auth_utils import superadmin_required

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/api/v1/superadmin')


@superadmin_bp.get('/users')
@superadmin_required
def list_users():
    """
    接口说明：获取用户列表（支持分页和搜索）。
    权限要求：超级管理员。
    查询参数：page, per_page, search。
    """
    service = SuperadminService()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    result = service.get_all_users(page=page, per_page=per_page, search=search)
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': result,
        'trace_id': g.trace_id,
    }), 200


@superadmin_bp.put('/users/<user_id>/role')
@superadmin_required
def set_user_role(user_id: str):
    """
    接口说明：更改指定用户的角色。
    权限要求：超级管理员。
    请求参数：role (user/admin/superadmin)。
    """
    data = request.get_json(silent=True) or {}
    service = SuperadminService()
    try:
        new_role = data.get('role', '')
        if not new_role or not isinstance(new_role, str):
            return jsonify({
                'code': 'SA_422_001',
                'message': '角色不能为空。',
                'trace_id': g.trace_id,
            }), 422
        result = service.set_user_role(
            user_id=user_id,
            new_role=new_role.strip().lower(),
            operator_account=g.account,
            operator_id=g.user_id,
        )
        return jsonify({
            'code': 0,
            'message': '角色修改成功',
            'data': result,
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'SA_422_002',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@superadmin_bp.put('/users/<user_id>/status')
@superadmin_required
def set_user_status(user_id: str):
    """
    接口说明：设置用户封禁/解封状态。
    权限要求：超级管理员。
    请求参数：status (active/banned)。
    """
    data = request.get_json(silent=True) or {}
    service = SuperadminService()
    try:
        new_status = data.get('status', '')
        if not new_status or not isinstance(new_status, str):
            return jsonify({
                'code': 'SA_422_003',
                'message': '状态不能为空。',
                'trace_id': g.trace_id,
            }), 422
        result = service.set_user_status(
            user_id=user_id,
            new_status=new_status.strip().lower(),
            operator_account=g.account,
            operator_id=g.user_id,
        )
        return jsonify({
            'code': 0,
            'message': '状态修改成功',
            'data': result,
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'SA_422_004',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@superadmin_bp.get('/logs')
@superadmin_required
def list_audit_logs():
    """
    接口说明：获取操作日志列表（支持分页和操作类型/目标类型筛选）。
    权限要求：超级管理员。
    查询参数：page, per_page, action, target_type。
    """
    service = SuperadminService()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    action = request.args.get('action', '', type=str)
    target_type = request.args.get('target_type', '', type=str)
    result = service.get_audit_logs(page=page, per_page=per_page, action=action, target_type=target_type)
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': result,
        'trace_id': g.trace_id,
    }), 200


@superadmin_bp.put('/users/<user_id>/password')
@superadmin_required
def change_password(user_id: str):
    """
    接口说明：超级管理员强制修改指定用户密码。
    权限要求：超级管理员。
    请求参数：password（新密码，6-128 位）。
    异常说明：用户不存在返回 SA_422_006，参数非法返回 SA_422_005。
    """
    data = request.get_json(silent=True) or {}
    service = SuperadminService()
    try:
        new_password = data.get('password', '')
        if not new_password or not isinstance(new_password, str):
            return jsonify({
                'code': 'SA_422_005',
                'message': '新密码不能为空，请输入后重试。',
                'trace_id': g.trace_id,
            }), 422
        result = service.change_user_password(
            user_id=user_id,
            new_password=new_password,
            operator_account=g.account,
            operator_id=g.user_id,
        )
        return jsonify({
            'code': 0,
            'message': f'已成功将 {result["account"]} 的密码重置。',
            'data': result,
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'SA_422_006',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@superadmin_bp.get('/dashboard')
@superadmin_required
def dashboard():
    """
    接口说明：获取数据报表。
    权限要求：超级管理员。
    """
    service = SuperadminService()
    stats = service.get_dashboard_stats()
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': stats,
        'trace_id': g.trace_id,
    }), 200
