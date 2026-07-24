# backend/app/services/predict_service.py
import os
import json
import joblib
import pymysql  # 导入 pymysql 自行直连数据库，不依赖并修改任何 search 代码！
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.config import Config

try:
    from backend.app import redis_client
except ImportError:
    try:
        from app import redis_client
    except ImportError:
        redis_client = None


class PricePredictService:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "price_predict_model.pkl")
        self.encoder_path = os.path.join(base_dir, "algorithm", "models", "encoders.pkl")

        self.model = None
        self.encoders = None

        # 读取物理 MySQL 配置，实现独立自连
        self.db_host = Config.MYSQL_HOST
        self.db_port = Config.MYSQL_PORT
        self.db_name = Config.MYSQL_DB
        self.db_user = Config.MYSQL_USER
        self.db_pass = Config.MYSQL_PASSWORD

        self.airline_rank = {
            'DL': 0.9, 'AA': 0.85, 'UA': 0.85, 'B6': 0.75,
            'WN': 0.80, 'NK': 0.60, 'F9': 0.55, 'AS': 0.85
        }

        self.features = [
            'days_to_departure', 'flight_month', 'flight_dayofweek', 'is_weekend',
            'is_summer', 'is_holiday', 'segment_count', 'stop_count',
            'seatsremaining', 'distance', 'duration_hours', 'airline_score',
            'price_per_stop', 'duration_per_stop', 'price_per_hour', 'price_per_mile',
            'startingairport_encoded', 'destinationairport_encoded'
        ]

        # 加载模型
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"[Predict Service] 成功加载价格预测模型: {self.model_path}")
            except Exception as e:
                print(f"[Predict Service] 模型加载失败: {str(e)}")

        # 加载编码器
        if os.path.exists(self.encoder_path):
            try:
                self.encoders = joblib.load(self.encoder_path)
                print(f"[Predict Service] 成功加载编码器: {self.encoder_path}")
            except Exception as e:
                print(f"[Predict Service] 编码器加载失败: {str(e)}")

    def _get_route_avg_price_from_db(self, origin: str, destination: str):
        """独立自连：从 MySQL 提取平均报价作为模型基准，不调用任何外部 search 代码"""
        try:
            conn = self._get_db_connection()
            sql = "SELECT AVG(lowest_price) as avg_p FROM ads_route_cabin_lowest_price WHERE origin_city = %s AND destination_city = %s"
            with conn.cursor() as cursor:
                cursor.execute(sql, [origin.upper(), destination.upper()])
                res = cursor.fetchone()
            conn.close()
            return float(res["avg_p"]) if res and res["avg_p"] else 200.0
        except Exception as e:
            print(f"[SQL Debug] 价格预测独立连接数据库失败，启用保底价格 200.0: {str(e)}")
            return 200.0

    def _get_db_connection(self):
        return pymysql.connect(
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_pass,
            database=self.db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def _predict_single(self, features_dict):
        if self.model is None:
            return None
        try:
            df_pred = pd.DataFrame([features_dict])
            if self.encoders:
                for col in ['startingairport', 'destinationairport']:
                    if col in self.encoders and col in features_dict:
                        try:
                            encoded_col = col + '_encoded'
                            df_pred[encoded_col] = self.encoders[col].transform([features_dict[col]])[0]
                        except:
                            df_pred[col + '_encoded'] = 0

            for feature in self.features:
                if feature not in df_pred.columns:
                    df_pred[feature] = 0
            return float(self.model.predict(df_pred[self.features])[0])
        except Exception as e:
            print(f"[Model Error] 预测计算失败: {str(e)}")
            return None

    def predict_price_trend(self, origin: str, destination: str, departure_date: str, days: int = 7):
        cache_key = f"predict:{origin}:{destination}:{departure_date}:{days}"

        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                print(f"[Redis Error] {str(e)}")

        if self.model and self.encoders:
            try:
                trend_data = self._predict_with_model(origin, destination, departure_date, days)
            except Exception as e:
                print(f"[Model Error] 模型推演异常，转为降级: {str(e)}")
                trend_data = self._generate_fallback_trend(departure_date, days)
        else:
            trend_data = self._generate_fallback_trend(departure_date, days)

        statistics = self._calculate_statistics(trend_data)
        best_buy = self._find_best_buy(trend_data)
        suggestion = self._generate_suggestion(trend_data)

        # 保持 camelCase 前端契约
        result = {
            "departure": origin.upper(),
            "destination": destination.upper(),
            "startDate": departure_date,
            "totalDays": len(trend_data),
            "trend": trend_data,
            "statistics": statistics,
            "bestBuy": best_buy,
            "suggestion": suggestion
        }

        if redis_client and trend_data:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False))
            except Exception as e:
                print(f"[Redis Error] {str(e)}")

        return result

    def _predict_with_model(self, origin: str, destination: str, departure_date: str, days: int = 7):
        search_date = datetime.strptime("2022-04-19", "%Y-%m-%d").date()
        flight_date = datetime.strptime(departure_date, "%Y-%m-%d").date()

        total_days = (flight_date - search_date).days
        if total_days <= 0:
            return self._generate_fallback_trend(departure_date, days)

        predict_days = min(days, total_days + 1)

        # 100% 解耦自主从数据库捞取基准价格
        baseline_fare = self._get_route_avg_price_from_db(origin, destination)

        airline_code = 'DL'
        segment_count = 1
        distance = 2475
        duration_hours = 6.0
        seatsremaining = 150

        trend_data = []
        for day_offset in range(predict_days):
            current_date = search_date + timedelta(days=day_offset)
            days_to_departure = total_days - day_offset

            features_dict = {
                'startingairport': origin.upper(),
                'destinationairport': destination.upper(),
                'segmentsairlinecode': airline_code,
                'segment_count': segment_count,
                'stop_count': max(0, segment_count - 1),
                'distance': distance,
                'duration_hours': duration_hours,
                'seatsremaining': seatsremaining,
                'days_to_departure': max(0, days_to_departure),
                'flight_month': flight_date.month,
                'flight_dayofweek': current_date.weekday(),
                'is_weekend': 1 if current_date.weekday() in [5, 6] else 0,
                'is_summer': 1 if flight_date.month in [6, 7, 8] else 0,
                'is_holiday': 1 if flight_date.month in [7, 8, 12] else 0,
                'airline_score': self.airline_rank.get(airline_code, 0.5),

                'price_per_stop': baseline_fare / (max(0, segment_count - 1) + 1),
                'duration_per_stop': duration_hours / (max(0, segment_count - 1) + 1),
                'price_per_hour': baseline_fare / (duration_hours + 0.1),
                'price_per_mile': baseline_fare / (distance + 0.1)
            }

            price = self._predict_single(features_dict)
            if price is None:
                price = baseline_fare + np.random.randint(-15, 15)

            trend_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "daysToDeparture": max(0, days_to_departure),
                "predictedPrice": round(price, 2)
            })

        return trend_data

    def _generate_fallback_trend(self, departure_date: str, days: int = 7):
        try:
            base_date = datetime.strptime(departure_date, "%Y-%m-%d")
        except ValueError:
            base_date = datetime.now()

        mock_prices = [180.50, 166.61, 155.00, 162.30, 175.00, 190.00, 210.00]
        trend = []
        today = datetime.strptime("2022-04-19", "%Y-%m-%d").date()
        flight_date = base_date.date()
        total_days = (flight_date - today).days

        for i in range(min(days, len(mock_prices))):
            curr_date = today + timedelta(days=i)
            trend.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "daysToDeparture": max(0, total_days - i),
                "predictedPrice": mock_prices[i % len(mock_prices)]
            })
        return trend

    def _calculate_statistics(self, trend_data):
        if not trend_data:
            return {}
        prices = [item['predictedPrice'] for item in trend_data]
        return {
            "minPrice": round(min(prices), 2),
            "maxPrice": round(max(prices), 2),
            "avgPrice": round(sum(prices) / len(prices), 2),
            "totalDays": len(trend_data)
        }

    def _find_best_buy(self, trend_data):
        if not trend_data:
            return {}
        best = min(trend_data, key=lambda x: x['predictedPrice'])
        return {
            "date": best['date'],
            "daysToDeparture": best['daysToDeparture'],
            "price": best['predictedPrice']
        }

    def _generate_suggestion(self, trend_data):
        if not trend_data:
            return "暂无建议"
        best = min(trend_data, key=lambda x: x['predictedPrice'])
        current = trend_data[0]['predictedPrice'] if trend_data else 0
        last = trend_data[-1]['predictedPrice'] if trend_data else 0

        # 修正对齐：将原本的 best['price'] 变更为规范的 best['predictedPrice']
        if current < 170.0:
            return f"当前价格处于近期极低水平（${current:.2f}），建议立即购票。最佳购买日期：{best['date']}，价格：${best['predictedPrice']:.2f}"
        elif last > current:
            return f"预测价格呈明显上涨趋势（将从${current:.2f}涨至${last:.2f}），建议尽快购买。最佳购买日期：{best['date']}，价格：${best['predictedPrice']:.2f}"
        else:
            return f"价格相对稳定，建议保持关注。最佳购买日期：{best['date']}，价格：${best['predictedPrice']:.2f}"


# 实例化
price_predict_service = PricePredictService()