"""
文件名：app/repositories/dining_display_repository.py
功能描述：餐饮展示业务域的底层数据库访问封装。
作者：郝炫斌
"""

from app.entities.models import Canteen, Stall, Dish
from app.extensions import db

class DiningDisplayRepository:
    """
    类职责：负责“食堂-档口-菜品”核心展示链路的所有数据库查询操作。
    使用场景：首页食堂推荐、食堂详情页渲染、高分菜品榜单展示。
    依赖关系：依赖 SQLAlchemy 的 db.session。
    设计说明：将 Canteen, Stall, Dish 作为餐饮展示域的聚合进行统一查询管理，避免代码横向散落。
    """

    def get_all_canteens(self) -> list[Canteen]:
        """
        功能描述：查询所有食堂的全部信息。
        返回值说明：
            返回 Canteen 模型对象的列表。若无数据则返回空列表。
        """
        return db.session.query(Canteen).all()

    def get_stalls_by_canteen_id(self, canteen_id: str) -> list[Stall]:
        """
        功能描述：根据食堂 ID 查询下属所有档口的全部信息。
        参数说明：
            canteen_id: 目标食堂的唯一标识。
        返回值说明：
            返回符合条件的 Stall 模型对象列表。
        """
        return db.session.query(Stall).filter(Stall.canteen_id == canteen_id).all()

    def get_dishes_by_stall_id(self, stall_id: str) -> list[Dish]:
        """
        功能描述：根据档口 ID 查询下属所有餐品的全部信息。
        参数说明：
            stall_id: 目标档口的唯一标识。
        返回值说明：
            返回符合条件的 Dish 模型对象列表。
        """
        return db.session.query(Dish).filter(Dish.stall_id == stall_id).all()

    def get_top_dishes(self, limit: int = 10) -> list[Dish]:
        """
        功能描述：查询评分排名前 N 的餐品全部信息。
        参数说明：
            limit: 限制返回的记录数，默认为 10。
        返回值说明：
            返回按 rating 降序排列的 Dish 模型对象列表。
        """
        return db.session.query(Dish).order_by(Dish.rating.desc()).limit(limit).all()

    def increment_dish_recommend_votes(self, dish_id: str) -> bool:
        """
        功能描述：将指定菜品的推荐人数 (recommend_votes) 加 1。
        参数说明：
            dish_id: 菜品的唯一标识。
        返回值说明：
            返回布尔值。如果菜品存在且更新成功返回 True，若菜品不存在返回 False。

        """
        # 执行原子更新，result 返回受影响的行数
        result = db.session.query(Dish).filter(Dish.id == dish_id).update(
            {"recommend_votes": Dish.recommend_votes + 1},
            synchronize_session=False
        )
        return result > 0

    def increment_dish_avoid_votes(self, dish_id: str) -> bool:
        """
        功能描述：将指定菜品的避雷人数 (avoid_votes) 加 1。
        参数说明：
            dish_id: 菜品的唯一标识。
        返回值说明：
            返回布尔值。如果菜品存在且更新成功返回 True，若菜品不存在返回 False。

        """
        result = db.session.query(Dish).filter(Dish.id == dish_id).update(
            {"avoid_votes": Dish.avoid_votes + 1},
            synchronize_session=False
        )
        return result > 0