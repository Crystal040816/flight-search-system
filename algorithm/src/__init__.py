# algorithm/src/__init__.py
"""
算法模块
包含价格预测、推荐和拼接三个核心模型
"""
from .price_predictor import PricePredictor
from .recommend_engine import RecommendEngine
from .route_splicer import RouteSplicer
from .data_loader import load_itinerary_data, load_segments_data

__all__ = [
    'PricePredictor',
    'RecommendEngine',
    'RouteSplicer',
    'load_itinerary_data',
    'load_segments_data'
]