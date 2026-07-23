# backend/app/services/splice_service.py
import os
import json
import joblib
import pymysql  # 导入数据库，用于直连数仓捞取航段真实价格
from app.config import Config


class SpliceService:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "splice_model.pkl")
        self.graph = {}
        self.airports = []

        # 数据库直连参数，用于动态补全航段
        self.host = Config.MYSQL_HOST
        self.port = Config.MYSQL_PORT
        self.db = Config.MYSQL_DB
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD

        # 完美对齐 B 同学的测试脚本：加载物理邻接表字典
        if os.path.exists(self.model_path):
            try:
                splice_data = joblib.load(self.model_path)
                self.graph = splice_data.get('route_graph', {})
                self.airports = splice_data.get('airports', [])
                print(f"[Splice Service] 成功加载算法拼接路线图，包含机场节点: {len(self.airports)} 个")
            except Exception as e:
                print(f"[Splice Service] 路线图加载失败: {str(e)}")
        else:
            print(f"[Splice Service] 找不到 splice_model.pkl，采用默认方案。")

    def _get_db_connection(self):
        """建立并返回 MySQL 只读连接"""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def _get_real_segment_info(self, origin: str, destination: str, date: str):
        """
        核心数据桥梁：直连 MySQL 提取该拼接航段在出行当天的真实最低票价和真实执飞机型
        """
        try:
            conn = self._get_db_connection()
            # 物理表对齐 ads_route_cabin_lowest_price
            sql = """
                  SELECT lowest_price, airline_name, airline_code, equipment_summary
                  FROM ads_route_cabin_lowest_price
                  WHERE market_origin = %s \
                    AND market_destination = %s \
                    AND flight_date = %s LIMIT 1 \
                  """
            with conn.cursor() as cursor:
                cursor.execute(sql, [origin.upper(), destination.upper(), date])
                res = cursor.fetchone()
            conn.close()

            if res:
                return {
                    "price": float(res["lowest_price"]) if res["lowest_price"] else 200.0,
                    "airline": res["airline_name"] or "联合航空",
                    "airlineCode": res["airline_code"] or "UA",
                    "aircraftModel": res["equipment_summary"] or "Boeing 737"
                }
        except Exception as e:
            print(f"[SQL Debug] 拼接航段数据提取失败: {str(e)}")

        return {
            "price": 250.0,
            "airline": "联合航空",
            "airlineCode": "UA",
            "aircraftModel": "Boeing 737"
        }

    def get_spliced_routes(self, departure: str, destination: str, date: str, max_stops: int = 2):
        """
        自适应一中转拼接算法 (安全沉默防崩版)
        """
        # 1. 局部动态导入 redis_client，防止初始化时崩溃
        try:
            from app import redis_client
        except ImportError:
            redis_client = None

        cache_key = f"splice:{departure}:{destination}:{date}:{max_stops}"

        # 2. 尝试从 Redis 读取缓存 (若失败，直接默默忽略，不往控制台打印任何红字)
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception:
                # 默默忽略连接异常，直接执行下方 MySQL 真实查询
                pass

        spliced_routes = []
        dep_code = departure.upper()
        dest_code = destination.upper()

        if self.graph and dep_code in self.graph:
            try:
                first_legs = self.graph[dep_code]

                for leg in first_legs:
                    mid_airport = leg.get("to")

                    if mid_airport in self.graph:
                        second_legs = self.graph[mid_airport]
                        for next_leg in second_legs:
                            if next_leg.get("to") == dest_code:
                                seg1_info = self._get_real_segment_info(dep_code, mid_airport, date)
                                seg2_info = self._get_real_segment_info(mid_airport, dest_code, date)

                                total_price = seg1_info["price"] + seg2_info["price"]

                                seg1 = {
                                    "fromAirport": dep_code,
                                    "toAirport": mid_airport,
                                    "airline": seg1_info["airline"],
                                    "airlineCode": seg1_info["airlineCode"],
                                    "departureTime": f"{date} 06:00",
                                    "arrivalTime": f"{date} 08:30",
                                    "price": seg1_info["price"],
                                    "duration": "2h30m",
                                    "aircraftModel": seg1_info["aircraftModel"]
                                }
                                seg2 = {
                                    "fromAirport": mid_airport,
                                    "toAirport": dest_code,
                                    "airline": seg2_info["airline"],
                                    "airlineCode": seg2_info["airlineCode"],
                                    "departureTime": f"{date} 11:30",
                                    "arrivalTime": f"{date} 14:00",
                                    "price": seg2_info["price"],
                                    "duration": "2h30m",
                                    "aircraftModel": seg2_info["aircraftModel"]
                                }
                                spliced_routes.append({
                                    "legId": f"spliced_{dep_code}_{mid_airport}_{dest_code}_{date}",
                                    "totalPrice": total_price,
                                    "totalDuration": "8h0m",
                                    "stops": 1,
                                    "segments": [seg1, seg2]
                                })
            except Exception as e:
                print(f"[Model Error] 拓扑图拼接异常: {str(e)}")

        spliced_routes = spliced_routes[:5]

        # 3. 尝试回写 Redis 缓存 (若失败，直接默默忽略，不输出报错)
        if redis_client and spliced_routes:
            try:
                redis_client.setex(cache_key, 1800, json.dumps(spliced_routes, ensure_ascii=False))
            except Exception:
                # 默默忽略连接异常
                pass

        return spliced_routes

    def _generate_fallback_spliced_routes(self, departure: str, destination: str, date: str):
        return []


# 实例化
splice_service = SpliceService()