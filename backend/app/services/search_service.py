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

    def _format_iso_time(self, time_str: str) -> str:
        """
        高安全解析：将 "2022-06-08T15:51:00.000-07:00"
        解析并格式化为 "2022-06-08, 15:51:00"
        """
        if not time_str:
            return "N/A"
        try:
            parts = time_str.split('T')
            date_part = parts[0]
            time_part = parts[1].split('.')[0]
            return f"{date_part}, {time_part}"
        except Exception:
            return time_str

    def _format_duration_minutes(self, minutes) -> str:
        """
        将整数分钟数（如 150）转换为 "2时30分" 的格式
        """
        if minutes is None or minutes == "":
            return "N/A"
        try:
            total_mins = int(minutes)
            hrs = total_mins // 60
            mins = total_mins % 60
            if hrs > 0:
                return f"{hrs}时{mins}分"
            else:
                return f"{mins}分"
        except Exception:
            return f"{minutes}分"

    def get_active_origin_cities(self):
        try:
            conn = self._get_db_connection()
            sql = """
                  SELECT DISTINCT origin_city as city_name
                  FROM ads_route_cabin_lowest_price
                  WHERE origin_city IS NOT NULL \
                    AND origin_city != '' \
                  """
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            conn.close()
            return sorted([row["city_name"] for row in rows])
        except Exception as e:
            print(f"[MySQL Error] 获取出发城市列表失败: {str(e)}")
            return ["Chicago", "Boston", "New York"]

    def get_active_destination_cities(self):
        try:
            conn = self._get_db_connection()
            sql = """
                  SELECT DISTINCT destination_city as city_name
                  FROM ads_route_cabin_lowest_price
                  WHERE destination_city IS NOT NULL \
                    AND destination_city != '' \
                  """
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            conn.close()
            return sorted([row["city_name"] for row in rows])
        except Exception as e:
            print(f"[MySQL Error] 获取目的城市列表失败: {str(e)}")
            return ["New York", "San Francisco", "Boston"]

    def get_active_flight_dates(self):
        try:
            conn = self._get_db_connection()
            sql = "SELECT DISTINCT flight_date FROM ads_route_cabin_lowest_price ORDER BY flight_date ASC"
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            conn.close()
            return [row["flight_date"].strftime("%Y-%m-%d") for row in rows]
        except Exception as e:
            print(f"[MySQL Error] 获取可用日期失败: {str(e)}")
            return []

    def get_active_cabins(self):
        try:
            conn = self._get_db_connection()
            sql = """
                  SELECT DISTINCT cabin_type as cabin
                  FROM ads_route_cabin_lowest_price
                  WHERE cabin_type IS NOT NULL \
                    AND cabin_type != '' \
                  """
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            conn.close()
            return sorted([row["cabin"] for row in rows])
        except Exception as e:
            print(f"[MySQL Error] 获取可用舱型失败: {str(e)}")
            return []

    def get_active_origins(self, city_filter: str = None):
        try:
            conn = self._get_db_connection()
            if city_filter:
                sql = """
                      SELECT DISTINCT market_origin as airport_code
                      FROM ads_route_cabin_lowest_price
                      WHERE origin_city = %s \
                      """
                params = [city_filter]
            else:
                sql = "SELECT DISTINCT market_origin as airport_code FROM ads_route_cabin_lowest_price"
                params = []
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            conn.close()
            return sorted([row["airport_code"] for row in rows])
        except Exception as e:
            print(f"[MySQL Error] 获取出发机场失败: {str(e)}")
            return ["ORD", "LGA"]

    def get_active_destinations(self, city_filter: str = None):
        try:
            conn = self._get_db_connection()
            if city_filter:
                sql = """
                      SELECT DISTINCT market_destination as airport_code
                      FROM ads_route_cabin_lowest_price
                      WHERE destination_city = %s \
                      """
                params = [city_filter]
            else:
                sql = "SELECT DISTINCT market_destination as airport_code FROM ads_route_cabin_lowest_price"
                params = []
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            conn.close()
            return sorted([row["airport_code"] for row in rows])
        except Exception as e:
            print(f"[MySQL Error] 获取目的机场失败: {str(e)}")
            return ["LGA", "SFO"]

    def search_flights(self, departure: str = None, destination: str = None,
                       departure_city: str = None, destination_city: str = None,
                       flight_date: str = None, search_date: str = None,
                       cabin_code: str = None, page: int = 1, size: int = 20,
                       sort_by: str = "price", filters: dict = None):
        """
        100% 动态多表联查：直连真实 ads_route_cabin_lowest_price 表，解析真实的起降时间与飞行时长
        """
        print(
            f"[SQL Debug] 收到查询请求: 出发={departure}/{departure_city}, 目的={destination}/{destination_city}, 出行日期={flight_date}, 搜索日={search_date}, 舱型={cabin_code}")

        try:
            conn = self._get_db_connection()
        except Exception as e:
            print(f"[MySQL Connection Error] {str(e)}")
            return {"total": 0, "flights": []}

        if not search_date:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT MAX(search_date) as max_date FROM ads_route_cabin_lowest_price")
                    res = cursor.fetchone()
                    search_date = res["max_date"].strftime("%Y-%m-%d") if res and res["max_date"] else "2022-04-19"
            except Exception as e:
                search_date = "2022-04-19"

        # 2. 组装 SQL 基础查询 (使用真实的新表)
        sql_base = """
            FROM ads_route_cabin_lowest_price lp
            LEFT JOIN ads_route_offer_rank rk 
                ON lp.search_date = rk.search_date 
               AND lp.market_origin = rk.market_origin 
               AND lp.market_destination = rk.market_destination
            LEFT JOIN ads_airline_offer_share sh 
                ON lp.search_date = sh.search_date 
               AND lp.airline_code = sh.airline_code
            WHERE lp.search_date = %s
              AND lp.flight_date = %s
        """

        params = [search_date, flight_date]

        if departure:
            sql_base += " AND lp.market_origin = %s"
            params.append(departure.upper())
        elif departure_city:
            sql_base += " AND lp.origin_city = %s"
            params.append(departure_city)

        if destination:
            sql_base += " AND lp.market_destination = %s"
            params.append(destination.upper())
        elif destination_city:
            sql_base += " AND lp.destination_city = %s"
            params.append(destination_city)

        if cabin_code and cabin_code.lower() not in ["all", "", "unknown"]:
            sql_base += " AND lp.cabin_type = %s"
            params.append(cabin_code)

        if filters and "airlines" in filters and filters["airlines"]:
            placeholders = ', '.join(['%s'] * len(filters["airlines"]))
            sql_base += f" AND lp.airline_code IN ({placeholders})"
            params.extend(filters["airlines"])

        sql_count = f"SELECT COUNT(*) as total {sql_base}"
        sql_query = f"""
            SELECT 
                lp.quote_snapshot_id, lp.market_origin, lp.market_destination, lp.flight_date,
                lp.lowest_price, lp.avg_price as route_avg_price, lp.airline_code, lp.airline_name,
                lp.origin_city, lp.origin_country_code, lp.origin_country_name,
                lp.destination_city, lp.destination_country_code, lp.destination_country_name,
                lp.seats_remaining, lp.cabin_type, lp.cabin_summary, lp.is_mixed_cabin, lp.equipment_summary,
                lp.departure_time_raw, lp.arrival_time_raw, lp.travel_duration_minutes,
                rk.rank_num, rk.previous_day_avg_price, rk.price_change_pct, rk.quote_count as route_quote_count, rk.distinct_leg_count,
                sh.offer_share_pct, sh.avg_price as airline_avg_price
            {sql_base}
        """

        if sort_by == "price":
            sql_query += " ORDER BY lp.lowest_price ASC"
        else:
            sql_query += " ORDER BY lp.lowest_price ASC"

        from_offset = (page - 1) * size
        sql_query += f" LIMIT {from_offset}, {size}"

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql_count, params)
                total_res = cursor.fetchone()
                total = total_res["total"] if total_res else 0

                cursor.execute(sql_query, params)
                rows = cursor.fetchall()

            flights_list = []
            for row in rows:
                flights_list.append({
                    "legId": row["quote_snapshot_id"],
                    "departureTime": self._format_iso_time(row["departure_time_raw"]),
                    "arrivalTime": self._format_iso_time(row["arrival_time_raw"]),
                    "duration": self._format_duration_minutes(row["travel_duration_minutes"]),

                    "lowestPrice": float(row["lowest_price"]) if row["lowest_price"] else 0.0,
                    "price": float(row["lowest_price"]) if row["lowest_price"] else 0.0,
                    "avgPrice": float(row["route_avg_price"]) if row["route_avg_price"] else 0.0,

                    # 1. 物理表一关联特征 (DWD 行程供给排行)
                    "routeRank": row["rank_num"] if row["rank_num"] else None,
                    "previousDayAvgPrice": float(row["previous_day_avg_price"]) if row[
                        "previous_day_avg_price"] else 0.0,
                    "priceChangePct": float(row["price_change_pct"]) if row["price_change_pct"] else 0.0,
                    "routeQuoteCount": int(row["route_quote_count"]) if row["route_quote_count"] else 0,
                    "distinctLegCount": int(row["distinct_leg_count"]) if row["distinct_leg_count"] else 0,

                    # 2. 物理表二关联特征 (航司供给占比)
                    "offerSharePct": float(row["offer_share_pct"]) if row["offer_share_pct"] else 0.0,
                    "airlineAvgPrice": float(row["airline_avg_price"]) if row["airline_avg_price"] else 0.0,

                    "airline": row["airline_name"],
                    "airlineCode": row["airline_code"],
                    "departure": row["market_origin"],
                    "departureCity": row["origin_city"],
                    "departureCountryCode": row["origin_country_code"],
                    "departureCountryName": row["origin_country_name"],
                    "destination": row["market_destination"],
                    "destinationCity": row["destination_city"],
                    "destinationCountryCode": row["destination_country_code"],
                    "destinationCountryName": row["destination_country_name"],
                    "cabin": row["cabin_type"],
                    "cabinSummary": row["cabin_summary"],
                    "isMixedCabin": bool(row["is_mixed_cabin"]),
                    "stops": 0,
                    "aircraftModel": row["equipment_summary"],
                    "seatsRemaining": row["seats_remaining"]
                })

            return {"total": total, "flights": flights_list}

        except Exception as e:
            print(f"[MySQL Query Error] 执行 SQL 异常: {str(e)}")
            return {"total": 0, "flights": []}
        finally:
            conn.close()

    def get_active_airlines(self):
        try:
            conn = self._get_db_connection()
            sql = "SELECT DISTINCT airline_code, airline_name FROM ads_route_cabin_lowest_price"
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            conn.close()
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
            return []


# 实例化
search_service = FlightSearchService()