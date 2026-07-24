# algorithm/src/model_loader.py
"""
统一模型加载器
供后端 API 调用
"""
import joblib
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

# 模型路径
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


class ModelLoader:
    """统一模型加载器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self._load_models()
            self._loaded = True

    def _load_models(self):
        """加载所有模型"""
        print("加载模型...")
        try:
            self.price_model = joblib.load(os.path.join(MODEL_DIR, 'price_predict_model.pkl'))
            self.encoders = joblib.load(os.path.join(MODEL_DIR, 'encoders.pkl'))
            self.recommend = joblib.load(os.path.join(MODEL_DIR, 'recommend_model.pkl'))
            self.splice = joblib.load(os.path.join(MODEL_DIR, 'splice_model.pkl'))
            print("✅ 所有模型加载成功")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.price_model = None
            self.encoders = {}
            self.recommend = {}
            self.splice = {}

    def predict_price(self,
                      days_to_departure: int,
                      flight_month: int,
                      flight_dayofweek: int,
                      is_weekend: int,
                      segment_count: int,
                      stop_count: int,
                      seats_remaining: int,
                      distance: float,
                      duration_hours: float,
                      airline_score: float,
                      starting_airport: str,
                      destination_airport: str) -> float:
        """
        预测机票价格
        """
        if self.price_model is None:
            return None

        # 编码
        start_encoded = self._encode_airport('startingairport', starting_airport)
        dest_encoded = self._encode_airport('destinationairport', destination_airport)

        # 特征
        features = {
            'days_to_departure': days_to_departure,
            'flight_month': flight_month,
            'flight_dayofweek': flight_dayofweek,
            'is_weekend': is_weekend,
            'is_summer': 1 if flight_month in [6, 7, 8] else 0,
            'is_holiday': 1 if flight_month in [7, 8, 12] else 0,
            'segment_count': segment_count,
            'stop_count': stop_count,
            'seatsremaining': seats_remaining,
            'distance': distance,
            'duration_hours': duration_hours,
            'airline_score': airline_score,
            'price_per_stop': 0,  # 预测时动态计算
            'duration_per_stop': 0,
            'price_per_hour': 0,
            'price_per_mile': 0,
            'startingairport_encoded': start_encoded,
            'destinationairport_encoded': dest_encoded
        }

        df = pd.DataFrame([features])
        pred = self.price_model.predict(df)[0]
        return round(float(pred), 2)

    def _encode_airport(self, col: str, airport: str) -> int:
        """编码机场"""
        le = self.encoders.get(col)
        if le:
            try:
                return le.transform([airport])[0]
            except:
                return 0
        return 0

    def get_airline_score(self, airline_code: str) -> float:
        """获取航司评分"""
        airline_rank = {
            'DL': 0.9, 'AA': 0.85, 'UA': 0.85, 'B6': 0.75,
            'WN': 0.80, 'NK': 0.60, 'F9': 0.55, 'AS': 0.85
        }
        return airline_rank.get(airline_code, 0.5)

    def get_recommend_weights(self) -> Dict:
        """获取推荐权重"""
        return self.recommend.get('weights', {})

    def get_route_graph(self) -> Dict:
        """获取航线图"""
        return self.splice.get('route_graph', {})


# 单例实例
model_loader = ModelLoader()