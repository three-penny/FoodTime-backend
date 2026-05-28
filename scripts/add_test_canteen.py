"""一次性脚本：向数据库添加一条测试食堂记录。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.entities.models import Canteen

app = create_app()
with app.app_context():
    existing = Canteen.query.filter_by(name='测试食堂').first()
    if existing:
        print(f"测试食堂已存在 (id={existing.id})，跳过。")
    else:
        canteen = Canteen(
            id='ceshi',
            name='测试食堂',
            short_name='测试',
            rating=4.5,
            location='测试校区',
            open_hours='08:00 - 20:00',
            avg_price='人均 ¥10 - ¥20',
            peak_queue='12:00 - 13:00',
            best_time='11:00 前',
            summary='这是一个用于测试的食堂。',
            rant='测试食堂，暂无吐槽。',
            features=['测试', '示例'],
            signature_dishes=['测试菜品A', '测试菜品B'],
            student_notes=['仅供开发测试使用'],
            intro_blocks=[
                {'title': '测试说明', 'content': '这是通过脚本自动创建的测试食堂数据。'}
            ],
        )
        db.session.add(canteen)
        db.session.commit()
        print(f"测试食堂添加成功 (id={canteen.id})")
