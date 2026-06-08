"""
文件名：app/repositories/rant_repository.py
功能描述：吐槽墙模块（UGC 反馈与审核）业务域的底层数据库访问封装。
作者：郝炫斌
"""

from app.entities.models import Rant
from app.extensions import db


class RantRepository:
    """
    类职责：负责 rants 表的所有底层 SQL 映射与数据交互。
    使用场景：用户端发表吐槽、管理端按状态筛选待审/历史吐槽、管理员审批吐槽墙工单。
    依赖关系：依赖 SQLAlchemy 的 db.session。
    设计说明：采用仓储模式，仅拼装并执行数据流操作，不包含 db.session.commit() 事务提交，完全交由上层 Service 控制事务边界。
    """

    def create_rant(
        self,
        canteen_name: str,
        author_account: str,
        content: str,
        tag: str
    ) -> Rant:
        """
        功能描述：在 rants 表中插入一条新的用户吐槽反馈记录。
        参数说明：
            canteen_name: 用户吐槽的食堂名称（允许为 None/Null）。
            author_account: 发表吐槽的用户账号。
            content: 吐槽的具体文本内容。
            tag: 吐槽的分类标签（例如：'排队'、'口味'、'服务'等）。
        返回值说明：
            返回插入整行后对应的 Rant ORM 模型对象，包含底层自动生成的唯一主键 id。
        使用示例：
            new_rant = repo.create_rant("学一餐厅", "2024211001", "座位真的紧张，转了两圈。", "排队")
        """
        # 利用 ORM 的默认值机制：status 默认为 'pending'，未指定的字段（如审核意见、管理员账号）自动为 None (Null)
        new_rant = Rant(
            canteen_name=canteen_name,
            author_account=author_account,
            content=content,
            tag=tag
        )
        db.session.add(new_rant)
        db.session.flush()
        return new_rant

    def get_rants_by_status(self, status: str) -> list[Rant]:
        """
        功能描述：根据输入的状态，查询 rants 表中对应的全部完整行数据。
        参数说明：
            status: 吐槽记录的审核状态，可选值为：'pending'（待审核）、'approved'（通过）、'rejected'（驳回）。
        返回值说明：
            返回包含一整行所有信息的 Rant ORM 模型对象列表。如果无匹配数据，返回空列表 []。
        """
        return db.session.query(Rant).filter(Rant.status == status).all()

    def update_rant_audit_result(
        self,
        rant_id: str,
        status: str,
        audit_reason: str,
        auditor_account: str
    ) -> bool:
        """
        功能描述：根据吐槽记录的唯一 id，填充其审核状态、审核意见以及负责审批的管理员账号。
        参数说明：
            rant_id: 吐槽记录的唯一标识 (UUID)。
            status: 审批后的新状态（'approved' 或 'rejected'）。
            audit_reason: 管理员填写的审核意见或驳回原因文本。
            auditor_account: 判定该吐槽工单的管理员账号。
        返回值说明：
            返回布尔值。如果找到对应 id 记录并成功更新填充返回 True；如果该工单记录不存在，返回 False。
        使用示例：
            success = repo.update_rant_audit_result("rant-uuid-001", "approved", "内容合规，准予上墙", "admin")
        """
        result = db.session.query(Rant).filter(Rant.id == rant_id).update(
            {
                "status": status,
                "audit_reason": audit_reason,
                "auditor_account": auditor_account
            },
            synchronize_session=False
        )
        return result > 0

    def update_rant(self, rant_id: str, **kwargs) -> bool:
        result = db.session.query(Rant).filter(Rant.id == rant_id).update(
            kwargs, synchronize_session=False
        )
        return result > 0