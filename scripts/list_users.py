from app import create_app
from app.entities.models import Canteen
from config import DevelopmentConfig
app = create_app(DevelopmentConfig)
with app.app_context():
    for c in Canteen.query.order_by(Canteen.id).all():
        print(f"{c.id:25s} | {c.name}")
