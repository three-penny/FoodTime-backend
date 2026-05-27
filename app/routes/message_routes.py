from flask import Blueprint, jsonify, g
from app.services.message_service import MessageService

message_bp = Blueprint('messages', __name__, url_prefix='/api/v1')
message_service = MessageService()


@message_bp.get('/messages')
def list_messages():
    data = message_service.get_all_messages()
    return jsonify({'code': 0, 'message': 'success', 'data': data, 'trace_id': g.trace_id}), 200
