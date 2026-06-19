"""
文件名：app/extensions.py
功能描述：集中初始化并管理所有 Flask 扩展插件，防止组件间循环引用。
作者：郝炫斌
"""
from datetime import timezone, timedelta
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from redis import Redis

tz_cst = timezone(timedelta(hours=8))


naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

migrate = Migrate()

mail = Mail()

_redis_client: Redis | None = None


def get_redis() -> Redis:
    if _redis_client is None:
        raise RuntimeError('Redis 未初始化，请检查 REDIS_URL 配置。')
    return _redis_client


def init_redis(app):
    global _redis_client
    _redis_client = Redis.from_url(app.config['REDIS_URL'], decode_responses=True)