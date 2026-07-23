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

        if os.path.exists(self.model_path):
            try:
                recommend_config = joblib.load(self.model_path)
                self.weights = recommend_config.get('weights', self.weights)
                print(f"[Recommend Service] 成功加载算法推荐权重配置: {self.weights}")
            except Exception as e:
                print(f"[Recommend Service] 权重加载失败: {str(e)}")
        else:
            print(f"[Recommend Service] 找不到 recommend_model.pkl，使用默认权重")

    def _parse_duration_hours(self, duration_str: str) -> float:
        try:
            parts = duration_str.replace("m", "").split("h")
            return float(parts[0]) + float(parts[1]) / 60.0
        except:
            return 2.5

    def _get_airline_score(self, airline_code: str) -> float:
        airline_rank = {'DL': 0.9, 'AA': 0.85, 'UA': 0.85, 'B6': 0.75, 'WN': 0.8}
        if not airline_code:
            return 0.5
        first = str(airline_code).split('||')[0] if '||' in str(airline_code) else str(airline_code)
        return airline_rank.get(first.upper(), 0.5)

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
                # 1. 检索候选集 (传入默认 searchDate=2022-04-19 确保数仓对齐)
                candidate_data = search_service.search_flights(
                    departure=departure,
                    destination=destination,
                    flight_date=flight_date,
                    search_date="2022-04-19",  # 显式对齐默认分区日
                    page=1,
                    size=50
                )
                candidates = candidate_data.get("flights", [])

                if candidates:
                    scored_flights = []

                    # 2. 提取最高最低值时，加入安全过滤与零值守护
                    prices = [float(f.get("lowestPrice") or 150.0) for f in candidates]
                    min_price, max_price = min(prices), max(prices)
                    price_diff = (max_price - min_price + 1.0)

                    durations = [self._parse_duration_hours(f.get("duration") or "2h30m") for f in candidates]
                    min_dur, max_dur = min(durations), max(durations)
                    dur_range = (max_dur - min_dur + 1.0)

                    seats = [int(f.get("seatsRemaining") or 9) for f in candidates]
                    max_seats = max(seats) if seats else 9
                    seats_range = max_seats + 1.0

                    for f in candidates:
                        # 3. 强空值容错处理：确保所有参与数学计算的变量绝不为 None
                        lowest_price = float(f.get("lowestPrice") or 150.0)
                        stops = int(f.get("stops") or 0)
                        seats_rem = int(f.get("seatsRemaining") or 9)
                        airline_code = f.get("airlineCode") or "UA"
                        duration_str = f.get("duration") or "2h30m"
                        dur_hours = self._parse_duration_hours(duration_str)

                        # 3.1 推荐多维特征打分公式 (安全变量计算)
                        price_score = 1.0 - (lowest_price - min_price) / price_diff
                        stops_score = 1.0 / (stops + 1.0)
                        seats_score = seats_rem / seats_range
                        direct_score = 1.0 if stops == 0 else 0.0
                        duration_score = 1.0 - (dur_hours - min_dur) / dur_range
                        airline_score = self._get_airline_score(airline_code)

                        # 4. 乘加算法算出推荐得分 (对齐算法 total_score)
                        total_score = (
                                price_score * self.weights.get('price', 0.3) +
                                stops_score * self.weights.get('stops', 0.25) +
                                seats_score * self.weights.get('seats', 0.15) +
                                airline_score * self.weights.get('airline', 0.15) +
                                direct_score * self.weights.get('direct', 0.1) +
                                duration_score * self.weights.get('duration', 0.05)
                        )

                        f_copy = f.copy()
                        f_copy["totalScore"] = round(float(total_score), 4)
                        scored_flights.append(f_copy)

                    # 5. 排序并输出前 10 个推荐航班
                    scored_flights = sorted(scored_flights, key=lambda x: x["totalScore"], reverse=True)

                    for idx, flight in enumerate(scored_flights[:10]):
                        recommendations.append({
                            "rank": idx + 1,
                            "reason": f"综合性价比打分高达 {flight['totalScore']}，全网第 {idx + 1} 推荐",
                            "flight": flight
                        })
                else:
                    recommendations = self._generate_fallback_recommendations(flight_date)
            except Exception as e:
                # 打印出具体的崩溃信息，协助排查
                print(f"[Model Error] 推荐排序算法崩溃 (已触发保底): {str(e)}")
                recommendations = self._generate_fallback_recommendations(flight_date)
        else:
            recommendations = self._generate_fallback_recommendations(flight_date)

        # 6. 写入 Redis 缓存
        if redis_client and recommendations:
            try:
                redis_client.setex(cache_key, 1800, json.dumps(recommendations, ensure_ascii=False))
            except Exception as e:
                print(f"[Redis Error] {str(e)}")

        return recommendations

    def _generate_fallback_recommendations(self, flight_date: str):
        return []


# 实例化
recommend_service = RecommendService()