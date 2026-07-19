# backend/app/services/destinations_service.py
import os

try:
    from backend.app import es_client
except ImportError:
    try:
        from app import es_client
    except ImportError:
        es_client = None


class DestinationsService:
    def __init__(self):
        # 对齐数仓表：出发市场下的低价目的地排行
        self.index_name = "ads_destination_rank"

    def get_lowest_price_destinations(self, departure: str, date: str):
        """
        根据出发城市和搜索日期，从数仓应用表 ads_destination_rank 获取目的地的最低报价排行
        """
        if not es_client:
            print("[Destinations Service] ES 未连接，启用 Mock")
            return self._get_fallback_destinations()

        # 组装 DSL
        body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"market_origin.keyword": departure.upper()}},
                        {"term": {"search_date": date}}  # 匹配该天的搜索抓取快照
                    ]
                }
            },
            "sort": [
                {"lowest_price": {"order": "asc"}}  # 按最低价升序排列
            ],
            "size": 30  # 返回排名前 30 的低价目的地
        }

        try:
            response = es_client.search(index=self.index_name, body=body)
            hits = response["hits"]["hits"]

            destinations = []
            for hit in hits:
                source = hit["_source"]
                destinations.append({
                    "destination": source.get("market_destination"),
                    "city": source.get("destination_city_name"),  # 由 dim_airport 维表关联出的城市名
                    "country": source.get("destination_country_name", "中国"),
                    "lowestPrice": float(source.get("lowest_price", 0))
                })

            return destinations

        except Exception as e:
            print(f"[ES Error] 无法从 ads_destination_rank 检索数据: {str(e)}")
            return self._get_fallback_destinations()

    def _get_fallback_destinations(self):
        return [
            {"destination": "PVG", "city": "上海", "country": "中国", "lowestPrice": 800.0},
            {"destination": "SIN", "city": "新加坡", "country": "新加坡", "lowestPrice": 2500.0}
        ]


destinations_service = DestinationsService()