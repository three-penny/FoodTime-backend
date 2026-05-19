# FoodTime 后端数据库与 Repository 层开发交接文档

作者：郝炫斌  
创建时间：2026-05-19  
适用项目：`FoodTime-backend`

## 1. 文档目的
本文档用于记录后端数据库模型设计与 Repository 数据访问层的实现范围、实体关系、关键文件、数据来源、操作封装、测试方式和后续交接注意事项，方便后续同学继续维护系统架构、补全 Service 层与接口逻辑。

## 2. 项目背景
FoodTime 是一个 B/S 架构的校园食堂点评与 UGC 系统。后端接口与数据库主要提供食堂与菜品展示、用户评价、UGC 内容（吐槽、新建菜品提报）等核心能力。

当前后端项目采用：
+ Python 3
+ Flask
+ Flask-SQLAlchemy (ORM)
+ Flask-Migrate (Alembic)
+ SQLite (开发 / 测试环境)
+ 仓储模式 (Repository Pattern)

常用运行与校验命令：

```bash
# 安装依赖
pip install -r requirements.txt

# 开发环境启动
python app.py

# 数据库清除与重建
Remove-Item -Recurse -Force migrations
Remove-Item -Force app_dev.db
flask db init
flask db migrate -m "init_foodtime_tables"
flask db upgrade

# 灌输初始数据
python seed.py
```

## 3. 任务范围
后端数据库与 Repository 层任务负责以下模块的设计与底层实现：
+ 餐饮核心数据域：食堂(Canteens)、档口(Stalls)、菜品(Dishes)
+ 用户与 UGC 域：用户体系、积分记录、菜品评价(Reviews)、食堂吐槽(Rants)、新菜品提报(DishSubmissions)
+ 基础查询仓库(Repositories)：为上层服务封装各域内实体创建、查询、更新、分页等方法。

当前实现重点是打通基础数据通道，确保后续功能能够顺利地基于聚合根模型在底层拉取或写入数据。

## 4. 目录与关键文件
### 实体文件 (Model)
```bash
app/entities/models.py
```

### 仓库文件 (Repository)
```bash
app/repositories/dining_display_repository.py
app/repositories/dish_submission_repository.py
app/repositories/rant_repository.py
app/repositories/review_repository.py
```
### 数据初始化
```bash
app/script/seed.py
```

## 5. 数据库结构说明
数据库模型统一在 `app/entities/models.py` 中通过 SQLAlchemy 进行声明。所有具有主键 `id` 的 UGC 和用户实体采用 `uuid4` 字符串，食堂、档口、菜品采用短字符串 UUID 或设定标识。

### 5.1 Canteen（食堂）
```bash
id              String(50)      PK
name            String(100)     食堂全称
short_name      String(50)      简称
image_url       String(255)     食堂封面图
rating          Float           评分
location        String(255)     位置描述
open_hours      String(100)     营业时间

avg_price       String(50)      人均消费区间
peak_queue      String(50)      排队高峰提示
best_time       String(50)      推荐就餐时段
summary         Text            食堂简介
rant            Text            食堂级精选吐槽（运营人工维护）

features        JSON            特色标签数组
signature_dishes JSON           招牌菜数组
student_notes   JSON            学生短评数组
intro_blocks    JSON            前端区块化介绍配置

created_at      DateTime        创建时间
updated_at      DateTime        更新时间
```

关系：stalls -> Stall[] (backref='canteen', cascade="all, delete-orphan")

### 5.2 Stall（档口）
```bash
id              String(100)     PK
canteen_id      String(50)      FK -> canteens.id
name            String(100)     档口名称
image_url       String(255)     档口图片

avg_price       String(50)      人均消费
best_time       String(50)      推荐时段
summary         Text            档口简介

created_at      DateTime
updated_at      DateTime
```

关系：dishes -> Dish[] (backref='stall', cascade="all, delete-orphan")

### 5.3 Dish（菜品）
```bash
id              String(100)     PK
stall_id        String(100)     FK -> stalls.id
canteen_id      String(50)      FK -> canteens.id (冗余，提升查询效率)

name            String(100)     菜品名称
image_url       String(255)     菜品图片
price           Float           价格（允许为空）

rating          Float           评分（需由上层 Service 维护更新）
description     Text            菜品描述
value_note      String(100)     性价比备注
tags            JSON            标签数组

recommend_votes Integer         推荐人数（默认 0）
avoid_votes     Integer         避雷人数（默认 0）

created_at      DateTime
updated_at      DateTime
```

关系：reviews -> Review[] (backref='dish')

