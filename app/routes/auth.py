from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash

from app.entities.models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _response(code, message, data=None, status_code=200):
    body = {
        "code": code,
        "message": message,
        "data": data,
        "trace_id": getattr(g, "trace_id", "6f6f6474696d65"),
    }
    return jsonify(body), status_code


def _serialize_user(user):
    return {
        "id": user.id,
        "account": user.account,
        "email": "",
        "nickname": user.nickname,
        "role": user.role,
    }


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    login_id = (payload.get("login_id") or payload.get("account") or "").strip()
    password = payload.get("password") or ""

    if not login_id or not password:
        return _response("AUTH_400_001", "Please enter account and password.", status_code=400)

    user = User.query.filter_by(account=login_id).first()
    if not user or not check_password_hash(user.password_hash, password):
        return _response("AUTH_401_001", "Invalid account or password.", status_code=401)

    if user.account_status != "active":
        return _response("AUTH_403_001", "Account is disabled.", status_code=403)

    return _response(0, "success", _serialize_user(user))
