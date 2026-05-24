"""
文件名：app/__init__.py
功能描述：应用工厂核心文件，负责 Flask 实例的组装、生命周期钩子编排及中间件横切控制。
作者：郝炫斌
创建时间：2026-05-19
"""

import uuid
from flask import Flask, g, request, jsonify
from config import DevelopmentConfig
from app.extensions import db, migrate


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

    from app.routes.auth_routes import auth_bp
    from app.routes.dish_submission_routes import submission_bp
    from app.routes.dining_routes import dining_bp
    from app.routes.review_routes import review_bp
    from app.routes.rant_routes import rant_bp
    from app.routes.points_routes import points_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(dining_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(rant_bp)
    app.register_blueprint(points_bp)


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

        trace_id = getattr(g, 'trace_id', '6f6f6474696d65')

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