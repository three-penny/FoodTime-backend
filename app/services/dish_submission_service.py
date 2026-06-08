"""
文件名：app/services/dish_submission_service.py
功能描述：菜品提报业务编排层，负责图片落盘、参数校验与提报记录创建。
作者：FoodTime Backend Team
创建时间：2026-05-23
"""
import os
import shutil
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

        image_url = current_app.config.get('DEFAULT_IMG_URL', '/api/v1/uploads/default_img/default.jpg')
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

        try:
            from app.services.points_service import PointsService
            from app.repositories.auth_repository import AuthRepository
            user = AuthRepository().find_by_account(submitter_account)
            if user:
                PointsService().add_points(user.id, 5, '上传菜品提报', 'upload')
        except Exception:
            pass

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

    def get_all_submissions(self) -> list[dict]:
        """查询所有提报记录（按创建时间倒序）。"""
        from app.entities.models import DishSubmission
        from app.extensions import db
        submissions = db.session.query(DishSubmission).order_by(DishSubmission.created_at.desc()).all()
        return [self._to_dict(s) for s in submissions]

    def audit_submission(self, submission_id: str, status: str, audit_reason: str, auditor_account: str) -> bool:
        """审核菜品提报工单。审核通过时自动创建对应菜品记录。"""
        if status not in ('approved', 'rejected'):
            raise ValueError('审核状态只能是 approved 或 rejected。')
        if not audit_reason or not audit_reason.strip():
            raise ValueError('审核意见不能为空。')

        from app.entities.models import DishSubmission, Canteen, Stall, Dish

        submission = db.session.query(DishSubmission).filter_by(id=submission_id).first()
        if not submission:
            raise ValueError('提报记录不存在。')

        submission.status = status
        submission.audit_reason = audit_reason.strip()
        submission.auditor_account = auditor_account

        if status == 'approved':
            self._create_dish_from_submission(submission)

        db.session.commit()
        return True

    def _create_dish_from_submission(self, submission) -> None:
        """审核通过时将投稿数据写入正式菜品表。"""
        from app.entities.models import Canteen, Stall, Dish

        canteen = db.session.query(Canteen).filter(
            Canteen.name == submission.canteen_name
        ).first()
        if not canteen:
            logger.warning('未找到食堂 "%s"，跳过菜品创建', submission.canteen_name)
            return

        stall_id = self._resolve_stall_id(canteen.id, submission.stall_name)
        dish_id = f'{canteen.id}-{submission.dish_name}'

        existing = db.session.query(Dish).filter_by(id=dish_id).first()
        if existing:
            logger.info('菜品 "%s" 已存在，跳过创建', dish_id)
            return

        dish_image_url = self._migrate_dish_image(submission)

        new_dish = Dish(
            id=dish_id,
            stall_id=stall_id,
            canteen_id=canteen.id,
            name=submission.dish_name,
            image_url=dish_image_url,
            price=submission.price,
            rating=0.0,
            description=submission.description or '',
            value_note='',
            tags=submission.tags or [],
            recommend_votes=0,
            avoid_votes=0,
        )
        db.session.add(new_dish)
        logger.info('审核通过：已创建菜品 "%s" (canteen=%s, stall=%s)', dish_id, canteen.id, stall_id)

    def _resolve_stall_id(self, canteen_id: str, stall_name: str) -> str:
        """查找或创建档口，返回档口 ID。"""
        from app.entities.models import Stall

        stall = db.session.query(Stall).filter(
            Stall.canteen_id == canteen_id,
            Stall.name == stall_name,
        ).first()
        if stall:
            return stall.id

        stall_id = f'{canteen_id}-{stall_name}'
        new_stall = Stall(
            id=stall_id,
            canteen_id=canteen_id,
            name=stall_name,
            avg_price='',
            best_time='',
            summary=f'用户投稿创建的档口：{stall_name}',
        )
        db.session.add(new_stall)
        db.session.flush()
        logger.info('自动创建档口 "%s" (id=%s)', stall_name, stall_id)
        return stall_id

    def _migrate_dish_image(self, submission) -> str:
        """将投稿图片复制到正式菜品图片目录，返回 API 可访问的 URL 路径。"""
        if not submission.image_url:
            return current_app.config.get('DEFAULT_IMG_URL', '/api/v1/uploads/default_img/default.jpg')

        if submission.image_url.startswith('/'):
            return submission.image_url

        src_dir = current_app.config['SUBMISSION_IMG_FOLDER']
        dst_dir = current_app.config['DISH_IMG_FOLDER']
        src_path = os.path.join(src_dir, submission.image_url)
        ext = submission.image_url.rsplit('.', 1)[-1] if '.' in submission.image_url else 'jpg'
        new_name = f'{uuid.uuid4().hex}.{ext}'
        dst_path = os.path.join(dst_dir, new_name)

        try:
            os.makedirs(dst_dir, exist_ok=True)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
                logger.info('图片已迁移: %s -> %s', src_path, dst_path)
            return f'/api/v1/images/dish/{new_name}'
        except OSError as e:
            logger.warning('图片迁移失败，使用默认图片: %s', e)
            return current_app.config.get('DEFAULT_IMG_URL', '/api/v1/uploads/default_img/default.jpg')

    def admin_create_submission(self, auditor_account: str, **kwargs) -> dict:
        """管理员直接创建提报并自动审核通过，同时创建菜品记录。"""
        submission = self.repository.create_submission(
            dish_name=kwargs.get('dish_name', '').strip(),
            canteen_name=kwargs.get('canteen_name', '').strip(),
            stall_name=kwargs.get('stall_name', '').strip(),
            price=kwargs.get('price'),
            image_url=kwargs.get('image_url', ''),
            description=kwargs.get('description', '').strip(),
            tags=kwargs.get('tags', []),
            submitter_account=kwargs.get('submitter_account', auditor_account),
        )
        db.session.flush()
        self.audit_submission(
            submission_id=submission.id,
            status='approved',
            audit_reason='管理员直接创建并审核通过',
            auditor_account=auditor_account,
        )
        return self._to_dict(submission)

    def update_submission_content(self, submission_id: str, **kwargs) -> dict:
        """更新提报内容。"""
        allowed = {'dish_name', 'canteen_name', 'stall_name', 'price', 'description', 'tags'}
        updates = {}
        for key in allowed:
            if key in kwargs and kwargs[key] is not None:
                val = kwargs[key]
                if isinstance(val, str):
                    val = val.strip()
                updates[key] = val
        if not updates:
            raise ValueError('没有需要更新的字段。')
        success = self.repository.update_submission(submission_id, **updates)
        if not success:
            raise ValueError('提报记录不存在。')
        db.session.commit()
        from app.entities.models import DishSubmission
        submission = db.session.query(DishSubmission).filter(DishSubmission.id == submission_id).first()
        return self._to_dict(submission)

    def _to_dict(self, submission) -> dict:
        image_url = submission.image_url or ''
        if image_url and not image_url.startswith('/'):
            image_url = f'/api/v1/uploads/submission_img/{image_url}'
        if not image_url:
            image_url = current_app.config.get('DEFAULT_IMG_URL', '/api/v1/uploads/default_img/default.jpg')
        return {
            'id': submission.id,
            'dish_name': submission.dish_name,
            'canteen_name': submission.canteen_name,
            'stall_name': submission.stall_name,
            'price': submission.price,
            'image_url': image_url,
            'description': submission.description,
            'tags': submission.tags,
            'submitter_account': submission.submitter_account,
            'status': submission.status,
            'audit_reason': submission.audit_reason,
            'created_at': submission.created_at.isoformat() if submission.created_at else None,
            'updated_at': submission.updated_at.isoformat() if submission.updated_at else None,
        }
