"""
补充脚本：为所有食堂创建默认档口数据，匹配前端 mock 行为。
运行方式：在 seed.py 之后执行。
"""

import logging
from app import create_app
from app.extensions import db
from app.entities.models import Canteen, Stall, Dish, Review

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

SPOT_CANTEEN_IDS = ['xueyi', 'minghu', 'dongkuai', 'xueer', 'qingzhen', 'xuesi', 'liuyuan', 'jiaogong', 'dongqu', 'yimin']

DEFAULT_STALLS = [
    ("northwest-noodles", "西北面食", "¥12 - ¥20", "11:20 前", "主打热汤面、拌面和筋道面食",
     [("油泼扯面", 4.9, 15), ("牛肉拉面", 4.8, 18), ("臊子面", 4.7, 14), ("孜然羊肉拌面", 4.6, 20)]),
    ("fei-uncle-hunan", "费大叔湘菜", "¥16 - ¥26", "12:40 后", "偏下饭的小炒窗口，辣度直接",
     [("小炒黄牛肉饭", 4.9, 24), ("农家一碗香", 4.8, 22), ("剁椒鸡腿饭", 4.7, 21), ("湘味豆角肉末饭", 4.5, 18)]),
    ("shandong-cuisine", "山东菜", "¥13 - ¥22", "11:30 前", "口味偏家常，菜量实在",
     [("葱烧豆腐饭", 4.8, 14), ("酱爆鸡丁饭", 4.7, 19), ("糖醋里脊饭", 4.6, 21), ("白菜粉条炖肉", 4.5, 18)]),
    ("yunnan-fried-rice", "云南炒饭", "¥12 - ¥19", "13:00 后", "炒饭出餐快，香气足",
     [("云腿鸡蛋炒饭", 4.8, 16), ("菌菇牛肉炒饭", 4.7, 19), ("酸菜肉末炒饭", 4.6, 15), ("番茄鸡蛋炒饭", 4.4, 13)]),
    ("yunnan-rice-noodle", "云南米线", "¥14 - ¥24", "晚饭错峰", "米线汤底选择多",
     [("酸汤肥牛米线", 4.9, 23), ("番茄牛肉米线", 4.8, 22), ("菌菇鸡汤米线", 4.7, 20), ("麻辣小锅米线", 4.5, 18)]),
    ("grilled-pork-belly", "炙烤五花肉", "¥18 - ¥28", "11:15 前", "焦香肉类窗口",
     [("炙烤五花肉饭", 4.9, 26), ("黑椒鸡腿双拼饭", 4.8, 25), ("蒜香烤肉拌饭", 4.7, 23), ("照烧肥牛饭", 4.6, 24)]),
    ("xiaogu-malaban", "小谷姐姐麻辣烫", "¥16 - ¥30", "避开 12:00", "自选称重窗口，丰俭由人",
     [("招牌麻辣烫", 4.8, 24), ("番茄骨汤麻辣烫", 4.7, 23), ("麻酱拌烫菜", 4.6, 22), ("藤椒清汤烫菜", 4.5, 21)]),
    ("beef-soup", "牛肉汤", "¥15 - ¥25", "早餐后段", "热汤窗口，主打牛肉汤、粉丝和烧饼搭配",
     [("原汤牛肉粉丝", 4.8, 18), ("牛肉汤配烧饼", 4.7, 20), ("番茄牛肉汤饭", 4.6, 22), ("萝卜牛腩汤", 4.5, 24)]),
    ("cotti-coffee", "库迪咖啡", "¥9 - ¥18", "下午 15:00", "咖啡和轻食补给点",
     [("生椰拿铁", 4.8, 13), ("厚乳拿铁", 4.7, 12), ("美式咖啡", 4.6, 9), ("火腿芝士可颂", 4.4, 16)]),
]


