"""
文件名：scripts/seed.py
功能描述：全量业务数据初始化与重置脚本，包含食堂、档口、菜品、用户及UGC数据。
作者：郝炫斌
创建时间：2026-05-19
设计说明：
    - 严禁使用 db.drop_all()，改为按依赖关系逆序 delete() 清理数据，保护表结构。
    - 采用标准 logging 替代 print。
    - 包含全局事务处理，任何异常均触发回滚。
"""

import uuid
import logging
from app import create_app
from app.extensions import db
from app.entities.models import (
    User, PointRecord, Canteen, Stall, Dish, Review, Rant, DishSubmission
)
from werkzeug.security import generate_password_hash


logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


CANTEENS_DATA = [

    {
        "id": "xueyi", "name": "学一餐厅", "short_name": "学一", "image_url": "食堂1.png",
        "rating": 4.6, "location": "明湖餐厅一层（十八号楼后）", "open_hours": "06:30 - 21:30",
        "avg_price": "人均 ¥12 - ¥18", "peak_queue": "11:45 - 12:15", "best_time": "11:20 前、12:40 后",
        "summary": "学一餐厅在明湖一层，是很多同学早午晚都会顺路去的基础型食堂。整体风格偏家常，菜品不花哨但很适合日常吃饭，赶课前来一份热菜配米饭很稳。公开上新菜单里出现过二代水煮鱼、三鲜烩肉片这类低油健康菜，适合作为“稳定不踩雷”的首页食堂。",
        "rant": "平时觉得普通、真赶时间又会第一个想起来的食堂。饭点排队不算轻松，但胜在出餐快。",
        "features": ["家常稳定", "出餐快", "价格友好", "适合赶课"],
        "signature_dishes": ["二代水煮鱼", "三鲜烩肉片"],
        "student_notes": ["明湖一层比较好找", "午饭高峰建议提前十分钟", "适合日常正餐"],
        "intro_blocks": [
            {"title": "食堂印象", "content": "学一更像交大学生的日常饭点，选择直接，吃完也不耽误后面的课。"},
            {"title": "推荐菜品", "content": "二代水煮鱼、三鲜烩肉片都是公开上新中出现过的菜，适合放进招牌菜。"},
            {"title": "排队建议", "content": "12 点左右人会明显变多，想舒服一点可以 11:20 前去。"}
        ]
    },
    {
        "id": "minghu", "name": "明湖餐厅", "short_name": "明湖", "image_url": "食堂2.png",
        "rating": 4.7, "location": "明湖二层（十八号楼后）", "open_hours": "10:30 - 21:30",
        "avg_price": "人均 ¥14 - ¥20", "peak_queue": "11:45 - 12:40", "best_time": "11:25 前、12:45 后",
        "summary": "明湖餐厅在明湖二层，适合想换点面食、饼类或者风味小吃的同学。分为八个档口，整体比其他更有“今天想吃点不一样”的感觉。适合做菜品列表页里的风味类食堂。",
        "rant": "明湖有时候会让人纠结，因为看着都想吃。缺点是高峰期上楼之后发现热门窗口已经排起来了。",
        "features": ["风味面食", "小吃丰富", "选择灵活", "适合换口味"],
        "signature_dishes": ["云南米线", "炒饭"],
        "student_notes": ["云南米线特别正宗", "面食窗口适合晚饭", "热门小吃饭点排队明显"],
        "intro_blocks": [
            {"title": "食堂定位", "content": "明湖适合做风味餐厅，不只是吃饱，也适合用户来找特色菜。"},
            {"title": "推荐菜品", "content": "西北面食和牛肉汤都适合做详情页展示菜。"},
            {"title": "体验建议", "content": "想慢慢选窗口的话，尽量避开刚下课的时间。"}
        ]
    },
    {
        "id": "dongkuai", "name": "东快餐厅", "short_name": "东快", "image_url": "食堂3.png",
        "rating": 4.7, "location": "明湖二层（十八号楼后）", "open_hours": "10:30 - 21:30",
        "avg_price": "人均 ¥16 - ¥28", "peak_queue": "11:45 - 12:15", "best_time": "11:20 前、12:40 后",
        "summary": "东快餐厅位于明湖二层，名字听起来像快餐，但实际更偏风味窗口集合。公开上新里有木桶鱼、一纸鸡这类菜，适合想吃热乎、口味重一点的同学。它很适合放在项目里做“风味快餐型”食堂。",
        "rant": "东快的问题是香味太明显，路过很难不被勾进去。钱包和减肥计划总有一个要妥协。",
        "features": ["风味快餐", "口味丰富", "适合聚餐", "菜量扎实"],
        "signature_dishes": ["木桶鱼", "一纸鸡"],
        "student_notes": ["明湖二层", "适合想吃重口味时来", "鱼类窗口饭点可能排队"],
        "intro_blocks": [
            {"title": "整体印象", "content": "东快更适合想吃风味菜的同学，比普通打饭更有选择感。"},
            {"title": "推荐菜品", "content": "木桶鱼、一纸鸡是公开菜单中出现过的真实菜品。"},
            {"title": "使用场景", "content": "适合午晚餐，也适合朋友一起点不同窗口互相尝。"}
        ]
    },
    {
        "id": "xueer", "name": "学二餐厅", "short_name": "学二", "image_url": "食堂4.png",
        "rating": 4.8, "location": "学活一层", "open_hours": "06:30 - 22:00",
        "avg_price": "人均 ¥13 - ¥24", "peak_queue": "11:40 - 12:20", "best_time": "11:15 前、12:45 后",
        "summary": "学二餐厅在学活一层，是学生活动中心附近最顺手的食堂之一。公开菜单里出现过红酸里脊和时蔬干拌面，既有下饭菜也有面食选择。这里适合做项目里的“人气主力食堂”，因为位置、容量和日常属性都很强。",
        "rant": "学二真的方便，但方便的代价就是饭点人多。你以为自己来得挺早，结果大家都这么想。",
        "features": ["位置核心", "人气高", "窗口多", "适合日常"],
        "signature_dishes": ["红酸里脊", "时蔬干拌面"],
        "student_notes": ["学活一层", "中午座位紧张", "适合赶活动或社团前吃"],
        "intro_blocks": [
            {"title": "食堂印象", "content": "学二是很典型的学生主力食堂，适合高频出现在首页推荐。"},
            {"title": "推荐菜品", "content": "红酸里脊适合配饭，时蔬干拌面适合想吃清爽一点的时候。"},
            {"title": "排队建议", "content": "11:40 后人流开始明显增加，12 点左右最挤。"}
        ]
    },
    {
        "id": "xuesan", "name": "学生三餐厅", "short_name": "学三", "image_url": "食堂5.png",
        "rating": 4.5, "location": "学活二层", "open_hours": "10:30 - 21:30",
        "avg_price": "人均 ¥14 - ¥25", "peak_queue": "11:45 - 12:15", "best_time": "11:20 前、12:40 后",
        "summary": "学生三餐厅在学活二层，后勤通知中也把它列为主校区餐厅。它适合和学二形成楼层联动：学二人多时可以上楼看看学三。项目里可以把它定位为学活区域的补充型风味餐厅。",
        "rant": "有时候不是一开始就想去学三，而是学二太挤了才上楼。结果吃完发现，其实也挺香。",
        "features": ["学活二层", "风味补充", "选择灵活", "适合错峰"],
        "signature_dishes": ["风味盖饭", "干拌面", "小炒套餐"],
        "student_notes": ["学二排队长时可上楼", "适合午晚餐", "具体窗口可后续再细分"],
        "intro_blocks": [
            {"title": "食堂定位", "content": "学三适合和学二一起作为学活片区的数据展示。"},
            {"title": "点餐建议", "content": "可以按窗口类型补充盖饭、面食、小炒等菜品。"},
            {"title": "数据备注", "content": "公开资料能确认餐厅存在和位置，具体菜品建议后续校内实拍补全。"}
        ]
    },
    {
        "id": "qingzhen", "name": "清真餐厅", "short_name": "清真", "image_url": "食堂6.png",
        "rating": 4.7, "location": "学活三层", "open_hours": "06:30 - 21:30",
        "avg_price": "人均 ¥15 - ¥28", "peak_queue": "11:40 - 12:15", "best_time": "11:15 前、12:40 后",
        "summary": "清真餐厅位于学活三层，主要服务有清真饮食需求的师生，也适合想换口味的同学。位置和功能都很明确，项目里建议单独建食堂条目，不要混进普通学活餐厅。",
        "rant": "清真餐厅属于目标很明确的选择，想吃的时候会专门上三层。饭点热门窗口也会排队。",
        "features": ["清真餐饮", "学活三层", "需求明确", "正餐友好"],
        "signature_dishes": ["牛肉类套餐", "羊肉丸子", "清真盖饭"],
        "student_notes": ["尊重清真餐饮规范", "适合单独筛选", "饭点建议提前"],
        "intro_blocks": [
            {"title": "餐厅特色", "content": "清真餐厅适合有清真饮食需求的师生，也适合想换口味的人。"},
            {"title": "页面建议", "content": "建议在筛选项里增加“清真”标签，方便用户快速找到。"},
            {"title": "用餐提示", "content": "午饭高峰排队明显，建议提前或错峰。"}
        ]
    },
    {
        "id": "xuesi", "name": "学四餐厅", "short_name": "学四", "image_url": "食堂1.png",
        "rating": 4.7, "location": "嘉园东侧", "open_hours": "06:30 - 21:30",
        "avg_price": "人均 ¥13 - ¥25", "peak_queue": "11:45 - 12:10",
        "best_time": "11:20 前、12:35 后",
        "summary": "学四餐厅位于嘉园东侧，是宿舍区附近很有存在感的食堂。公开上新菜品里有墩子肉、菠萝鱼，风格偏家常但也有记忆点。适合做“宿舍附近常去”的食堂条目。",
        "rant": "学四就是那种吃久了会有感情的地方。它不一定每次惊艳，但你饿的时候它很可靠。",
        "features": ["靠近嘉园", "家常实在", "学生常去", "性价比高"],
        "signature_dishes": ["墩子肉", "菠萝鱼"],
        "student_notes": ["嘉园附近同学常去", "中午座位紧张", "晚饭体验更舒服"],
        "intro_blocks": [
            {"title": "食堂印象", "content": "学四适合写成“生活感很强”的食堂，真实感会比较好。"},
            {"title": "推荐菜品", "content": "墩子肉和菠萝鱼都来自公开上新菜单。"},
            {"title": "排队建议", "content": "中午高峰要么早点来，要么干脆 12:35 后再来。"}
        ]
    },
    {
        "id": "xuesi_fengwei", "name": "学四风味餐厅", "short_name": "学四风味", "image_url": "食堂2.png",
        "rating": 4.6, "location": "学四二层", "open_hours": "10:30 - 21:30",
        "avg_price": "人均 ¥15 - ¥28", "peak_queue": "11:45 - 12:15", "best_time": "11:20 前、12:45 后",
        "summary": "学四风味餐厅在后勤通知中出现，位置为学四二层。它适合和学四餐厅区分开：一层偏日常正餐，二层偏风味选择。项目里可以把它做成同一区域下的另一个食堂卡片。",
        "rant": "学四风味适合“不想吃普通饭”的时候去。缺点是饭点上二层也不一定能逃过排队。",
        "features": ["风味窗口", "学四二层", "适合换口味", "选择多"],
        "signature_dishes": ["风味面食", "盖饭套餐", "特色小吃"],
        "student_notes": ["和学四餐厅分开建数据", "适合晚饭", "菜品后续可按窗口补充"],
        "intro_blocks": [
            {"title": "数据定位", "content": "建议不要和学四餐厅合并，风味餐厅可以独立展示。"},
            {"title": "推荐场景", "content": "适合想换口味，但又不想走远的嘉园附近同学。"},
            {"title": "备注", "content": "具体菜品需要后续按窗口继续采集。"}
        ]
    },
    {
        "id": "liuyuan", "name": "留园餐厅", "short_name": "留园", "image_url": "食堂3.png",
        "rating": 4.8, "location": "学四北侧", "open_hours": "10:30 - 20:00",
        "avg_price": "人均 ¥18 - ¥35",
        "peak_queue": "11:45 - 12:20",
        "best_time": "12:45 后、17:30 前",
        "summary": "留园餐厅位于学四北侧，它的菜品相对更精致，公开上新中出现过柠檬猪手、川味凉粉鸡。适合项目里做“品质更高、价格略高”的食堂。",
        "rant": "留园好吃是好吃，就是钱包也会更有感觉。适合偶尔改善伙食，不太适合天天无脑冲。",
        "features": ["菜品精致", "环境较安静", "价格略高", "适合改善伙食"],
        "signature_dishes": ["柠檬猪手", "川味凉粉鸡"],
        "student_notes": ["非常清淡", "中午只允许教工用餐", "适合错峰体验"],
        "intro_blocks": [
            {"title": "食堂印象", "content": "留园非常清淡、健康，但是价格较贵"},
            {"title": "推荐菜品", "content": "柠檬猪手和川味凉粉鸡都是公开上新菜品。"},
            {"title": "使用提示", "content": "注意：只有晚上给学生开放”。"}
        ]
    },
    {
        "id": "jiaogong", "name": "教工餐厅", "short_name": "教工", "image_url": "食堂4.png",
        "rating": 4.7, "location": "留园北侧", "open_hours": "10:30 - 20:00",
        "avg_price": "人均 ¥18 - ¥36",
        "peak_queue": "11:40 - 12:20",
        "best_time": "12:45 后、17:20 前",
        "summary": "教工餐厅位于留园北侧，属性上更偏教职工餐厅，但也适合做“精致健康、价格略高”的特殊餐厅展示。",
        "rant": "教工餐厅看起来总有一种“今天吃得正式一点”的感觉。学生去之前最好先确认开放时间。",
        "features": ["偏教工属性", "菜品精致", "低油低盐", "价格略高"],
        "signature_dishes": ["泰汁鱼条", "鲁大仙鸡腿"],
        "student_notes": ["留园北侧", "开放情况以校内通知为准", "适合改善伙食"],
        "intro_blocks": [
            {"title": "餐厅定位", "content": "教工餐厅建议在数据里标注为偏教工属性，避免学生误解为全天普通开放。"},
            {"title": "推荐菜品", "content": "泰汁鱼条、鲁大仙鸡腿可作为真实菜品展示。"},
            {"title": "页面提示", "content": "详情页可加入“部分时段可能面向教职工”的提示。"}
        ]
    },
    {
        "id": "xueyuan_dahuo", "name": "学苑大伙餐厅", "short_name": "学苑大伙", "image_url": "食堂5.png",
        "rating": 4.8, "location": "学苑大门左拐", "open_hours": "06:30 - 21:30",
        "avg_price": "人均 ¥13 - ¥25", "peak_queue": "11:45 - 12:20", "best_time": "11:20 前、12:50 后",
        "summary": "学苑大伙餐厅位于学苑大门左拐，是学苑片区的基础型食堂。公开上新菜单里出现过小碗杂粮饭、鲜果脆皮肉，既有健康主食也有酸甜口热菜。适合研究生、公寓区同学日常就餐。",
        "rant": "学苑大伙就是那种住得近会经常吃的地方。菜不一定每天都惊喜，但离得近这件事太加分了。",
        "features": ["学苑片区", "日常正餐", "主食友好", "适合常吃"],
        "signature_dishes": ["小碗杂粮饭", "鲜果脆皮肉"],
        "student_notes": ["学苑大门左拐", "适合学苑公寓同学", "饭点建议错峰"],
        "intro_blocks": [
            {"title": "食堂印象", "content": "学苑大伙适合做学苑片区的主力食堂。"},
            {"title": "推荐菜品", "content": "小碗杂粮饭和鲜果脆皮肉来自公开上新菜单。"},
            {"title": "使用场景", "content": "适合日常三餐，尤其适合住在学苑附近的同学。"}
        ]
    },
    {
        "id": "xueyuan_qingzhen", "name": "学苑清真餐厅", "short_name": "学苑清真", "image_url": "食堂6.png",
        "rating": 4.8, "location": "学苑大门左拐", "open_hours": "06:30 - 21:30",
        "avg_price": "人均 ¥15 - ¥28", "peak_queue": "11:45 - 12:15", "best_time": "11:20 前、12:45 后",
        "summary": "学苑清真餐厅属于学苑片区的清真餐饮选择。公开菜单里出现过烩羊肉丸子和春饼套餐，适合有清真饮食需求的同学，也适合想在学苑附近换口味的人。",
        "rant": "学苑清真很适合固定需求的同学收藏，住学苑附近的话会觉得特别方便。",
        "features": ["清真餐饮", "学苑片区", "正餐友好", "需求明确"],
        "signature_dishes": ["烩羊肉丸子", "春饼套餐"],
        "student_notes": ["注意清真餐饮规范", "适合单独加标签", "饭点建议提前"],
        "intro_blocks": [
            {"title": "餐厅特色", "content": "学苑清真建议单独建数据，不要并入学苑大伙。"},
            {"title": "推荐菜品", "content": "烩羊肉丸子、春饼套餐可作为真实菜品。"},
            {"title": "页面建议", "content": "可以加“清真”“学苑片区”“正餐”三个标签。"}
        ]
    },
    {
        "id": "xueyuan_xican", "name": "学苑西餐厅", "short_name": "学苑西餐", "image_url": "食堂1.png",
        "rating": 4.6, "location": "学苑大门左拐", "open_hours": "10:30 - 20:30",
        "avg_price": "人均 ¥16 - ¥32", "peak_queue": "11:50 - 12:20", "best_time": "11:30 前、13:00 后",
        "summary": "学苑西餐厅位于学苑片区，公开上新菜单中出现过司康糕点、金牌黄油面包。它适合做轻食、面包、简餐类餐厅，和普通大伙饭区分明显。页面上可以做得更年轻一点。",
        "rant": "学苑西餐适合想吃点“不像食堂饭”的时候去，但真饿的时候可能还是会想加点主食。",
        "features": ["西式简餐", "面包糕点", "适合轻食", "学苑片区"],
        "signature_dishes": ["司康糕点", "金牌黄油面包"],
        "student_notes": ["适合下午加餐", "价格略高于普通大伙", "可以做轻食分类"],
        "intro_blocks": [
            {"title": "食堂定位", "content": "学苑西餐厅适合作为轻食/西式简餐类餐厅展示。"},
            {"title": "推荐菜品", "content": "司康糕点和金牌黄油面包是公开上新菜单中出现过的品类。"},
            {"title": "页面建议", "content": "可以在详情页里突出“下午加餐”“面包糕点”“轻食”。"}
        ]
    },
    {
        "id": "dongqu", "name": "东区餐厅", "short_name": "东区", "image_url": "食堂2.png",
        "rating": 4.6, "location": "东区操场西侧", "open_hours": "07:00 - 21:30",
        "avg_price": "人均 ¥13 - ¥18", "peak_queue": "11:45 - 12:15",
        "best_time": "11:20 前、12:40 后",
        "summary": "东区餐厅位于东区操场西侧，是东校区同学最方便的日常食堂。热门档口有烤盘饭和小份菜，适合做东校区基础食堂。它的核心优势不是网红，而是近、快、稳定。",
        "rant": "对东区同学来说就是刚需。不是每次都惊艳，但下楼能吃上热饭就很重要。",
        "features": ["东校区", "距离方便", "日常稳定", "正餐小吃都有"],
        "signature_dishes": ["蜜雪冰城", "麻辣烫"],
        "student_notes": ["东区操场西侧", "适合东校区同学", "午饭高峰人多"],
        "intro_blocks": [
            {"title": "食堂印象", "content": "东区餐厅适合做东校区主力食堂，强调便利和稳定。"},
            {"title": "推荐菜品", "content": "小份菜味道不错，还有蜜雪冰城"},
            {"title": "使用场景", "content": "适合日常三餐，尤其适合不想跑主校区和点外卖的同学。"}
        ]
    },
    {
        "id": "dongqu_qingzhen", "name": "东区清真餐厅", "short_name": "东区清真", "image_url": "食堂3.png",
        "rating": 4.7, "location": "东区餐厅东北侧一层", "open_hours": "06:30 - 21:30",
        "avg_price": "人均 ¥15 - ¥28", "peak_queue": "11:45 - 12:15", "best_time": "11:20 前、12:45 后",
        "summary": "东区清真餐厅位于东区餐厅东北侧一层，是东区的清真餐饮选择。公开菜单里出现过豆花时蔬和牛肉爆三丁，适合做清真与东校区双标签。对于住在东区、有清真饮食需求的同学来说很实用。",
        "rant": "东区清真胜在不用跨校区找清真餐。饭点排队有，但比跑远路强多了。",
        "features": ["东区清真", "位置明确", "牛肉菜品", "正餐友好"],
        "signature_dishes": ["豆花时蔬", "牛肉爆三丁"],
        "student_notes": ["东区餐厅东北侧一层", "适合清真需求用户筛选", "午餐建议提前"],
        "intro_blocks": [
            {"title": "餐厅特色", "content": "东区清真餐厅适合在筛选里同时打上“东区”和“清真”标签。"},
            {"title": "推荐菜品", "content": "豆花时蔬、牛肉爆三丁可作为真实菜品展示。"},
            {"title": "页面提示", "content": "建议和东区餐厅分开建条目，方便用户按饮食需求查找。"}
        ]
    },
    {
        "id": "yimin", "name": "益民餐厅", "short_name": "益民", "image_url": "食堂4.png",
        "rating": 4.4, "location": "明湖东侧家属区内 / 主校区东门外",
        "open_hours": "10:30 - 19:30",
        "avg_price": "人均 ¥16 - ¥30",
        "peak_queue": "11:45 - 12:30",
        "best_time": "11:25 前、12:40 后",
        "summary": "益民餐厅位置与家属区内，相较于学生食堂，更像社区型餐厅，有小吃和点菜两种形式，明档现钞、锅气十足",
        "rant": "益民不是最热闹的学生食堂，但胜在人少一点、节奏慢一点。适合不想挤大食堂的时候去。",
        "features": ["家属区附近", "相对安静", "适合点菜", "人流较稳"],
        "signature_dishes": ["家常小炒", "盖饭套餐", "炸串"],
        "student_notes": ["东北菜", "适合错峰", "位置别和明湖主楼混淆"],
        "intro_blocks": [
            {"title": "食堂定位", "content": "益民餐厅适合做家属区附近的补充型餐厅。"},
            {"title": "推荐菜品", "content": "有很多经典东北菜，锅包肉、溜肉段都很好吃"},
            {"title": "备注", "content": "点菜后记得报桌号"}
        ]
    }
]


