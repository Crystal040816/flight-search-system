# backend/app/services/recommend_service.py
import os
import json
import joblib

try:
    from backend.app import redis_client
except ImportError:
    try:
        from app import redis_client
    except ImportError:
        redis_client = None

try:
    from app.services.search_service import search_service
except ImportError:
    search_service = None


class RecommendService:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "recommend_model.pkl")
        self.weights = {"price": 0.3, "stops": 0.25, "seats": 0.15, "airline": 0.15, "direct": 0.1, "duration": 0.05}

        # 加载真实推荐权重配置
        if os.path.exists(self.model_path):
            try:
                recommend_config = joblib.load(self.model_path)
                self.weights = recommend_config.get('weights', self.weights)
                print(f"[Recommend Service] 成功加载算法推荐权重配置: {self.weights}")
            except Exception as e:
                print(f"[Recommend Service] 权重配置加载失败，启用默认权重: {str(e)}")
        else:
            print(f"[Recommend Service] 找不到 recommend_model.pkl，采用默认配置运作")

    def get_recommendations(self, departure: str, destination: str, flight_date: str, preferences: dict = None):
        pref_str = json.dumps(preferences, sort_keys=True) if preferences else "default"
        cache_key = f"recommend:{departure}:{destination}:{flight_date}:{pref_str}"

        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                print(f"[Redis Error] {str(e)}")

        recommendations = []
        if search_service:
            try:
                # 1. 从 MySQL 中检索候选航班集
                candidate_data = search_service.search_flights(
                    departure=departure, destination=destination, flight_date=flight_date, page=1, size=50
                )
                candidates = candidate_data.get("flights", [])

                if candidates:
                    # 2. 映射多维度打分评分机制
                    scored_flights = []
                    prices = [f["price"] for f in candidates]
                    min_price, max_price = min(prices), max(prices)
                    price_diff = (max_price - min_price + 1.0)

                    for f in candidates:
                        # 归一化计算各维度得分
                        price_score = 1.0 - (f["price"] - min_price) / price_diff
                        stops_score = 1.0 / (f["stops"] + 1.0)
                        seats_score = f["seatsRemaining"] / 10.0
                        direct_score = 1.0 if f["stops"] == 0 else 0.0
                        duration_score = 0.8  # 基准时长分
                        airline_score = 0.85 if f["airlineCode"] in ['DL', 'AA', 'UA'] else 0.5

                        # 3. 乘加算法权重，算出最终综合评分
                        total_score = (
                                price_score * self.weights.get('price', 0.3) +
                                stops_score * self.weights.get('stops', 0.25) +
                                seats_score * self.weights.get('seats', 0.15) +
                                airline_score * self.weights.get('airline', 0.15) +
                                direct_score * self.weights.get('direct', 0.1) +
                                duration_score * self.weights.get('duration', 0.05)
                        )

                        f_copy = f.copy()
                        f_copy["totalScore"] = round(total_score, 4)
                        scored_flights.append(f_copy)

                    # 4. 按总分降序排列，推荐前10个航班
                    scored_flights = sorted(scored_flights, key=lambda x: x["totalScore"], reverse=True)

                    for idx, flight in enumerate(scored_flights[:10]):
                        recommendations.append({
                            "rank": idx + 1,
                            "reason": f"综合评分高达 {flight['totalScore']}，性价比极其优异",
                            "flight": flight
                        })
                else:
                    recommendations = self._generate_fallback_recommendations(flight_date)
            except Exception as e:
                print(f"[Model Error] 推荐排序执行异常: {str(e)}")
                recommendations = self._generate_fallback_recommendations(flight_date)
        else:
            recommendations = self._generate_fallback_recommendations(flight_date)

        if redis_client and recommendations:
            try:
                redis_client.setex(cache_key, 1800, json.dumps(recommendations, ensure_ascii=False))
            except Exception as e:
                print(f"[Redis Error] {str(e)}")

        return recommendations

    def _generate_fallback_recommendations(self, flight_date: str):
        return []


recommend_service = RecommendService()