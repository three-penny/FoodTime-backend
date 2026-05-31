"""
文件名：app/__init__.py
功能描述：应用工厂核心文件，负责 Flask 实例的组装、生命周期钩子编排及中间件横切控制。
作者：郝炫斌
创建时间：2026-05-19
"""

import os
import uuid
import logging
from flask import Flask, g, request, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException
from sqlalchemy import inspect as sa_inspect
from werkzeug.security import generate_password_hash
from config import DevelopmentConfig
from app.extensions import db, migrate

logger = logging.getLogger(__name__)


def _init_database(app):
    """
    功能描述：数据库自动初始化守卫。在应用首次启动时检测表结构是否存在，
             若不存在则自动建表并插入默认管理员账号，确保核心功能开箱即用。
    参数说明：
        app: Flask 应用实例（需已完成配置加载与 db.init_app）。
    """
    with app.app_context():
        inspector = sa_inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            logger.info('[DB Init] 数据库表不存在，正在自动创建...')
            db.create_all()
            logger.info('[DB Init] 所有表已创建完毕。')

            from app.entities.models import User
            admin_exists = User.query.filter_by(account='admin').first()
            if not admin_exists:
                logger.info('[DB Init] 正在创建默认管理员账号 (admin / 123456)...')
                admin_user = User(
                    account='admin',
                    email='admin@foodtime.local',
                    password_hash=generate_password_hash('123456'),
                    nickname='审核管理员',
                    role='admin',
                    account_status='active',
                    current_points=999,
                    total_earned_points=999,
                    total_used_points=0,
                )
                db.session.add(admin_user)
                db.session.commit()
                logger.info('[DB Init] 默认管理员账号创建成功。')
            superadmin_exists = User.query.filter_by(account='superadmin').first()
            if not superadmin_exists:
                logger.info('[DB Init] 正在创建默认超级管理员账号 (superadmin / 123456)...')
                superadmin_user = User(
                    account='superadmin',
                    email='superadmin@foodtime.local',
                    password_hash=generate_password_hash('123456'),
                    nickname='超级管理员',
                    role='superadmin',
                    account_status='active',
                    current_points=9999,
                    total_earned_points=9999,
                    total_used_points=0,
                )
                db.session.add(superadmin_user)
                db.session.commit()
                logger.info('[DB Init] 默认超级管理员账号创建成功。')
            elif superadmin_exists.nickname == '超级管理员':
                from werkzeug.security import check_password_hash
                if not check_password_hash(superadmin_exists.password_hash, '123456'):
                    logger.info('[DB Init] 检测到默认超管密码非 123456，正在重置...')
                    superadmin_exists.password_hash = generate_password_hash('123456')
                    db.session.commit()
                    logger.info('[DB Init] 默认超管密码已重置为 123456。')
        else:
            logger.info('[DB Init] 数据库表已存在，跳过初始化。')
            if 'invite_codes' not in existing_tables:
                logger.info('[DB Init] 检测到 invite_codes 表缺失，正在创建...')
                from app.entities.models import InviteCode
                db.create_all()
                logger.info('[DB Init] invite_codes 表已创建。')
            if 'audit_logs' not in existing_tables:
                logger.info('[DB Init] 检测到 audit_logs 表缺失，正在创建...')
                from app.entities.models import AuditLog
                db.create_all()
                logger.info('[DB Init] audit_logs 表已创建。')

            from app.entities.models import User
            admin_user = User.query.filter_by(account='admin').first()
            if admin_user and not admin_user.email:
                logger.info('[DB Init] 检测到默认管理员缺少 email，正在补全...')
                admin_user.email = 'admin@foodtime.local'
                db.session.commit()
                logger.info('[DB Init] 默认管理员 email 已补全。')

            superadmin_exists = User.query.filter_by(account='superadmin').first()
            if not superadmin_exists:
                logger.info('[DB Init] 正在创建默认超级管理员账号 (superadmin / 123456)...')
                superadmin_user = User(
                    account='superadmin',
                    email='superadmin@foodtime.local',
                    password_hash=generate_password_hash('123456'),
                    nickname='超级管理员',
                    role='superadmin',
                    account_status='active',
                    current_points=9999,
                    total_earned_points=9999,
                    total_used_points=0,
                )
                db.session.add(superadmin_user)
                db.session.commit()
                logger.info('[DB Init] 默认超级管理员账号创建成功。')


