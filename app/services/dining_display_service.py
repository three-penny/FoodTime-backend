from app.repositories.dining_display_repository import DiningDisplayRepository
from app.repositories.review_repository import ReviewRepository


class DiningDisplayService:
    def __init__(self, dining_repo=None, review_repo=None):
        self.dining_repo = dining_repo or DiningDisplayRepository()
        self.review_repo = review_repo or ReviewRepository()

    def _canteen_to_dict(self, canteen):
        return {
            'id': canteen.id,
            'name': canteen.name,
            'shortName': canteen.short_name,
            'imageUrl': canteen.image_url,
            'rating': canteen.rating,
            'location': canteen.location,
            'openHours': canteen.open_hours,
            'avgPrice': canteen.avg_price,
            'peakQueue': canteen.peak_queue,
            'bestTime': canteen.best_time,
            'summary': canteen.summary,
            'rant': canteen.rant,
            'features': canteen.features or [],
            'signatureDishes': canteen.signature_dishes or [],
            'studentNotes': canteen.student_notes or [],
            'introBlocks': canteen.intro_blocks or [],
        }

    def _canteen_spot_to_dict(self, canteen, sort_order):
        price = 0
        if canteen.avg_price:
            import re
            match = re.search(r'¥(\d+)', canteen.avg_price)
            if match:
                price = int(match.group(1))
        features = canteen.features or []
        return {
            'id': f'{canteen.id}-spot',
            'canteenId': canteen.id,
            'name': canteen.name,
            'imageUrl': canteen.image_url,
            'rating': canteen.rating,
            'price': price,
            'valueNote': features[1] if len(features) > 1 else (features[0] if features else ''),
            'stamp': '',
            'comment': canteen.rant or '',
            'recommendVotes': None,
            'avoidVotes': None,
            'sortOrder': sort_order,
        }

    def _stall_to_dict(self, stall):
        return {
            'id': stall.id,
            'name': stall.name,
            'imageUrl': stall.image_url,
            'canteenId': stall.canteen_id,
            'avgPrice': stall.avg_price,
            'bestTime': stall.best_time,
            'summary': stall.summary,
            'dishes': [self._dish_to_dict(d) for d in (stall.dishes or [])],
        }

    def _dish_to_dict(self, dish):
        return {
            'id': dish.id,
            'name': dish.name,
            'imageUrl': dish.image_url,
            'canteenId': dish.canteen_id,
            'price': dish.price,
            'rating': dish.rating,
            'description': dish.description or '',
            'valueNote': dish.value_note or dish.name,
            'tags': dish.tags or [],
            'recommendVotes': dish.recommend_votes or 0,
            'avoidVotes': dish.avoid_votes or 0,
            'comment': dish.description or '',
            'stall': dish.value_note or '',
        }

    def _review_to_dict(self, review):
        return {
            'id': review.id,
            'dishId': review.dish_id,
            'rating': review.rating,
            'comment': review.comment,
            'reviewer': '匿名同学',
            'createdAt': review.created_at.strftime('%Y-%m-%d %H:%M') if review.created_at else '',
        }

    def get_all_canteens(self):
        canteens = self.dining_repo.get_all_canteens()
        return [self._canteen_to_dict(c) for c in canteens]

    def get_canteen_by_id(self, canteen_id):
        canteens = self.dining_repo.get_all_canteens()
        for c in canteens:
            if c.id == canteen_id:
                return self._canteen_to_dict(c)
        return None

    def get_canteen_spots(self):
        spot_ids = [
            'xueyi', 'minghu', 'dongkuai', 'xueer', 'qingzhen',
            'xuesi', 'liuyuan', 'jiaogong', 'dongqu', 'yimin',
        ]
        canteens = self.dining_repo.get_all_canteens()
        canteen_map = {c.id: c for c in canteens}
        spots = []
        for idx, cid in enumerate(spot_ids):
            c = canteen_map.get(cid)
            if c:
                spots.append(self._canteen_spot_to_dict(c, idx + 1))
        return spots

    def get_rankings(self):
        top_dishes = self.dining_repo.get_top_dishes(10)
        rankings = []
        for rank, dish in enumerate(top_dishes, 1):
            rankings.append({
                'rank': rank,
                'dishId': dish.id,
                'canteenId': dish.canteen_id,
                'dishName': dish.name,
                'score': dish.rating,
                'stamp': '必吃' if dish.rating >= 4.8 else '推荐',
                'recommendVotes': dish.recommend_votes or 0,
                'avoidVotes': dish.avoid_votes or 0,
            })
        return rankings

    def get_stalls_by_canteen(self, canteen_id):
        stalls = self.dining_repo.get_stalls_by_canteen_id(canteen_id)
        return [self._stall_to_dict(s) for s in stalls]

    def get_dishes_by_canteen(self, canteen_id):
        stalls = self.dining_repo.get_stalls_by_canteen_id(canteen_id)
        dishes = []
        for stall in stalls:
            stall_dishes = self.dining_repo.get_dishes_by_stall_id(stall.id)
            for d in stall_dishes:
                dish_dict = self._dish_to_dict(d)
                dish_dict['stall'] = stall.name
                dish_dict['canteenName'] = None
                dishes.append(dish_dict)
        return dishes

    def get_dish_by_id(self, dish_id):
        from app.entities.models import Dish as DishModel
        from app.extensions import db
        dish = db.session.query(DishModel).filter(DishModel.id == dish_id).first()
        if not dish:
            return None
        return self._dish_to_dict(dish)

    def get_top_dishes(self, limit=10):
        dishes = self.dining_repo.get_top_dishes(limit)
        return [self._dish_to_dict(d) for d in dishes]

    def get_reviews_by_dish(self, dish_id):
        from app.entities.models import Review as ReviewModel
        from app.extensions import db
        reviews = db.session.query(ReviewModel).filter(
            ReviewModel.dish_id == dish_id
        ).order_by(ReviewModel.created_at.desc()).all()
        return [self._review_to_dict(r) for r in reviews]

    def recommend_dish(self, dish_id):
        return self.dining_repo.increment_dish_recommend_votes(dish_id)

    def avoid_dish(self, dish_id):
        return self.dining_repo.increment_dish_avoid_votes(dish_id)
