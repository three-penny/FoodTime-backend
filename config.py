"""
文件名：config.py
功能描述：系统全局配置文件，通过环境变量动态加载多套运行环境配置。
作者：郝炫斌
创建时间：2026-05-19
"""

import os
import json
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    类职责：基础配置母类，定义各环境共享的默认配置项与基础设施参数。
    使用场景：不允许直接实例化，作为子类基类。
    设计说明：安全密钥等高危信息默认具备兜底策略，生产环境强制重写。
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'foodtime-super-secret-key'


    CANTEEN_IMG_FOLDER = os.path.join(BASE_DIR, 'data', 'canteen_img')
    STALL_IMG_FOLDER = os.path.join(BASE_DIR, 'data', 'stall_img')
    DISH_IMG_FOLDER = os.path.join(BASE_DIR, 'data', 'dish_img')
    SUBMISSION_IMG_FOLDER = os.path.join(BASE_DIR, 'data', 'submission_img')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SQLALCHEMY_ENGINE_OPTIONS = {
        "json_serializer": lambda obj: json.dumps(obj, ensure_ascii=False)
    }


class DevelopmentConfig(Config):
    """
    类职责：本地开发环境专属配置。
    运行特征：开启 Debug 模式，使用本地轻量级 app_dev.db 数据库。
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(BASE_DIR, 'app_dev.db')


class TestingConfig(Config):
    """
    类职责：自动化集成测试环境专属配置。
    运行特征：强制启用 TESTING 标记，使用独立内存数据库以确保测试隔离性与运行速度。
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """
    类职责：线上生产环境专属配置。
    运行特征：严禁开启 Debug 模式，数据源连接字符串及所有敏感密钥必须由环境变量强管控注入。
    """
    DEBUG = False
    TESTING = False


    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    @classmethod
    def init_app(cls, app):
        """
        功能描述：生产环境专属的初始化校验钩子，用于确保关键环境变量未缺失。
        """
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("生产环境启动失败：未检测到有效系统的 DATABASE_URL 环境变量。")