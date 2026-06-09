from app.repositories.rant_repository import RantRepository
from app.entities.models import Rant as RantModel
from app.extensions import db


class RantService:
    def __init__(self, repository=None):
        self.repository = repository or RantRepository()

    def _rant_to_dict(self, rant):
        return {
            'id': rant.id,
            'canteenName': rant.canteen_name or '',
            'author': rant.author_account,
            'content': rant.content,
            'tag': rant.tag or '吐槽',
            'createdAt': rant.created_at.strftime('%H:%M') if rant.created_at else '',
            'status': rant.status or 'pending',
            'reason': rant.audit_reason or '',
        }

    def get_approved_rants(self):
        rants = db.session.query(RantModel).filter(
            RantModel.status == 'approved'
        ).order_by(RantModel.created_at.desc()).all()
        return [self._rant_to_dict(r) for r in rants]

    def get_all_rants(self):
        rants = db.session.query(RantModel).order_by(RantModel.created_at.desc()).all()
        return [self._rant_to_dict(r) for r in rants]

    def get_rants_by_status(self, status):
        rants = self.repository.get_rants_by_status(status)
        return [self._rant_to_dict(r) for r in rants]

    def create_rant(self, canteen_name, author_account, content, tag='吐槽'):
        if not author_account:
            raise ValueError('用户账号不能为空。')
        if not content or not content.strip():
            raise ValueError('吐槽内容不能为空。')

        rant = self.repository.create_rant(
            canteen_name=canteen_name,
            author_account=author_account,
            content=content.strip(),
            tag=tag or '吐槽',
        )
        db.session.commit()
        return self._rant_to_dict(rant)

    def update_rant_content(self, rant_id, **kwargs):
        allowed = {'canteen_name', 'content', 'tag'}
        updates = {}
        for key in allowed:
            if key in kwargs and kwargs[key] is not None:
                val = kwargs[key]
                if isinstance(val, str):
                    val = val.strip()
                updates[key] = val
        if not updates:
            raise ValueError('没有需要更新的字段。')
        success = self.repository.update_rant(rant_id, **updates)
        if not success:
            raise ValueError('吐槽记录不存在。')
        db.session.commit()
        rant = db.session.query(RantModel).filter(RantModel.id == rant_id).first()
        return self._rant_to_dict(rant)

    def audit_rant(self, rant_id, status, audit_reason, auditor_account):
        if status not in ('approved', 'rejected'):
            raise ValueError('审核状态只能是 approved 或 rejected。')
        if not audit_reason or not audit_reason.strip():
            raise ValueError('审核意见不能为空。')

        success = self.repository.update_rant_audit_result(
            rant_id=rant_id,
            status=status,
            audit_reason=audit_reason.strip(),
            auditor_account=auditor_account,
        )
        if not success:
            raise ValueError('吐槽记录不存在。')
        db.session.commit()
        return True