DEFAULT_STALLS = [
    {
        "id": "northwest-noodles", "name": "西北面食", "avg_price": "¥12 - ¥20", "best_time": "11:20 前",
        "summary": "主打热汤面、拌面和筋道面食，适合想吃一碗扎实主食的时候。",
        "target_canteen": "minghu",
        "dishes": [
            {"name": "油泼扯面", "rating": 4.9, "price": 15, "comment": "辣香够直，面条筋道，适合赶课前快速补能量。"},
            {"name": "牛肉拉面", "rating": 4.8, "price": 18, "comment": "汤底清亮，牛肉片给得稳，冬天很加分。"},
            {"name": "臊子面", "rating": 4.7, "price": 14, "comment": "酸香开胃，饭点排队也值得等一小会儿。"},
            {"name": "孜然羊肉拌面", "rating": 4.6, "price": 20, "comment": "香味很冲，适合想吃重口味的晚上。"}
        ]
    },
    {
        "id": "fei-uncle-hunan", "name": "费大叔湘菜", "avg_price": "¥16 - ¥26", "best_time": "12:40 后",
        "summary": "偏下饭的小炒窗口，辣度直接，适合米饭党和重口味同学。",
        "target_canteen": "dongkuai",
        "dishes": [
            {"name": "小炒黄牛肉饭", "rating": 4.9, "price": 24, "comment": "锅气足，辣度醒神，下午课不会犯困。"},
            {"name": "农家一碗香", "rating": 4.8, "price": 22, "comment": "鸡蛋和肉片都下饭，是窗口里的稳定选项。"},
            {"name": "剁椒鸡腿饭", "rating": 4.7, "price": 21, "comment": "剁椒香气明显，鸡腿比预期更嫩。"},
            {"name": "湘味豆角肉末饭", "rating": 4.5, "price": 18, "comment": "价格友好，适合不想花太多的时候。"}
        ]
    },
    {
        "id": "shandong-cuisine", "name": "山东菜", "avg_price": "¥13 - ¥22", "best_time": "11:30 前",
        "summary": "口味偏家常，菜量实在，适合想吃热菜配米饭的日常正餐。",
        "target_canteen": "xueyi",
        "dishes": [
            {"name": "葱烧豆腐饭", "rating": 4.8, "price": 14, "comment": "豆腐入味，葱香很稳，性价比不错。"},
            {"name": "酱爆鸡丁饭", "rating": 4.7, "price": 19, "comment": "咸香下饭，适合不知道吃什么的时候点。"},
            {"name": "糖醋里脊饭", "rating": 4.6, "price": 21, "comment": "酸甜口明显，外壳脆度看出锅时间。"},
            {"name": "白菜粉条炖肉", "rating": 4.5, "price": 18, "comment": "热乎朴素，适合冷天慢慢吃。"}
        ]
    },
    {
        "id": "yunnan-fried-rice", "name": "云南炒饭", "avg_price": "¥12 - ¥19", "best_time": "13:00 后",
        "summary": "炒饭出餐快，香气足，是赶时间但又想吃热乎饭的选择。",
        "target_canteen": "xuesi_fengwei",
        "dishes": [
            {"name": "云腿鸡蛋炒饭", "rating": 4.8, "price": 16, "comment": "火腿咸香明显，米粒粒粒分明。"},
            {"name": "菌菇牛肉炒饭", "rating": 4.7, "price": 19, "comment": "菌香和牛肉都在线，适合当晚饭。"},
            {"name": "酸菜肉末炒饭", "rating": 4.6, "price": 15, "comment": "酸菜提味，越吃越顺口。"},
            {"name": "番茄鸡蛋炒饭", "rating": 4.4, "price": 13, "comment": "清爽不腻，适合想吃轻一点的时候。"}
        ]
    },
    {
        "id": "yunnan-rice-noodle", "name": "云南米线", "avg_price": "¥14 - ¥24", "best_time": "晚饭错峰",
        "summary": "米线汤底选择多，酸汤和菌汤都适合做晚课后的热汤补给。",
        "target_canteen": "qingzhen",
        "dishes": [
            {"name": "酸汤肥牛米线", "rating": 4.9, "price": 23, "comment": "酸香开胃，肥牛量稳定，是窗口王牌。"},
            {"name": "番茄牛肉米线", "rating": 4.8, "price": 22, "comment": "汤底浓但不腻，适合不吃辣的同学。"},
            {"name": "菌菇鸡汤米线", "rating": 4.7, "price": 20, "comment": "鲜味柔和，晚饭吃很舒服。"},
            {"name": "麻辣小锅米线", "rating": 4.5, "price": 18, "comment": "辣感直接，适合想出汗的时候。"}
        ]
    },
    {
        "id": "grilled-pork-belly", "name": "炙烤五花肉", "avg_price": "¥18 - ¥28", "best_time": "11:15 前",
        "summary": "焦香肉类窗口，适合想吃烤肉饭、拌饭和高蛋白正餐的时候。",
        "target_canteen": "liuyuan",
        "dishes": [
            {"name": "炙烤五花肉饭", "rating": 4.9, "price": 26, "comment": "焦边香气明显，配泡菜刚好解腻。"},
            {"name": "黑椒鸡腿双拼饭", "rating": 4.8, "price": 25, "comment": "肉量足，适合训练后补一顿。"},
            {"name": "蒜香烤肉拌饭", "rating": 4.7, "price": 23, "comment": "蒜香很上头，拌开后每口都有味。"},
            {"name": "照烧肥牛饭", "rating": 4.6, "price": 24, "comment": "甜咸口稳定，适合不想踩雷的时候。"}
        ]
    },
    {
        "id": "xiaogu-malaban", "name": "小谷姐姐麻辣烫", "avg_price": "¥16 - ¥30", "best_time": "避开 12:00",
        "summary": "自选称重窗口，丰俭由人，适合想自己控制菜量和口味的时候。",
        "target_canteen": "dongqu",
        "dishes": [
            {"name": "招牌麻辣烫", "rating": 4.8, "price": 24, "comment": "汤底香，丸子和青菜搭配很稳。"},
            {"name": "番茄骨汤麻辣烫", "rating": 4.7, "price": 23, "comment": "番茄汤底更柔和，不吃辣也能点。"},
            {"name": "麻酱拌烫菜", "rating": 4.6, "price": 22, "comment": "麻酱浓，适合想吃干拌口的时候。"},
            {"name": "藤椒清汤烫菜", "rating": 4.5, "price": 21, "comment": "藤椒香气清爽，吃完负担小。"}
        ]
    },
    {
        "id": "beef-soup", "name": "牛肉汤", "avg_price": "¥15 - ¥25", "best_time": "早餐后段",
        "summary": "热汤窗口，主打牛肉汤、粉丝和烧饼搭配，适合早午餐过渡。",
        "target_canteen": "xueer",
        "dishes": [
            {"name": "原汤牛肉粉丝", "rating": 4.8, "price": 18, "comment": "汤头热乎，粉丝吸味，早课后很合适。"},
            {"name": "牛肉汤配烧饼", "rating": 4.7, "price": 20, "comment": "汤和烧饼组合扎实，一份能顶很久。"},
            {"name": "番茄牛肉汤饭", "rating": 4.6, "price": 22, "comment": "酸甜汤底配米饭，适合胃口一般的时候。"},
            {"name": "萝卜牛腩汤", "rating": 4.5, "price": 24, "comment": "萝卜吸汤，牛腩软烂度看当天火候。"}
        ]
    },
    {
        "id": "cotti-coffee", "name": "库迪咖啡", "avg_price": "¥9 - ¥18", "best_time": "下午 15:00",
        "summary": "咖啡和轻食补给点，适合自习、赶作业或饭后买一杯提神。",
        "target_canteen": "xueyuan_xican",
        "dishes": [
            {"name": "生椰拿铁", "rating": 4.8, "price": 13, "comment": "椰香明显，冰杯更适合下午提神。"},
            {"name": "厚乳拿铁", "rating": 4.7, "price": 12, "comment": "奶感重，适合不想喝太苦的时候。"},
            {"name": "美式咖啡", "rating": 4.6, "price": 9, "comment": "直接、便宜、提神，适合ddl前。"},
            {"name": "火腿芝士可颂", "rating": 4.4, "price": 16, "comment": "适合垫肚子，不建议当正餐主力。"}
        ]
    }
]


