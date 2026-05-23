"""
文件名：app/routes/dish_submission_routes.py
功能描述：菜品提报相关路由，处理图片上传与提报创建请求。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
from flask import Blueprint, request, jsonify, g
from app.services.dish_submission_service import DishSubmissionService

submission_bp = Blueprint('submission', __name__, url_prefix='/api/v1/submissions')


@submission_bp.get('')
def list_submissions():
    """
    接口说明：查询指定用户的菜品提报列表。
    权限要求：需要用户登录。
    请求参数：account（必填，提交者账号）。
    返回说明：返回该用户的提报记录列表及统计信息。
    """
    account = request.args.get('account', '')
    if not account:
        return jsonify({
            'code': 'SUBMIT_422_002',
            'message': '账号参数不能为空。',
            'trace_id': g.trace_id,
        }), 422

    service = DishSubmissionService()
    submissions = service.get_submissions_by_user(account)

    pending_count = sum(1 for s in submissions if s['status'] == 'pending')
    approved_count = sum(1 for s in submissions if s['status'] == 'approved')
    rejected_count = sum(1 for s in submissions if s['status'] == 'rejected')

    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'items': submissions,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'total': len(submissions),
        },
        'trace_id': g.trace_id,
    }), 200


@submission_bp.post('')
def create_submission():
    """
    接口说明：创建菜品提报（支持图片上传）。
    权限要求：需要用户登录。
    请求参数（multipart/form-data）：
        dish_name: 菜品名称（必填）。
        canteen_name: 食堂名称（必填）。
        stall_name: 档口名称（必填）。
        submitter_account: 提交者账号（必填）。
        price: 价格。
        image: 菜品图片文件。
        description: 菜品说明。
        tags: 标签，逗号分隔。
    返回说明：返回创建成功的提报记录。
    """
    dish_name = request.form.get('dish_name', '')
    canteen_name = request.form.get('canteen_name', '')
    stall_name = request.form.get('stall_name', '')
    submitter_account = request.form.get('submitter_account', '')
    price = request.form.get('price', '')
    description = request.form.get('description', '')
    tags_raw = request.form.get('tags', '')

    image_file = request.files.get('image')

    tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []

    service = DishSubmissionService()

    try:
        submission = service.create_submission(
            dish_name=dish_name,
            canteen_name=canteen_name,
            stall_name=stall_name,
            submitter_account=submitter_account,
            price=float(price) if price else None,
            image_file=image_file,
            description=description,
            tags=tags,
        )
        return jsonify({
            'code': 0,
            'message': '提报成功，请等待审核。',
            'data': submission,
            'trace_id': g.trace_id,
        }), 201
    except ValueError as e:
        return jsonify({
            'code': 'SUBMIT_422_001',
            'message': str(e),
            'trace_id': g.trace_id,
        }), 422
