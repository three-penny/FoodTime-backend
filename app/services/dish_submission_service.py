"""
文件名：app/services/dish_submission_service.py
功能描述：菜品提报业务编排层，负责图片落盘、参数校验与提报记录创建。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from app.repositories.dish_submission_repository import DishSubmissionRepository

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


class DishSubmissionService:
    """菜品提报业务服务，编排图片保存与提报工单创建流程。"""

    def __init__(self, repository: DishSubmissionRepository | None = None):
        self.repository = repository or DishSubmissionRepository()

    def _allowed_file(self, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def _save_image(self, file) -> str:
        """保存上传图片到 data/submission_img/，返回文件名。"""
        upload_folder = current_app.config['SUBMISSION_IMG_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(upload_folder, unique_name)
        file.save(filepath)
        return unique_name

    def create_submission(
        self,
        dish_name: str,
        canteen_name: str,
        stall_name: str,
        submitter_account: str,
        price: float | None = None,
        image_file=None,
        description: str = '',
        tags: list | None = None,
    ) -> dict:
        """
        创建菜品提报。
        参数说明：
            dish_name: 菜品名称（必填）。
            canteen_name: 食堂名称（必填）。
            stall_name: 档口名称（必填）。
            submitter_account: 提交者账号（必填）。
            price: 价格。
            image_file: 上传的图片文件对象。
            description: 菜品描述。
            tags: 标签数组。
        返回值说明：
            返回创建成功的提报记录字典。
        异常抛出：
            ValueError: 参数校验失败。
        """
        dish_name = dish_name.strip()
        canteen_name = canteen_name.strip()
        stall_name = stall_name.strip()
        description = description.strip()
        tags = tags or []

        if not dish_name:
            raise ValueError('菜品名称不能为空。')
        if not canteen_name:
            raise ValueError('食堂名称不能为空。')
        if not stall_name:
            raise ValueError('档口名称不能为空。')
        if not submitter_account:
            raise ValueError('提交者账号不能为空。')

        image_url = ''
        if image_file and image_file.filename:
            if not self._allowed_file(image_file.filename):
                raise ValueError('不支持的图片格式，仅支持 png、jpg、jpeg、gif、webp、bmp。')
            image_url = self._save_image(image_file)

        submission = self.repository.create_submission(
            dish_name=dish_name,
            canteen_name=canteen_name,
            stall_name=stall_name,
            price=float(price) if price else None,
            image_url=image_url,
            description=description,
            tags=tags,
            submitter_account=submitter_account,
        )
        db.session.commit()

        return {
            'id': submission.id,
            'dish_name': submission.dish_name,
            'canteen_name': submission.canteen_name,
            'stall_name': submission.stall_name,
            'price': submission.price,
            'image_url': submission.image_url,
            'description': submission.description,
            'tags': submission.tags,
            'submitter_account': submission.submitter_account,
            'status': submission.status,
            'created_at': submission.created_at.isoformat() if submission.created_at else None,
        }

    def get_submissions_by_user(self, account: str) -> list[dict]:
        """查询指定用户的提报记录（按创建时间倒序）。"""
        submissions = self.repository.get_submissions_by_account(account)
        return [self._to_dict(s) for s in submissions]

    def _to_dict(self, submission) -> dict:
        return {
            'id': submission.id,
            'dish_name': submission.dish_name,
            'canteen_name': submission.canteen_name,
            'stall_name': submission.stall_name,
            'price': submission.price,
            'image_url': submission.image_url,
            'description': submission.description,
            'tags': submission.tags,
            'submitter_account': submission.submitter_account,
            'status': submission.status,
            'audit_reason': submission.audit_reason,
            'created_at': submission.created_at.isoformat() if submission.created_at else None,
            'updated_at': submission.updated_at.isoformat() if submission.updated_at else None,
        }
