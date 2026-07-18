# backend/app/services/recommend_service.py
import os
import json
import joblib
from app.models.flight import Flight

try:
    from backend.app import redis_client
except ImportError:
    try:
        from app import redis_client
    except ImportError:
        redis_client = None


class RecommendService:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "recommend_engine.pkl")
        self.model = None

        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"[Recommend Service] 成功加载推荐模型: {self.model_path}")
            except Exception as e:
                print(f"[Recommend Service] 模型加载失败，启用降级逻辑: {str(e)}")
        else:
            print(f"[Recommend Service] 未找到推荐模型，启用降级逻辑。")

    def get_recommendations(self, departure: str, destination: str, flight_date: str, preferences: dict = None):
        """
        获取多因素打分推荐航班列表
        """
        # 将偏好配置 hash 化，作为缓存 Key 的一部分
        pref_str = json.dumps(preferences, sort_keys=True) if preferences else "default"
        cache_key = f"recommend:{departure}:{destination}:{flight_date}:{pref_str}"

        # 1. 尝试读取 Redis 缓存
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    print(f"[Redis Hit] 命中智能推荐缓存: {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                print(f"[Redis Error] 缓存读取异常: {str(e)}")

        # 2. 调用推荐引擎打分或降级
        if self.model:
            try:
                # 联调时替换为算法同学具体的推荐计算 API
                recommendations = self.model.recommend(departure, destination, flight_date, preferences)
            except Exception as e:
                print(f"[Model Error] 推荐模型计算异常，转为降级方案: {str(e)}")
                recommendations = self._generate_fallback_recommendations(flight_date)
        else:
            recommendations = self._generate_fallback_recommendations(flight_date)

        # 3. 写入缓存
        if redis_client:
            try:
                redis_client.setex(cache_key, 1800, json.dumps(recommendations, ensure_ascii=False))  # 推荐结果缓存30分钟
                print(f"[Redis Save] 推荐结果成功写入缓存")
            except Exception as e:
                print(f"[Redis Error] 缓存写入异常: {str(e)}")

        return recommendations

    def _generate_fallback_recommendations(self, flight_date: str):
        """降级方案：返回标准评分航班 mock 列表"""
        # 使用你定义好的 Flight 实体返回
        flight_1 = Flight(
            flightNumber="CA1234",
            departureTime=f"{flight_date} 08:00",
            arrivalTime=f"{flight_date} 10:30",
            duration="2h30m",
            stops=0,
            airline="中国国航",
            airlineCode="CA",
            price=1200
        )
        flight_2 = Flight(
            flightNumber="MU5678",
            departureTime=f"{flight_date} 07:00",
            arrivalTime=f"{flight_date} 09:00",
            duration="2h0m",
            stops=0,
            airline="东方航空",
            airlineCode="MU",
            price=1500
        )
        return [
            {
                "rank": 1,
                "reason": "价格最低，性价比最高",
                "flight": flight_1.to_dict()
            },
            {
                "rank": 2,
                "reason": "总时长最短，直飞无中转",
                "flight": flight_2.to_dict()
            }
        ]


recommend_service = RecommendService()