SPECIFIC_DISHES = [
    {"name": '红烧牛肉面', "canteenId": 'xueyuan_dahuo', "stall": '一碗顶一顿', "rating": 4.9,
     "comment": '阿姨今天给肉给得很实在，记住这班人。', "price": 19},
    {"name": '黑椒鸡腿饭', "canteenId": 'xueyuan_dahuo', "stall": '肉量够狠', "rating": 4.8,
     "comment": '别在 12 点后去，晚 10 分钟就得排半小时。', "price": 22},
    {"name": '麻辣香锅', "canteenId": 'xuesi', "stall": '自选热锅', "rating": 4.6,
     "comment": '挑菜别贪多，称重那一刻会心痛。', "price": 26},
    {"name": '番茄肥牛饭', "canteenId": 'jiaogong', "stall": '酸甜稳妥', "rating": 4.8,
     "comment": '课间冲过去五分钟拿到，效率党福音。', "price": 18},
    {"name": '鸡胸沙拉碗', "canteenId": 'jiaogong', "stall": '轻食窗口', "rating": 4.5,
     "comment": '健身搭子聚会指定款。', "price": 16},
    {"name": '香菇鸡肉饭', "canteenId": 'xueyi', "stall": '家常盖饭', "rating": 4.6,
     "comment": '饿狠了就点这份，基本不会后悔。', "price": 17},
    {"name": '酸汤米线', "canteenId": 'qingzhen', "stall": '夜宵首选', "rating": 4.7,
     "comment": '考试周晚上最常见的“续命套餐”。', "price": 20},
    {"name": '藤椒鸡丝面', "canteenId": 'dongqu', "stall": '清爽麻香', "rating": 4.6,
     "comment": '第一口平平，后劲很上头。', "price": 15},
    {"name": '牛肉煲仔饭', "canteenId": 'liuyuan', "stall": '锅气略贵', "rating": 4.7,
     "comment": '锅底脆感看师傅手法，偶尔会翻车。', "price": 24},
    {"name": '宫保鸡丁饭', "canteenId": 'dongkuai', "stall": '下饭小炒', "rating": 4.5,
     "comment": '分量看心情，遇到手稳阿姨能开心一整天。', "price": 18},
    {"name": '番茄鸡蛋面', "canteenId": 'minghu', "stall": '热汤面', "rating": 4.3,
     "comment": '考试周压力大时，别对它期待太高。', "price": 13},
    {"name": '酥皮鱼排饭', "canteenId": 'xuesi', "stall": '炸物窗口', "rating": 4.4,
     "comment": '运气好是惊喜，运气差是复盘素材。', "price": 21}
]

