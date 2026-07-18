# backend/app/services/splice_service.py
import os
import json
import joblib
from app.models.flight import FlightSegment, SplicedRoute

try:
    from backend.app import redis_client
except ImportError:
    try:
        from app import redis_client
    except ImportError:
        redis_client = None


class SpliceService:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "route_splicer.pkl")
        self.model = None

        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"[Splice Service] 成功加载拼接算法: {self.model_path}")
            except Exception as e:
                print(f"[Splice Service] 算法加载失败，启用降级逻辑: {str(e)}")
        else:
            print(f"[Splice Service] 未找到拼接算法，启用默认组合方案。")

    def get_spliced_routes(self, departure: str, destination: str, date: str, max_stops: int = 2):
        """
        根据中转算法获取最优的机票拼接组合方案
        """
        cache_key = f"splice:{departure}:{destination}:{date}:{max_stops}"

        # 1. 尝试从 Redis 读取缓存
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    print(f"[Redis Hit] 命中路线拼接缓存: {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                print(f"[Redis Error] 缓存读取异常: {str(e)}")

        # 2. 调用拼接算法
        if self.model:
            try:
                # 联调时，此处传入两段航班的数据源并交由组员 B 的拼接引擎去交叉组合
                spliced_routes = self.model.splice_routes(departure, destination, date, max_stops)
            except Exception as e:
                print(f"[Model Error] 拼接计算异常，转为降级方案: {str(e)}")
                spliced_routes = self._generate_fallback_spliced_routes(departure, destination, date)
        else:
            spliced_routes = self._generate_fallback_spliced_routes(departure, destination, date)

        # 3. 写入缓存
        if redis_client:
            try:
                redis_client.setex(cache_key, 1800, json.dumps(spliced_routes, ensure_ascii=False))  # 缓存30分钟
                print(f"[Redis Save] 拼接方案成功写入缓存")
            except Exception as e:
                print(f"[Redis Error] 缓存写入异常: {str(e)}")

        return spliced_routes

    def _generate_fallback_spliced_routes(self, departure: str, destination: str, date: str):
        """默认路线拼接模拟生成"""
        seg1 = FlightSegment(
            from_airport=departure,
            to_airport="DOH",
            airline="卡塔尔航空",
            airlineCode="QR",
            departureTime=f"{date} 01:00",
            arrivalTime=f"{date} 05:00",
            price=3000,
            duration="4h"
        )
        seg2 = FlightSegment(
            from_airport="DOH",
            to_airport=destination,
            airline="卡塔尔航空",
            airlineCode="QR",
            departureTime=f"{date} 08:00",
            arrivalTime=f"{date} 13:00",
            price=6000,
            duration="5h"
        )
        route = SplicedRoute(
            totalPrice=9000,
            totalDuration="15h",
            stops=1,
            segments=[seg1, seg2]
        )
        return [route.to_dict()]


splice_service = SpliceService()