def main():
    app = create_app()
    with app.app_context():
        user = db.session.query(Review).first()
        reviewer_id = user.user_id if user else None
        if not reviewer_id:
            logger.warning("未找到已有用户，使用默认用户 ID")
            from app.entities.models import User
            user = User.query.first()
            reviewer_id = user.id if user else None

        canteens = Canteen.query.all()
        spot_canteens = [c for c in canteens if c.id in SPOT_CANTEEN_IDS]
        other_canteens = [c for c in canteens if c.id not in SPOT_CANTEEN_IDS]

        total_stalls = 0
        total_dishes = 0

        for canteen in spot_canteens:
            for s_idx, (sid, sname, sprice, stime, ssummary, sdishes) in enumerate(DEFAULT_STALLS):
                existing = Stall.query.filter(Stall.id == f"{canteen.id}-{sid}").first()
                if existing:
                    continue
                stall_img = '档口01.webp' if s_idx % 2 == 0 else '档口02.jpg'
                stall = Stall(
                    id=f"{canteen.id}-{sid}",
                    canteen_id=canteen.id,
                    name=sname,
                    avg_price=sprice,
                    best_time=stime,
                    summary=ssummary,
                    image_url=stall_img
                )
                db.session.add(stall)
                db.session.flush()
                total_stalls += 1
                for d_idx, (dname, drating, dprice) in enumerate(sdishes):
                    long_desc = f"{dname} 我会把它放在{canteen.name}{sname}的稳定备选里：味道记忆点明确，出餐速度和价格都比较平衡。"
                    dish = Dish(
                        id=f"{canteen.id}-{sid}-dish-{d_idx + 1}",
                        stall_id=stall.id,
                        canteen_id=canteen.id,
                        name=dname,
                        price=dprice,
                        rating=drating,
                        description=long_desc,
                        value_note=sname,
                        tags=[sname],
                        image_url='番茄肥牛饭.jpg'
                    )
                    db.session.add(dish)
                    db.session.flush()
                    total_dishes += 1
                    if reviewer_id:
                        db.session.add(Review(dish_id=dish.id, user_id=reviewer_id, rating=drating, comment=dname))

        for canteen in other_canteens:
            for s_idx, (sid, sname, sprice, stime, ssummary, sdishes) in enumerate(DEFAULT_STALLS[:3]):
                existing = Stall.query.filter(Stall.id == f"{canteen.id}-{sid}").first()
                if existing:
                    continue
                stall_img = '档口01.webp' if s_idx % 2 == 0 else '档口02.jpg'
                stall = Stall(
                    id=f"{canteen.id}-{sid}",
                    canteen_id=canteen.id,
                    name=sname,
                    avg_price=sprice,
                    best_time=stime,
                    summary=ssummary,
                    image_url=stall_img
                )
                db.session.add(stall)
                db.session.flush()
                total_stalls += 1
                for d_idx, (dname, drating, dprice) in enumerate(sdishes[:3]):
                    long_desc = f"{dname} 我会把它放在{canteen.name}{sname}的稳定备选里。"
                    dish = Dish(
                        id=f"{canteen.id}-{sid}-dish-{d_idx + 1}",
                        stall_id=stall.id,
                        canteen_id=canteen.id,
                        name=dname,
                        price=dprice,
                        rating=drating,
                        description=long_desc,
                        value_note=sname,
                        tags=[sname],
                        image_url='番茄肥牛饭.jpg'
                    )
                    db.session.add(dish)
                    db.session.flush()
                    total_dishes += 1
                    if reviewer_id:
                        db.session.add(Review(dish_id=dish.id, user_id=reviewer_id, rating=drating, comment=dname))

        db.session.commit()
        logger.info(f"完成！新增 {total_stalls} 档口, {total_dishes} 菜品")
        logger.info(f"汇总: Canteens={Canteen.query.count()}, Stalls={Stall.query.count()}, Dishes={Dish.query.count()}, Reviews={Review.query.count()}")


if __name__ == '__main__':
    main()