### 5.4 User（用户）
```bash
id              String(36)      PK, UUID
account         String(50)      登录账号（唯一索引）
password_hash   String(255)     密码哈希
nickname        String(50)      展示昵称
role            String(20)      角色（默认 'user'）

account_status  String(20)      账号状态（默认 'active'）
current_points  Integer         当前可用积分
total_earned_points Integer     累计获得积分
total_used_points Integer       累计消耗积分

created_at      DateTime
updated_at      DateTime
```

### 5.5 PointRecord（积分流水）
```bash
id              String(36)      PK, UUID
user_id         String(36)      FK -> users.id (索引)

amount          Integer         变动金额（正数为获得，负数为消耗）
record_type     String(20)      类型（建议枚举：'earn' / 'use'）
source_or_dest  String(255)     来源或去向说明

created_at      DateTime
updated_at      DateTime
```

### 5.6 Review（菜品评价）
```bash
id              String(36)      PK, UUID
dish_id         String(100)     FK -> dishes.id
user_id         String(36)      FK -> users.id
rating          Float           星级评分（必填）
comment         Text            评论内容（必填）

created_at      DateTime
updated_at      DateTime
```

### 5.7 Rant（吐槽墙）
```bash
id              String(36)      PK, UUID
canteen_name    String(100)     吐槽关联食堂（允许为空）
author_account  String(50)      FK -> users.account

content         Text            吐槽内容（必填）
tag             String(50)      分类标签（如：'排队'、'口味'、'服务'）
status          String(20)      审核状态（默认 'pending'）
audit_reason    Text            审核意见

auditor_account String(50)      FK -> users.account（允许为空）

created_at      DateTime
updated_at      DateTime
```

### 5.8 DishSubmission（菜品提报）
```bash
id              String(36)      PK, UUID
dish_name       String(100)     菜品名称（必填）
canteen_name    String(100)     食堂名称（必填）
stall_name      String(100)     档口名称（必填）
price           Float           价格（允许为空）
image_url       String(255)     图片地址
description     Text            描述
tags            JSON            标签数组

submitter_account String(50)    FK -> users.account
status          String(20)      审核状态（默认 'pending'）
audit_reason    Text            审核意见

auditor_account String(50)      FK -> users.account（允许为空）

created_at      DateTime
updated_at      DateTime
```

## 6. Repository 层设计
本项目使用 Repository 层将数据操作细节局限在其内部：
1. **DiningDisplayRepository**：封装餐饮展现系统相关的展示业务查询操作，如获取高分餐品，指定档口下菜品等。
```bash
get_all_canteens: 查询所有食堂的全部信息。
get_stalls_by_canteen_id: 根据食堂 ID 查询下属所有档口的全部信息。
get_dishes_by_stall_id: 根据档口 ID 查询下属所有餐品的全部信息。
get_top_dishes: 查询评分排名前 N 的餐品全部信息。
increment_dish_recommend_votes: 将指定菜品的推荐人数加 1。
increment_dish_avoid_votes: 将指定菜品的避雷人数加 1。
```
2. **ReviewRepository**：封装用户反馈评价内容的拉取与创建操作。
```bash
create_review: 在 reviews 表中插入一条新的用户菜品评价记录。
```
3. **RantRepository** 与 **DishSubmissionRepository**：UGC 提报模型的相关操作，涉及状态的读取（用于管理员审核读取）、操作插入。
**RantRepository**:
```bash
create_rant: 在 rants 表中插入一条新的用户吐槽反馈记录。
get_rants_by_status: 根据输入的状态，查询 rants 表中对应的全部完整行数据。
update_rant_audit_result: 根据吐槽记录的唯一 id，填充其审核状态、审核意见及负责审批的管理员账号。
```
**DishSubmissionRepository**:
```bash
create_submission: 在 dish_submissions 表中插入一条新的菜品提报记录。
get_submissions_by_status: 根据输入的状态，查询 dish_submissions 表中对应的全部完整行数据。
update_audit_result: 根据提报工单的唯一 id，填充其审核状态、审核意见及负责审批的管理员账号。
```

## 7. 数据流说明
后续开发应当坚持以下数据流通方向，不再允许在 Web 服务层（`app/routes/`）里直接进行 `db.session.query`，必须由 `services` 层通过调用各 `repositories` 的获取数据来组装返回结构。

## 8. 交接检查清单
+ 能通过 `python seed.py` 成功重置且通过 `models` 定义生成数据。
+ `models.py` 中所有的关联在 SQLAlchemy 中能够被访问（使用 `backref` 或 `relationship`）。
+ Repository 的每个类有明确的归口划分。