def create_app(config_class=DevelopmentConfig) -> Flask:
    """
    功能描述：Flask 应用工厂函数，动态装配扩展插件、路由蓝图并植入全局守卫。
    参数说明：
        config_class: 传入对应的配置类，默认为本地开发环境配置 (DevelopmentConfig)。
    返回值说明：
        返回配置完整、状态健全的 Flask 核心应用实例。
    使用示例：
        app = create_app(ProductionConfig)
    """
    app = Flask(__name__)
    app.config.from_object(config_class)


    db.init_app(app)
    migrate.init_app(app, db)

    from app.entities import models

    _init_database(app)

    @app.route('/api/v1/images/canteen/<path:filename>')
    def serve_canteen_image(filename):
        return send_from_directory(app.config['CANTEEN_IMG_FOLDER'], filename)

    @app.route('/api/v1/images/stall/<path:filename>')
    def serve_stall_image(filename):
        return send_from_directory(app.config['STALL_IMG_FOLDER'], filename)

    @app.route('/api/v1/images/dish/<path:filename>')
    def serve_dish_image(filename):
        return send_from_directory(app.config['DISH_IMG_FOLDER'], filename)

    @app.route('/api/v1/images/submission/<path:filename>')
    def serve_submission_image(filename):
        return send_from_directory(app.config['SUBMISSION_IMG_FOLDER'], filename)

    from app.routes.auth_routes import auth_bp
    from app.routes.dish_submission_routes import submission_bp
    from app.routes.review_routes import review_bp
    from app.routes.dining_routes import dining_bp
    from app.routes.rant_routes import rant_bp
    from app.routes.points_routes import points_bp
    from app.routes.message_routes import message_bp
    from app.routes.superadmin_routes import superadmin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(dining_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(rant_bp)
    app.register_blueprint(points_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(superadmin_bp)

    _setup_scheduler(app)


    @app.before_request
    def ensure_trace_id():
        """
        功能描述：前置请求拦截器。对每一个入栈请求生成或透传 trace_id，确保全链路可观测。
        对齐规范：rules.md 第 6.1 节日志监控指标。
        """

        trace_id = request.headers.get('X-Trace-Id') or str(uuid.uuid4().hex)[:16]
        g.trace_id = trace_id

    @app.errorhandler(Exception)
    def handle_global_exception(error):
        """
        功能描述：未捕获异常全局拦截器。阻断敏感堆栈外泄，将故障统一包装为标准响应体。
        参数说明：
            error: 触发的原始 Python 异常对象。
        对齐规范：rules.md 第 4.2 节全局异常拦截与标准错误码。
        """
        # HTTP 异常（404 等）交由 Flask 内置处理，避免图片服务等端点返回 500 JSON
        if isinstance(error, HTTPException):
            return error

        trace_id = getattr(g, 'trace_id', '6f6f6474696d65')
        app.logger.exception('未捕获异常 (trace_id=%s): %s', trace_id, error)

        response_body = {
            'code': 'SYSTEM_500_001',
            'message': '服务器内部未知错误，请联系系统管理员或携带追踪码重试。',
            'trace_id': trace_id
        }
        return jsonify(response_body), 500



    @app.route('/ping', methods=['GET'])
    def ping():
        """
        接口说明：服务可用性健康检查（对齐 rules.md 3.2 统一数据响应骨架）。
        权限要求：无，属于公开暴露端点。
        """
        trace_id = getattr(g, 'trace_id', '6f6f6474696d65')
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'status': 'healthy',
                'message': 'FoodTime API is running successfully!'
            },
            'trace_id': trace_id
        }), 200

    return app


def _setup_scheduler(app):
    """配置 APScheduler 定时任务（每日/每周推荐刷新）。"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from app.services.recommendation_service import refresh_daily_recommendations, refresh_weekly_recommendations

        scheduler = BackgroundScheduler()

        def daily_wrapper():
            with app.app_context():
                refresh_daily_recommendations()

        def weekly_wrapper():
            with app.app_context():
                refresh_weekly_recommendations()

        scheduler.add_job(daily_wrapper, CronTrigger(hour=0, minute=0, timezone='Asia/Shanghai'), id='daily_rec')
        scheduler.add_job(weekly_wrapper, CronTrigger(day_of_week='sun', hour=0, minute=0, timezone='Asia/Shanghai'), id='weekly_rec')

        scheduler.start()
        app.logger.info('[Scheduler] 定时任务已启动')
    except Exception as e:
        app.logger.warning('[Scheduler] 定时任务启动失败: %s', e)