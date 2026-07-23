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

    def get_lowest_price_destinations(self, departure_city: str, date: str = "2022-04-19"):
        """
        纯数仓驱动：根据出发城市名 (origin_city)，在 SQL 级聚合计算出所有可达目的地的最低票价与详细起降属性
        """
        try:
            conn = self._get_db_connection()
        except Exception as e:
            print(f"[MySQL Connection Error] 数据库连接失败: {str(e)}")
            return self._get_fallback_destinations()

        # 精妙的物理列聚合：支持多字段分组，直接捞出起降城市、机场及国家
        sql = """
              SELECT origin_city              as departureCity, \
                     market_origin            as departure, \
                     destination_city         as city, \
                     market_destination       as destination, \
                     destination_country_name as country, \
                     MIN(lowest_price)        as lowestPrice
              FROM ads_route_lowest_price
              WHERE origin_city = %s
                AND search_date = %s
              GROUP BY origin_city, market_origin, destination_city, market_destination, destination_country_name
              ORDER BY lowestPrice ASC \
              """

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, [departure_city, date])
                rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append({
                    "departureCity": row["departureCity"],  # 1. 出发城市 (物理 origin_city)
                    "departure": row["departure"],  # 2. 出发机场 (物理 market_origin)
                    "city": row["city"],  # 3. 目的城市 (物理 destination_city)
                    "destination": row["destination"],  # 4. 目的机场 (物理 market_destination)
                    "country": row["country"] if row["country"] else "Unknown",  # 5. 国家 (物理 destination_country_name)
                    "continent": "N/A",  # 6. 大洲 (提示：ADS表不包含大洲字段，为了不写手写映射，统一输出 N/A)
                    "lowestPrice": float(row["lowestPrice"]) if row["lowestPrice"] else 0.0  # 7. 最低票价
                })
            return results

        except Exception as e:
            print(f"[MySQL Query Error] 目的地地图聚合失败: {str(e)}")
            return self._get_fallback_destinations()
        finally:
            conn.close()

    def _get_fallback_destinations(self):
        """降级方案"""
        return []


# 实例化
destinations_service = DestinationsService()