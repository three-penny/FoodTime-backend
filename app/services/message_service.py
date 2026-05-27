from app.entities.models import Message
from app.extensions import db


class MessageService:
    def get_all_messages(self):
        messages = db.session.query(Message).order_by(Message.created_at.desc()).all()
        return [
            {
                'id': m.id,
                'title': m.title,
                'content': m.content,
                'tag': m.tag,
                'time': m.time,
            }
            for m in messages
        ]
