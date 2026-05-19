"""
文件名：app/repositories/dish_submission_repository.py
功能描述：菜品提报（UGC 上传与审核）业务域的底层数据库访问封装。
作者：郝炫斌
"""

from app.entities.models import DishSubmission
from app.extensions import db


class DishSubmissionRepository:
    """
    类职责：负责 dish_submissions 表的所有底层 SQL 映射与数据交互。
    使用场景：用户端上传新菜品、管理端按状态筛选待审/历史工单、管理员审批工单。
    依赖关系：依赖 SQLAlchemy 的 db.session。
    设计说明：采用仓储模式，仅拼装并执行数据流操作，不包含 db.session.commit() 事务提交，完全交由上层 Service 控制事务边界。
    """

    def create_submission(
        self,
        dish_name: str,
        canteen_name: str,
        stall_name: str,
        price: float,
        image_url: str,
        description: str,
        tags: list,
        submitter_account: str
    ) -> DishSubmission:
        """
        功能描述：在 dish_submissions 表中插入一条新的菜品提报记录。
        参数说明：
            dish_name: 用户填写的菜品名称。
            canteen_name: 菜品所在的食堂名称。
            stall_name: 菜品所在的档口名称。
            price: 菜品价格（允许为 None/Null）。
            image_url: 菜品现场图片的文件名或外链 URL。
            description: 菜品的详细文本描述说明。
            tags: 标签数组（在内部通过 JSON 字段存储）。
            submitter_account: 上传该菜品的普通用户账号。
        返回值说明：
            返回插入整行后对应的 DishSubmission ORM 模型对象，包含底层的自动生成的唯一主键 id。
        使用示例：
            submission = repo.create_submission("藤椒鸡丝拌面", "东区餐厅", "清爽麻香", 15.0, "img.jpg", "描述", ["拌面"], "2024211001")
        """
        # 利用 ORM 的默认值机制：status 默认为 'pending'，未指定的字段（如审核意见、管理员账号）自动为 None (Null)
        new_submission = DishSubmission(
            dish_name=dish_name,
            canteen_name=canteen_name,
            stall_name=stall_name,
            price=price,
            image_url=image_url,
            description=description,
            tags=tags,
            submitter_account=submitter_account
        )
        db.session.add(new_submission)
        # 执行 flush 以便让 SQLite 提前生成该行的唯一主键 id，方便 Service 层后续直接获取 id，但不提交事务
        db.session.flush()
        return new_submission

    def get_submissions_by_status(self, status: str) -> list[DishSubmission]:
        """
        功能描述：根据输入的状态，查询 dish_submissions 表中对应的全部完整行数据。
        参数说明：
            status: 提报工单的审核状态，建议传入值为：'pending'（待审核）、'approved'（通过）、'rejected'（驳回）。
        返回值说明：
            返回包含一整行所有信息的 DishSubmission ORM 模型对象列表。如果无匹配数据，返回空列表 []。
        """
        return db.session.query(DishSubmission).filter(DishSubmission.status == status).all()

    def update_audit_result(
        self,
        submission_id: str,
        status: str,
        audit_reason: str,
        auditor_account: str
    ) -> bool:
        """
        功能描述：根据提报工单的唯一 id，填充其审核状态、审核意见以及负责审批的管理员账号。
        参数说明：
            submission_id: 提报记录的唯一标识 (UUID)。
            status: 审批后的新状态（'approved' 或 'rejected'）。
            audit_reason: 管理员填写的审核意见、通过寄语或驳回原因文本。
            auditor_account: 判定该工单的管理员账号。
        返回值说明：
            返回布尔值。如果找到对应 id 记录并成功填充返回 True；如果该工单不存在，返回 False。
        使用示例：
            success = repo.update_audit_result("sub-uuid-001", "approved", "图片清晰，准予上线", "admin")
        """
        result = db.session.query(DishSubmission).filter(DishSubmission.id == submission_id).update(
            {
                "status": status,
                "audit_reason": audit_reason,
                "auditor_account": auditor_account
            },
            synchronize_session=False
        )
        return result > 0