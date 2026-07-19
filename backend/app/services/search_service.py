# backend/app/services/search_service.py
import os

try:
    from backend.app import es_client
except ImportError:
    try:
        from app import es_client
    except ImportError:
        es_client = None


class FlightSearchService:
    def __init__(self):
        # 对齐数仓：同步至 ES 的宽表索引名称
        self.index_name = "ads_flight_search"

    def search_flights(self, departure: str, destination: str, flight_date: str, page: int = 1, size: int = 20,
                       sort_by: str = "price", filters: dict = None):
        """
        从 ES 同步宽表 ads_flight_search 中读取真实报价数据
        """
        if not es_client:
            print("[Search Service] ES 客户端未连接，启用降级模拟")
            return self._generate_fallback_search(departure, destination, flight_date, page, size)

        # 1. 组装符合数仓逻辑的查询 DSL
        query_must = [
            {"term": {"market_origin.keyword": departure.upper()}},
            {"term": {"market_destination.keyword": destination.upper()}},
            {"term": {"flight_date": flight_date}}
        ]

        # 2. 过滤器组装
        if filters:
            if "airlines" in filters and filters["airlines"]:
                query_must.append({"terms": {"airline_code.keyword": filters["airlines"]}})
            if "maxStops" in filters and filters["maxStops"] is not None:
                query_must.append({"range": {"stop_count": {"lte": filters["maxStops"]}}})

            price_range = {}
            if "minPrice" in filters:
                price_range["gte"] = filters["minPrice"]
            if "maxPrice" in filters:
                price_range["lte"] = filters["maxPrice"]
            if price_range:
                query_must.append({"range": {"total_fare": price_range}})

        # 3. 排序解析
        sort_field = []
        if sort_by == "price":
            sort_field.append({"total_fare": {"order": "asc"}})
        elif sort_by == "duration":
            sort_field.append({"travel_duration_minutes": {"order": "asc"}})
        else:
            sort_field.append({"total_fare": {"order": "asc"}})

        from_offset = (page - 1) * size

        body = {
            "query": {"bool": {"must": query_must}},
            "from": from_offset,
            "size": size,
            "sort": sort_field
        }

        try:
            response = es_client.search(index=self.index_name, body=body)
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]

            flights_list = []
            for hit in hits:
                source = hit["_source"]

                # 转换时长：将数仓的 travel_duration_minutes (INT) 转为 "Xh Ym"
                duration_mins = source.get("travel_duration_minutes", 0)
                duration_str = f"{duration_mins // 60}h{duration_mins % 60}m" if duration_mins else "N/A"

                # 4. 根据数仓规范：用 leg_id 替代 flightNumber
                flights_list.append({
                    "legId": source.get("leg_id"),  # 唯一行程标识
                    "departureTime": source.get("departure_time_raw"),  # DWD航段明细
                    "arrivalTime": source.get("arrival_time_raw"),
                    "duration": duration_str,
                    "stops": source.get("stop_count", 0),
                    "stopoverCities": source.get("stopover_cities", []),  # DWD拼接解析出的中转城市
                    "airline": source.get("airline_name"),
                    "airlineCode": source.get("airline_code"),
                    "price": float(source.get("total_fare", 0)),
                    "seatsRemaining": source.get("seats_remaining", 0),
                    "cabin": source.get("cabin_code", "economy"),
                    "aircraftModel": source.get("equipment_description", "Unknown")  # DWD设备描述
                })

            return {"total": total, "flights": flights_list}

        except Exception as e:
            print(f"[ES Error] 无法从 ads_flight_search 检索数据: {str(e)}")
            return self._generate_fallback_search(departure, destination, flight_date, page, size)

    def _generate_fallback_search(self, departure: str, destination: str, flight_date: str, page: int, size: int):
        # 降级模拟逻辑：使用 legId
        mock_list = []
        for i in range(3):
            mock_list.append({
                "legId": f"leg_mock_{departure}_{destination}_{i}",
                "departureTime": f"{flight_date} 09:00",
                "arrivalTime": f"{flight_date} 11:30",
                "duration": "2h30m",
                "stops": 0,
                "stopoverCities": [],
                "airline": "中国国航",
                "airlineCode": "CA",
                "price": 850.00,
                "seatsRemaining": 9,
                "cabin": "economy",
                "aircraftModel": "Boeing 737"
            })
        return {"total": len(mock_list), "flights": mock_list}


search_service = FlightSearchService()