DISH_IMAGE_MAPPING = {
    '红烧牛肉面': '红烧牛肉面.jpg',
    '黑椒鸡腿饭': '黑胶鸡腿饭.png',
    '番茄肥牛饭': '番茄肥牛饭.jpg',
    '酸汤米线': '酸汤米线.png',
    '牛肉煲仔饭': '煲仔饭.webp',
}


RANTS_DATA = [
    {'canteen_id': 'xueyi', 'author': '2024211001', 'content': '午高峰队伍移动很快，但座位真的紧张，端着餐盘转了两圈。',
     'tag': '排队', 'status': 'approved'},
    {'canteen_id': 'minghu', 'author': '2024211012',
     'content': '酸汤米线今天汤底在线，就是窗口前面同学选择困难，排队被迫读完一章书。', 'tag': '口味',
     'status': 'approved'},
    {'canteen_id': 'dongqu', 'author': '2024211033',
     'content': '烤盘饭香味很强，路过不买有点需要意志力。', 'tag': '香味',
     'status': 'approved'},
    {'canteen_id': 'liuyuan', 'author': '2024211008',
     'content': '晚上人少一点，环境舒服，但价格也确实更有存在感。',
     'tag': '价格', 'status': 'approved'},
    {'canteen_id': 'dongqu', 'author': '2024211033',
     'content': '二楼某窗口今天出餐慢了不少，希望能补一个预计等待时间提示。', 'tag': '服务', 'status': 'pending'}
]

