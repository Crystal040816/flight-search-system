# backend/app/services/splice_service.py
import os
import json
import joblib
import pymysql
from app.config import Config


class SpliceService:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "splice_model.pkl")
        self.graph = {}
        self.airports = []

        # 数据库直连参数，作为 ES 连接失败时的“B 计划”容灾备份
        self.host = Config.MYSQL_HOST
        self.port = Config.MYSQL_PORT
        self.db = Config.MYSQL_DB
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD

        # 加载物理邻接表字典
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

    def get_spliced_routes(self, departure: str, destination: str, date: str, max_stops: int = 2):
        """
        极限性能优化版一中转拼接：优先从 Elasticsearch 读取，若失败则自动降级为 MySQL 容灾备份
        """
        # 1. 局部动态导入 redis_client 和 es_client，防止初始化时崩溃
        try:
            from app import redis_client, es_client
        except ImportError:
            redis_client = None
            es_client = None

        cache_key = f"splice:{departure}:{destination}:{date}:{max_stops}"

        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception:
                pass

        spliced_routes = []
        dep_code = departure.upper()
        dest_code = destination.upper()

        # ====================================================================
        # A 计划：优先从具备倒排索引的 Elasticsearch 极速捞取当日所有航段数据
        # ====================================================================
        db_routes = {}
        if es_client:
            try:
                # 组装 ES 查询 DSL 语句
                body = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"flight_date": date}},
                                {"term": {"search_date": "2022-04-19"}}
                            ]
                        }
                    },
                    "size": 5000  # 一次性最多读入 5000 条当日航段
                }
                # 请与数据同学确认 ES 中索引的名称 (此处暂定为 ads_flight_search)
                response = es_client.search(index="ads_flight_search", body=body)
                hits = response["hits"]["hits"]

                # 将数据组装为内存 Map。Key 为 (起飞, 降落) 元组，实现 O(1) 极速检索
                for hit in hits:
                    source = hit["_source"]
                    key = (source["market_origin"].upper(), source["market_destination"].upper())
                    db_routes[key] = {
                        "price": float(source.get("total_fare") or 200.0),
                        "airline": source.get("airline_name") or "联合航空",
                        "airlineCode": source.get("airline_code") or "UA",
                        "aircraftModel": source.get("equipment_description") or "Boeing 737"
                    }
                print(f"[ES Debug] 成功从 Elasticsearch 读取当日候选航段数: {len(db_routes)}")
            except Exception as e:
                print(f"[ES Error] 从 ES 读取数据失败: {str(e)}。正在自动降级，尝试从 MySQL 读取。")
                db_routes = {}

        # ====================================================================
        # B 计划：如果 ES 挂了或没数据，自动降级启用 MySQL 容灾备份查询
        # ====================================================================
        if not db_routes:
            try:
                conn = self._get_db_connection()
                sql_all = """
                          SELECT market_origin, \
                                 market_destination, \
                                 lowest_price, \
                                 airline_name, \
                                 airline_code, \
                                 equipment_summary
                          FROM ads_route_cabin_lowest_price
                          WHERE flight_date = %s \
                            AND search_date = '2022-04-19' \
                          """
                with conn.cursor() as cursor:
                    cursor.execute(sql_all, [date])
                    rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    key = (row["market_origin"].upper(), row["market_destination"].upper())
                    db_routes[key] = {
                        "price": float(row["lowest_price"]) if row["lowest_price"] else 200.0,
                        "airline": row["airline_name"] or "联合航空",
                        "airlineCode": row["airline_code"] or "UA",
                        "aircraftModel": row["equipment_summary"] or "Boeing 737"
                    }
                print(f"[MySQL Fallback] 成功从 MySQL 读取当日候选航段数: {len(db_routes)}")
            except Exception as e:
                print(f"[SQL Debug] 容灾方案 MySQL 查询失败: {str(e)}")

        # 2. 内存级拓扑图拼接与数据碰撞
        if self.graph and dep_code in self.graph:
            try:
                first_legs = self.graph[dep_code]
                for leg in first_legs:
                    mid_airport = leg.get("to")
                    if mid_airport in self.graph:
                        second_legs = self.graph[mid_airport]
                        for next_leg in second_legs:
                            if next_leg.get("to") == dest_code:
                                seg1_info = db_routes.get((dep_code, mid_airport))
                                seg2_info = db_routes.get((mid_airport, dest_code))

                                if not seg1_info or not seg2_info:
                                    continue

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

        # 3. 尝试回写 Redis 缓存
        if redis_client and spliced_routes:
            try:
                redis_client.setex(cache_key, 1800, json.dumps(spliced_routes, ensure_ascii=False))
            except Exception:
                pass

        return spliced_routes


# 实例化
splice_service = SpliceService()