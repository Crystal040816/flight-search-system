# backend/app/services/destinations_service.py
import os
import pymysql
from app.config import Config


class DestinationsService:
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

    def get_lowest_price_destinations(self, departure_city: str, flight_date: str, search_date: str = None):
        """
        根据出发城市名 (origin_city)、起飞日期。若未传 search_date，自动匹配数据库中针对该航线日期的最新快照分区。
        """
        try:
            conn = self._get_db_connection()
        except Exception as e:
            print(f"[MySQL Connection Error] 数据库连接失败: {str(e)}")
            return self._get_fallback_destinations()

        # 1. 动态自适应：如果未传入快照日，自动在 SQL 级查出当前城市和起飞日期下，最新（最大）的一个 search_date
        if not search_date:
            try:
                sql_max = """
                    SELECT MAX(search_date) as max_date 
                    FROM ads_route_cabin_lowest_price 
                    WHERE origin_city = %s AND flight_date = %s
                """
                with conn.cursor() as cursor:
                    cursor.execute(sql_max, [departure_city, flight_date])
                    res = cursor.fetchone()
                    # 如果查到了最大日期，格式化为字符串；否则使用 2022-04-19 兜底
                    search_date = res["max_date"].strftime("%Y-%m-%d") if res and res["max_date"] else "2022-04-19"
                    print(f"[SQL Debug] 目的地地图接口自动匹配到最新快照分区日: {search_date}")
            except Exception as e:
                print(f"[SQL Debug] 动态获取最新分区日失败，使用保底 2022-04-19: {str(e)}")
                search_date = "2022-04-19"

        # 2. 精准聚合 SQL
        sql = """
              SELECT origin_city              as departureCity, \
                     market_origin            as departure, \
                     destination_city         as city, \
                     market_destination       as destination, \
                     destination_country_name as country, \
                     MIN(lowest_price)        as lowestPrice
              FROM ads_route_cabin_lowest_price
              WHERE origin_city = %s
                AND flight_date = %s
                AND search_date = %s
              GROUP BY origin_city, market_origin, destination_city, market_destination, destination_country_name
              ORDER BY lowestPrice ASC \
              """

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, [departure_city, flight_date, search_date])
                rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append({
                    "departureCity": row["departureCity"],
                    "departure": row["departure"],
                    "city": row["city"],
                    "destination": row["destination"],
                    "country": row["country"] if row["country"] else "Unknown",
                    "continent": "N/A",
                    "lowestPrice": float(row["lowestPrice"]) if row["lowestPrice"] else 0.0
                })
            return results

        except Exception as e:
            print(f"[MySQL Query Error] 目的地地图聚合失败 (已进入保底降级): {str(e)}")
            return self._get_fallback_destinations()
        finally:
            conn.close()

    def _get_fallback_destinations(self):
        """降级方案"""
        return []


# 实例化
destinations_service = DestinationsService()