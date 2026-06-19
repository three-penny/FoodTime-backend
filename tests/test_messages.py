import pytest
from app.extensions import db
from app.entities.models import Message


class TestMessages:
    def test_list_messages(self, client):
        resp = client.get('/api/v1/messages')
        data = resp.get_json()
        assert resp.status_code == 200
        assert isinstance(data['data'], list)

    def test_messages_structure(self, client, app):
        with app.app_context():
            msg = Message(
                id='test_msg_1',
                title='测试通知',
                content='这是一条测试通知',
                tag='通知',
                time='2026-06-19',
            )
            db.session.add(msg)
            db.session.commit()
        resp = client.get('/api/v1/messages')
        data = resp.get_json()
        assert resp.status_code == 200
        assert any(m['title'] == '测试通知' for m in data['data'])
