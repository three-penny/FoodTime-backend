"""
文件名：app/utils/email_utils.py
功能描述：邮件发送工具，提供验证码邮件发送与内存级验证码存储校验能力。
作者：FoodTime Backend Team
创建时间：2026-06-01
"""

import random
import time
import logging
from threading import Lock
from flask import current_app
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)

_code_store: dict[str, dict] = {}
_code_store_lock = Lock()
_CLEANUP_INTERVAL = 300
_last_cleanup = time.time()


def _generate_code(length: int = 6) -> str:
    """生成指定位数的纯数字验证码。"""
    return ''.join(random.choices('0123456789', k=length))


def _cleanup_expired():
    """清理过期验证码，避免内存泄漏。"""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return
    with _code_store_lock:
        expired_keys = [k for k, v in _code_store.items() if v['expires_at'] <= now]
        for k in expired_keys:
            del _code_store[k]
        _last_cleanup = now


def send_verification_code_email(email: str) -> str:
    """
    生成6位数字验证码并发送到指定邮箱。
    参数说明：
        email: 目标邮箱地址。
    返回值说明：
        返回生成的验证码字符串。
    异常抛出：
        RuntimeError: 邮件发送失败。
    """
    code = _generate_code(6)
    expires_at = time.time() + current_app.config['VERIFICATION_CODE_EXPIRE_SECONDS']

    with _code_store_lock:
        _code_store[email] = {
            'code': code,
            'expires_at': expires_at,
        }

    subject = 'FoodTime 注册验证码'
    body = f"""您好，

您的 FoodTime 注册验证码为：{code}

该验证码有效期为 {current_app.config['VERIFICATION_CODE_EXPIRE_SECONDS'] // 60} 分钟，请勿泄露给他人。

如果不是您本人操作，请忽略此邮件。

FoodTime 团队"""

    try:
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body,
        )
        mail.send(msg)
        logger.info('验证码邮件已发送至 %s', email)
    except Exception as e:
        logger.exception('验证码邮件发送失败: email=%s, error=%s', email, e)
        raise RuntimeError('验证码发送失败，请稍后重试。')

    _cleanup_expired()
    return code


def verify_code(email: str, code: str) -> bool:
    """
    校验邮箱验证码是否正确且未过期。
    参数说明：
        email: 邮箱地址。
        code: 用户输入的验证码。
    返回值说明：
        校验通过返回 True，否则返回 False。
    """
    with _code_store_lock:
        record = _code_store.get(email)
        if not record:
            return False
        if time.time() > record['expires_at']:
            del _code_store[email]
            return False
        if record['code'] != code:
            return False
        del _code_store[email]
        return True
