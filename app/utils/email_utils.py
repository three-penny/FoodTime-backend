import random
import logging
from flask import current_app
from flask_mail import Message
from app.extensions import mail, get_redis

logger = logging.getLogger(__name__)

_VERIFICATION_CODE_PREFIX = 'verification_code:'


def _generate_code(length: int = 6) -> str:
    return ''.join(random.choices('0123456789', k=length))


def send_verification_code_email(email: str) -> str:
    code = _generate_code(6)
    expire = current_app.config['VERIFICATION_CODE_EXPIRE_SECONDS']
    key = f'{_VERIFICATION_CODE_PREFIX}{email}'

    r = get_redis()
    r.setex(key, expire, code)

    subject = 'FoodTime 注册验证码'
    body = f"""您好，

您的 FoodTime 注册验证码为：{code}

该验证码有效期为 {expire // 60} 分钟，请勿泄露给他人。

如果不是您本人操作，请忽略此邮件。

FoodTime 团队"""

    try:
        msg = Message(subject=subject, recipients=[email], body=body)
        mail.send(msg)
        logger.info('验证码邮件已发送至 %s', email)
    except Exception as e:
        logger.exception('验证码邮件发送失败: email=%s, error=%s', email, e)
        r.delete(key)
        raise RuntimeError('验证码发送失败，请稍后重试。')

    return code


def verify_code(email: str, code: str) -> bool:
    key = f'{_VERIFICATION_CODE_PREFIX}{email}'
    r = get_redis()
    stored = r.get(key)
    if stored is None:
        return False
    if stored != code:
        return False
    r.delete(key)
    return True