SUBMISSIONS_DATA = [
    {'dish_name': '藤椒鸡丝拌面', 'canteen_name': '东区餐厅', 'stall_name': '清爽麻香', 'price': 15,
     'submitter': '2024211001', 'status': 'pending', 'desc': '东区餐厅清爽麻香档口新增拌面类菜品'},
    {'dish_name': '番茄肥牛盖饭', 'canteen_name': '教工餐厅', 'stall_name': '酸甜稳定', 'price': 18,
     'submitter': '2024211008', 'status': 'approved', 'desc': '教工餐厅酸甜稳定档口新增盖饭类菜品',
     'reason': '图片清晰，描述完整，已进入推荐池。'},
    {'dish_name': '夜宵麻辣烫', 'canteen_name': '明湖餐厅', 'stall_name': '小锅米线旁', 'price': 22,
     'submitter': '2024211012', 'status': 'rejected', 'desc': '明湖餐厅自选类菜品投稿',
     'reason': '图片过暗，无法确认菜品细节，请重新上传。'}
]


def create_long_comment(dish_comment, canteen_name, stall_name):
    return f"{dish_comment} 我会把它放在{canteen_name}{stall_name}的稳定备选里：味道记忆点明确，出餐速度和价格都比较平衡，饭点排队能接受；如果想吃刚出锅的口感，建议错开最高峰再去。"


