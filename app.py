"""
文件名：app.py
功能描述：后端服务的唯一主启动脚本，负责解析环境标志并执行多线程拉起。
作者：郝炫斌
创建时间：2026-05-19
"""

import os
from app import create_app
from config import DevelopmentConfig, ProductionConfig, TestingConfig


env_flag = os.environ.get('APP_ENV', 'development').lower()

if env_flag == 'production':
    active_config = ProductionConfig
elif env_flag == 'testing':
    active_config = TestingConfig
else:
    active_config = DevelopmentConfig


app = create_app(active_config)

if __name__ == '__main__':

    is_debug_mode = app.config.get('DEBUG', False)

    app.run(
        debug=is_debug_mode,
        host=os.environ.get('FLASK_RUN_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_RUN_PORT', 5000))
    )