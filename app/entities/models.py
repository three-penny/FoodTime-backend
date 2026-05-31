"""
文件名：app/entities/model.py
功能描述：数据库结构模型。
作者：郝炫斌
"""
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.extensions import db




def generate_uuid():
    """
    功能描述：生成标准的 UUID 字符串。
    返回值说明：返回 36 位的 UUID 字符串。
    """
    return str(uuid.uuid4())




class Canteen(db.Model):
    """
    类职责：定义食堂实体模型，映射食堂基本信息与特色数据。
    实体业务含义：校园内的独立食堂或餐饮大楼。
    关键字段：name, features, signature_dishes。
    关联关系：1 个食堂对应 N 个档口 (Stall)。
    创建时间：2026-05-19
    """
    __tablename__ = 'canteens'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(50))
    image_url = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)
    location = db.Column(db.String(255))
    open_hours = db.Column(db.String(100))

    avg_price = db.Column(db.String(50))
    peak_queue = db.Column(db.String(50))
    best_time = db.Column(db.String(50))
    summary = db.Column(db.Text)
    rant = db.Column(db.Text)

    features = db.Column(db.JSON)
    signature_dishes = db.Column(db.JSON)
    student_notes = db.Column(db.JSON)
    intro_blocks = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stalls = db.relationship('Stall', backref='canteen', lazy=True, cascade="all, delete-orphan")


class Stall(db.Model):
    """
    类职责：定义档口实体模型，映射档口信息及其所属食堂。
    实体业务含义：食堂内部的具体餐饮档口或商户。
    关键字段：name, canteen_id。
    关联关系：属于 1 个食堂 (Canteen)，包含 N 个菜品 (Dish)。
    创建时间：2026-05-19
    """
    __tablename__ = 'stalls'

    id = db.Column(db.String(100), primary_key=True)
    canteen_id = db.Column(db.String(50), db.ForeignKey('canteens.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255))

    avg_price = db.Column(db.String(50))
    best_time = db.Column(db.String(50))
    summary = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dishes = db.relationship('Dish', backref='stall', lazy=True, cascade="all, delete-orphan")


class Dish(db.Model):
    """
    类职责：定义菜品实体模型，映射具体餐品信息。
    实体业务含义：档口售卖的具体菜品或套餐。
    关键字段：name, price, stall_id。
    关联关系：属于 1 个档口 (Stall)，冗余 canteen_id 提升查询效率；对应 N 条评价 (Review)。
    创建时间：2026-05-19
    """
    __tablename__ = 'dishes'

    id = db.Column(db.String(100), primary_key=True)
    stall_id = db.Column(db.String(100), db.ForeignKey('stalls.id'), nullable=False)
    canteen_id = db.Column(db.String(50), db.ForeignKey('canteens.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=True)

    rating = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    value_note = db.Column(db.String(100))
    tags = db.Column(db.JSON)

    recommend_votes = db.Column(db.Integer, default=0, nullable=False)
    avoid_votes = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reviews = db.relationship('Review', backref='dish', lazy=True)




class User(db.Model):
    """
    类职责：定义用户实体模型，映射账号、权限及积分体系。
    实体业务含义：系统的核心用户。
    关键字段：account, role, account_status, current_points。
    约束：account 必须唯一且建有索引。
    创建时间：2026-05-19
    """
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    account = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')


    account_status = db.Column(db.String(20), nullable=False, default='active')
    current_points = db.Column(db.Integer, nullable=False, default=0)
    total_earned_points = db.Column(db.Integer, nullable=False, default=0)
    total_used_points = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PointRecord(db.Model):
    """
    类职责：定义积分流水记录模型，用于追踪积分获取与消耗。
    实体业务含义：用户积分的变动明细。
    关键字段：amount, record_type, source_or_dest。
    关联关系：归属于 1 个用户 (User)。
    创建时间：2026-05-19
    """
    __tablename__ = 'point_records'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)

    amount = db.Column(db.Integer, nullable=False)
    record_type = db.Column(db.String(20), nullable=False)
    source_or_dest = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Review(db.Model):
    """
    类职责：定义菜品评价实体模型。
    实体业务含义：用户对特定菜品的评分与留言。
    关键字段：rating, comment, status。
    关联关系：关联 1 个菜品 (Dish)，关联 1 个用户 (User)。
    创建时间：2026-05-19
    """
    __tablename__ = 'reviews'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    dish_id = db.Column(db.String(100), db.ForeignKey('dishes.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default='pending')
    audit_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Rant(db.Model):
    """
    类职责：定义吐槽与反馈实体模型。
    实体业务含义：用户对食堂或整体用餐体验的反馈。
    关键字段：canteen_name, content, status。
    关联关系：上传账户关联 users.account。
    创建时间：2026-05-19
    """
    __tablename__ = 'rants'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    canteen_name = db.Column(db.String(100), nullable=True)
    author_account = db.Column(db.String(50), db.ForeignKey('users.account'), nullable=False)

    content = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    audit_reason = db.Column(db.Text)

    auditor_account = db.Column(db.String(50), db.ForeignKey('users.account'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyRecommendation(db.Model):
    __tablename__ = 'daily_recommendations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    dish_id = db.Column(db.String(100), nullable=False)
    canteen_id = db.Column(db.String(50), nullable=False)
    dish_name = db.Column(db.String(100), nullable=False)
    canteen_name = db.Column(db.String(100), nullable=False)
    stall_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    rating = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(255))
    tags = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WeeklyRecommendation(db.Model):
    __tablename__ = 'weekly_recommendations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    dish_id = db.Column(db.String(100), nullable=False)
    canteen_id = db.Column(db.String(50), nullable=False)
    dish_name = db.Column(db.String(100), nullable=False)
    canteen_name = db.Column(db.String(100), nullable=False)
    stall_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    rating = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(255))
    tags = db.Column(db.JSON)
    review_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InviteCode(db.Model):
    __tablename__ = 'invite_codes'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    code = db.Column(db.String(6), nullable=False, unique=True, index=True)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    used_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by], backref='created_invite_codes')
    user = db.relationship('User', foreign_keys=[used_by], backref='used_invite_code')


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    operator_account = db.Column(db.String(50), nullable=True)
    operator_id = db.Column(db.String(36), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.String(100), nullable=True)
    detail = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50), nullable=False, default='通知')
    time = db.Column(db.String(20), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DishSubmission(db.Model):
    """
    类职责：定义菜品提报实体模型。
    实体业务含义：用户发起的 UGC 新增菜品申请。
    关键字段：dish_name, submitter_account, status。
    关联关系：提报账户关联 users.account。
    创建时间：2026-05-19
    """
    __tablename__ = 'dish_submissions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    dish_name = db.Column(db.String(100), nullable=False)
    canteen_name = db.Column(db.String(100), nullable=False)
    stall_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(255))
    description = db.Column(db.Text)
    tags = db.Column(db.JSON)

    submitter_account = db.Column(db.String(50), db.ForeignKey('users.account'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    audit_reason = db.Column(db.Text)

    auditor_account = db.Column(db.String(50), db.ForeignKey('users.account'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)