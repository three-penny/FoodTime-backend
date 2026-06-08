from flask import Blueprint, jsonify, request, g
from app.services.rant_service import RantService
from app.utils.auth_utils import login_required, admin_required

rant_bp = Blueprint('rants', __name__, url_prefix='/api/v1')
rant_service = RantService()


@rant_bp.get('/rants')
@login_required
def list_rants():
    status = request.args.get('status')
    if status:
        data = rant_service.get_rants_by_status(status)
    else:
        data = rant_service.get_all_rants()
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200


@rant_bp.post('/rants')
@login_required
def create_rant():
    data = request.get_json(silent=True) or {}

    try:
        rant = rant_service.create_rant(
            canteen_name=data.get('canteenName', ''),
            author_account=data.get('author', ''),
            content=data.get('content', ''),
            tag=data.get('tag', '吐槽'),
        )
        return jsonify({
            'code': 0,
            'message': '吐槽发布成功，请等待审核。',
            'data': rant,
            'trace_id': g.trace_id,
        }), 201
    except ValueError as e:
        return jsonify({
            'code': 'RANT_422_001',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422


@rant_bp.put('/rants/<rant_id>')
@admin_required
def edit_rant(rant_id):
    data = request.get_json(silent=True) or {}
    try:
        rant = rant_service.update_rant_content(
            rant_id,
            canteen_name=data.get('canteenName'),
            content=data.get('content'),
            tag=data.get('tag'),
        )
        return jsonify({'code': 0, 'message': '更新成功', 'data': rant, 'trace_id': g.trace_id}), 200
    except ValueError as e:
        return jsonify({'code': 'RANT_422_003', 'message': str(e), 'trace_id': g.trace_id}), 422


@rant_bp.put('/rants/<rant_id>/audit')
@admin_required
def audit_rant(rant_id):
    data = request.get_json(silent=True) or {}

    try:
        rant_service.audit_rant(
            rant_id=rant_id,
            status=data.get('status', ''),
            audit_reason=data.get('reason', ''),
            auditor_account=data.get('auditor', ''),
        )
        return jsonify({
            'code': 0,
            'message': '审核完成',
            'data': {},
            'trace_id': g.trace_id,
        }), 200
    except ValueError as e:
        return jsonify({
            'code': 'RANT_422_002',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422
