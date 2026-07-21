# backend/app/api/__init__.py
# backend/app/api/__init__.py
from app.api.search import search_bp
from app.api.predict import predict_bp
from app.api.recommend import recommend_bp
from app.api.splice import splice_bp
from app.api.destinations import destinations_bp

__all__ = [
    'search_bp',
    'predict_bp',
    'recommend_bp',
    'splice_bp',
    'destinations_bp'
]