def seed_data():
    app = create_app()
    with app.app_context():
        try:
            logger.info("正在安全清理旧数据...")

            db.session.query(DishSubmission).delete()
            db.session.query(Rant).delete()
            db.session.query(Review).delete()
            db.session.query(Dish).delete()
            db.session.query(Stall).delete()
            db.session.query(Canteen).delete()
            db.session.query(PointRecord).delete()
            db.session.query(User).delete()
            db.session.commit()

            logger.info("灌入测试用户基础数据...")
            users = [
                User(account='admin', password_hash=generate_password_hash('123456'), nickname='审核管理员',
                     role='admin', account_status='active', current_points=999, total_earned_points=999,
                     total_used_points=0),
                User(account='2024211001', password_hash=generate_password_hash('123456'), nickname='干饭王',
                     role='user', account_status='active', current_points=120, total_earned_points=120,
                     total_used_points=0),
                User(account='2024211008', password_hash=generate_password_hash('123456'), nickname='高分测评家',
                     role='user', account_status='active', current_points=85, total_earned_points=85,
                     total_used_points=0),
                User(account='2024211012', password_hash=generate_password_hash('123456'), nickname='深夜夜宵党',
                     role='user', account_status='active', current_points=40, total_earned_points=40,
                     total_used_points=0),
                User(account='2024211033', password_hash=generate_password_hash('123456'), nickname='热心食客',
                     role='user', account_status='active', current_points=15, total_earned_points=15,
                     total_used_points=0)
            ]
            db.session.add_all(users)
            db.session.commit()


            for u in users:
                pr = PointRecord(user_id=u.id, amount=u.current_points, record_type='earn',
                                 source_or_dest='系统初始赠送')
                db.session.add(pr)
            db.session.commit()

            logger.info("灌入全量 16 个真实调研食堂数据...")
            canteen_dict = {}
            for c_data in CANTEENS_DATA:
                canteen = Canteen(**c_data)
                db.session.add(canteen)
                canteen_dict[canteen.id] = canteen.name
            db.session.commit()

            logger.info("路由分配通用档口及附属菜品数据...")
            for idx, stall_data in enumerate(DEFAULT_STALLS):
                target_cid = stall_data['target_canteen']
                canteen_name = canteen_dict.get(target_cid, "未知餐厅")
                stall_image = '档口01.webp' if idx % 2 == 0 else '档口02.jpg'

                stall = Stall(
                    id=f"{target_cid}-{stall_data['id']}",
                    canteen_id=target_cid,
                    name=stall_data['name'],
                    avg_price=stall_data['avg_price'],
                    best_time=stall_data['best_time'],
                    summary=stall_data['summary'],
                    image_url=stall_image
                )
                db.session.add(stall)
                db.session.commit()

                for d_idx, dish_data in enumerate(stall_data['dishes']):
                    full_desc = create_long_comment(dish_data['comment'], canteen_name, stall.name)
                    dish = Dish(
                        id=f"{stall.id}-dish-{d_idx + 1}",
                        stall_id=stall.id,
                        canteen_id=target_cid,
                        name=dish_data['name'],
                        price=dish_data['price'],
                        rating=dish_data['rating'],
                        description=full_desc,
                        value_note=stall.name,
                        tags=[stall.name],
                        image_url=DISH_IMAGE_MAPPING.get(dish_data['name'])
                    )
                    db.session.add(dish)

                    review = Review(dish_id=dish.id, user_id=users[1].id, rating=dish.rating,
                                    comment=dish_data['comment'])
                    db.session.add(review)
                db.session.commit()

            logger.info("写入精选菜品，并动态映射补全专属档口关系...")
            dynamic_stalls = {}
            for s_dish in SPECIFIC_DISHES:
                cid = s_dish['canteenId']
                stall_name = s_dish['stall']
                canteen_name = canteen_dict.get(cid, "未知餐厅")
                stall_key = f"{cid}-{stall_name}"

                if stall_key not in dynamic_stalls:
                    new_stall = Stall(
                        id=f"dyn-stall-{uuid.uuid4().hex[:6]}",
                        canteen_id=cid,
                        name=stall_name,
                        avg_price="人均 ¥15 - ¥25",
                        best_time="11:30 前",
                        summary="人气精选推荐窗口",
                        image_url='档口01.webp'
                    )
                    db.session.add(new_stall)
                    db.session.commit()
                    dynamic_stalls[stall_key] = new_stall

                target_stall = dynamic_stalls[stall_key]
                dish = Dish(
                    id=f"dish-spec-{uuid.uuid4().hex[:8]}",
                    stall_id=target_stall.id,
                    canteen_id=cid,
                    name=s_dish['name'],
                    price=s_dish['price'],
                    rating=s_dish['rating'],
                    description=create_long_comment(s_dish['comment'], canteen_name, stall_name),
                    value_note=stall_name,
                    tags=["精选", "高分"],
                    image_url=DISH_IMAGE_MAPPING.get(s_dish['name'])
                )
                db.session.add(dish)

                review = Review(dish_id=dish.id, user_id=users[2].id, rating=dish.rating, comment=s_dish['comment'])
                db.session.add(review)
            db.session.commit()

            logger.info("写入今日吐槽墙初始数据...")
            for r in RANTS_DATA:
                canteen_name = canteen_dict.get(r['canteen_id'], "未知餐厅")
                db.session.add(Rant(
                    canteen_name=canteen_name,
                    author_account=r['author'],
                    content=r['content'],
                    tag=r['tag'],
                    status=r['status'],
                    audit_reason=''
                ))

            logger.info("写入上传投稿审核工单数据...")
            for s in SUBMISSIONS_DATA:
                db.session.add(DishSubmission(
                    dish_name=s['dish_name'],
                    canteen_name=s['canteen_name'],
                    stall_name=s['stall_name'],
                    price=s['price'],
                    submitter_account=s['submitter'],
                    status=s['status'],
                    audit_reason=s.get('reason', ''),
                    description=s.get('desc', ''),
                    tags=["投稿", "新品"]
                ))

            db.session.commit()
            logger.info("终极版全量真实业务数据成功组装入库！")

        except Exception as e:
            db.session.rollback()
            logger.error(f"数据初始化失败，事务已安全回滚。错误信息: {str(e)}")
            raise e


if __name__ == '__main__':
    seed_data()