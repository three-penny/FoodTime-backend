import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest
from config import TestingConfig
from app.extensions import db as _db
from app.entities.models import (
    User, Canteen, Stall, Dish, Review, Rant,
    PointRecord, InviteCode, AuditLog, VerificationCode,
    DailyRecommendation, WeeklyRecommendation,
)


@pytest.fixture(scope='function')
def app():
    with patch('app.__init__._setup_scheduler'):
        with patch('app.__init__.init_redis'):
            from app import create_app
            application = create_app(TestingConfig)

    with application.app_context():
        _db.create_all()

    yield application

    with application.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture(scope='function')
def session(db):
    return db.session


@pytest.fixture(autouse=True)
def mock_redis():
    from app.extensions import get_redis
    codes = {}

    def mock_setex(key, expire, code):
        codes[key] = code

    def mock_get(key):
        return codes.get(key)

    def mock_delete(key):
        codes.pop(key, None)
        return 1

    mock = MagicMock()
    mock.setex.side_effect = mock_setex
    mock.get.side_effect = mock_get
    mock.delete.side_effect = mock_delete

    with patch('app.extensions.get_redis', return_value=mock), \
         patch('app.utils.email_utils.get_redis', return_value=mock):
        yield mock


def _make_token(app, user_id: str, account: str, role: str = 'user') -> str:
    from app.utils.auth_utils import generate_token
    with app.app_context():
        return generate_token(user_id=user_id, account=account, role=role)


@pytest.fixture
def user_headers(app, client):
    with app.app_context():
        existing = User.query.filter_by(account='testuser').first()
        if not existing:
            user = User(
                id=str(uuid.uuid4()),
                account='testuser',
                email='testuser@test.com',
                password_hash='pbkdf2:sha256:600000$dummy',
                nickname='测试用户',
                role='user',
                account_status='active',
            )
            _db.session.add(user)
            _db.session.commit()
        else:
            user = existing
        token = _make_token(app, user.id, user.account, 'user')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def admin_headers(app, client):
    with app.app_context():
        existing = User.query.filter_by(account='admin').first()
        if not existing:
            admin = User(
                id=str(uuid.uuid4()),
                account='admin',
                email='admin@test.com',
                password_hash='pbkdf2:sha256:600000$dummy',
                nickname='管理员',
                role='admin',
                account_status='active',
            )
            _db.session.add(admin)
            _db.session.commit()
        else:
            admin = existing
        token = _make_token(app, admin.id, admin.account, 'admin')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def superadmin_headers(app, client):
    with app.app_context():
        existing = User.query.filter_by(account='superadmin').first()
        if not existing:
            sa = User(
                id=str(uuid.uuid4()),
                account='superadmin',
                email='superadmin@test.com',
                password_hash='pbkdf2:sha256:600000$dummy',
                nickname='超级管理员',
                role='superadmin',
                account_status='active',
            )
            _db.session.add(sa)
            _db.session.commit()
        else:
            sa = existing
        token = _make_token(app, sa.id, sa.account, 'superadmin')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def seeded_canteen(app, db):
    canteen = Canteen(
        id='test_canteen',
        name='测试食堂',
        short_name='测试',
        image_url='/img/canteen.jpg',
        rating=4.5,
        location='测试位置',
        open_hours='11:00-13:00',
        avg_price='¥15',
        features=['好吃', '便宜'],
        signature_dishes=['招牌菜'],
        summary='测试食堂描述',
    )
    db.session.add(canteen)

    stall = Stall(
        id='test_canteen-测试档口',
        canteen_id='test_canteen',
        name='测试档口',
        avg_price='¥12',
        summary='测试档口描述',
    )
    db.session.add(stall)
    db.session.commit()
    db.session.refresh(canteen)
    db.session.refresh(stall)
    return canteen


@pytest.fixture
def seeded_dish(app, db, seeded_canteen):
    dish = Dish(
        id='test_canteen-测试菜品',
        stall_id='test_canteen-测试档口',
        canteen_id='test_canteen',
        name='测试菜品',
        image_url='/img/dish.jpg',
        price=12.5,
        rating=4.5,
        description='好吃的测试菜品',
        value_note='推荐',
        tags=['辣', '推荐'],
        recommend_votes=10,
        avoid_votes=1,
    )
    db.session.add(dish)
    db.session.commit()
    db.session.refresh(dish)
    return dish


@pytest.fixture
def seeded_review(app, db, seeded_dish, user_headers):
    with app.app_context():
        user = User.query.filter_by(account='testuser').first()
        review = Review(
            id=str(uuid.uuid4()),
            dish_id=seeded_dish.id,
            user_id=user.id,
            rating=4.5,
            comment='很好吃！',
            status='approved',
        )
        db.session.add(review)
        db.session.commit()
        db.session.refresh(review)
    return review
