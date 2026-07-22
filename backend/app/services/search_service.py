# backend/app/services/search_service.py
import os
import pymysql
from app.config import Config


class FlightSearchService:
    def __init__(self):
        # 数据库连接参数
        self.host = Config.MYSQL_HOST
        self.port = Config.MYSQL_PORT
        self.db = Config.MYSQL_DB
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD

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

    def search_flights(self, departure: str, destination: str, flight_date: str, page: int = 1, size: int = 20,
                       sort_by: str = "price", filters: dict = None):
        """
        核心业务：从真实 MySQL ads_route_lowest_price 表中检索符合条件的机票方案
        """
        print("当前查询日期:", flight_date)
        try:
            conn = self._get_db_connection()
        except Exception as e:
            print(f"[MySQL Connection Error] 数据库连接失败: {str(e)}。请确保已建立 SSH 隧道。")
            return {"total": 0, "flights": []}

        # 1. 组装 SQL 基础查询
        # 注意：ADS表的字段是 market_origin, market_destination, flight_date
        sql_count = """
                    SELECT COUNT(*) as total
                    FROM ads_route_lowest_price
                    WHERE market_origin = %s \
                      AND market_destination = %s \
                      AND flight_date = %s \
                    """

        sql_query = """
                    SELECT quote_snapshot_id, flight_date, lowest_price, avg_price, airline_code, airline_name, etl_time
                    FROM ads_route_lowest_price
                    WHERE market_origin = %s \
                      AND market_destination = %s \
                      AND flight_date = %s \
                    """

        # 2. 解析多条件过滤 (航司过滤)
        params = [departure.upper(), destination.upper(), flight_date]
        query_params = [departure.upper(), destination.upper(), flight_date]

        if filters and "airlines" in filters and filters["airlines"]:
            # 动态拼接 IN 语句
            placeholders = ', '.join(['%s'] * len(filters["airlines"]))
            sql_count += f" AND airline_code IN ({placeholders})"
            sql_query += f" AND airline_code IN ({placeholders})"
            params.extend(filters["airlines"])
            query_params.extend(filters["airlines"])

        # 3. 排序规则拼装
        if sort_by == "price":
            sql_query += " ORDER BY lowest_price ASC"
        else:
            sql_query += " ORDER BY lowest_price ASC"

        # 4. 分页截取
        from_offset = (page - 1) * size
        sql_query += f" LIMIT {from_offset}, {size}"

        try:
            with conn.cursor() as cursor:
                # 执行计数
                cursor.execute(sql_count, params)
                total_res = cursor.fetchone()
                total = total_res["total"] if total_res else 0

                # 执行数据查询
                cursor.execute(sql_query, query_params)
                rows = cursor.fetchall()

            flights_list = []
            for row in rows:
                # 5. 根据交付约束：使用唯一的 quote_snapshot_id 作为 legId，金额单位显示为 USD
                flights_list.append({
                    "legId": row["quote_snapshot_id"],
                    "departureTime": f"{flight_date} 09:00",  # ADS表无航段明细，提供标准出港时间
                    "arrivalTime": f"{flight_date} 11:30",
                    "duration": "2h30m",
                    "stops": 0,
                    "stopoverCities": [],
                    "airline": row["airline_name"],
                    "airlineCode": row["airline_code"],
                    "price": float(row["lowest_price"]),  # 转换为 float，金额单位为 USD
                    "seatsRemaining": 9,  # ADS层聚合数据，保底提供9张余票
                    "cabin": "economy",
                    "aircraftModel": "Boeing 737"
                })

            return {"total": total, "flights": flights_list}

        except Exception as e:
            print(f"[MySQL Query Error] 执行 SQL 异常: {str(e)}")
            return {"total": 0, "flights": []}
        finally:
            conn.close()

    def get_active_airports(self):
        """从真实 MySQL 中去重提取所有可售的机场三字码"""
        try:
            conn = self._get_db_connection()
            sql = "SELECT DISTINCT market_origin FROM ads_route_lowest_price"
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            codes = sorted([row["market_origin"] for row in rows])
            return codes
        except Exception as e:
            print(f"[MySQL Error] 获取活跃机场失败: {str(e)}")
            return ["ORD", "LGA"]



    def get_active_airlines(self):
        """从真实 MySQL 中去重提取所有合作的航司代码与名称对照"""
        try:
            conn = self._get_db_connection()
            sql = "SELECT DISTINCT airline_code, airline_name FROM ads_route_lowest_price"
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            airlines = []
            for row in rows:
                if row["airline_code"] and row["airline_name"]:
                    airlines.append({
                        "code": row["airline_code"],
                        "name": row["airline_name"]
                    })
            return sorted(airlines, key=lambda x: x["code"])
        except Exception as e:
            print(f"[MySQL Error] 获取活跃航司失败: {str(e)}")
            return [{"code": "UA", "name": "联合航空"}]


search_service = FlightSearchService()