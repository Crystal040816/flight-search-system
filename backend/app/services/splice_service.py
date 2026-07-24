import json
import os
from collections import defaultdict

import joblib
import pymysql

from app.config import Config


class SpliceService:
    MIN_CONNECTION_SECONDS = 45 * 60
    MAX_CONNECTION_SECONDS = 12 * 60 * 60
    MAX_RESULTS = 5

    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "splice_model.pkl")
        self.graph = {}
        self.airports = []

        self.host = Config.MYSQL_HOST
        self.port = Config.MYSQL_PORT
        self.db = Config.MYSQL_DB
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD
        self.search_date = Config.SPLICE_SEARCH_DATE

        if os.path.exists(self.model_path):
            try:
                splice_data = joblib.load(self.model_path)
                self.graph = splice_data.get("route_graph", {})
                self.airports = splice_data.get("airports", [])
                print(
                    "[Splice Service] Loaded route graph with "
                    f"{len(self.airports)} airport nodes"
                )
            except Exception as exc:
                print(f"[Splice Service] Failed to load route graph: {exc}")
        else:
            print(f"[Splice Service] Model not found: {self.model_path}")

    def _get_db_connection(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3,
            read_timeout=10,
            write_timeout=10,
        )

    def _candidate_midpoints(self, departure, destination):
        midpoints = set()
        for first_leg in self.graph.get(departure, []):
            midpoint = first_leg.get("to")
            if not midpoint or midpoint not in self.graph:
                continue
            if any(leg.get("to") == destination for leg in self.graph[midpoint]):
                midpoints.add(midpoint)
        return sorted(midpoints)

    def _load_candidate_segments(self, departure, destination, date, midpoints):
        route_pairs = [(departure, midpoint) for midpoint in midpoints]
        route_pairs.extend((midpoint, destination) for midpoint in midpoints)
        if not route_pairs:
            return {}

        pair_placeholders = ",".join(["(%s,%s)"] * len(route_pairs))
        sql = f"""
            SELECT market_origin,
                   market_destination,
                   departure_time_raw,
                   departure_time_epoch,
                   arrival_time_raw,
                   arrival_time_epoch,
                   travel_duration_minutes,
                   lowest_price,
                   airline_name,
                   airline_code,
                   equipment_summary,
                   cabin_type,
                   quote_snapshot_id
            FROM ads_route_cabin_lowest_price
            WHERE search_date = %s
              AND flight_date = %s
              AND (market_origin, market_destination) IN ({pair_placeholders})
            ORDER BY market_origin,
                     market_destination,
                     lowest_price,
                     departure_time_epoch,
                     cabin_type,
                     quote_snapshot_id
        """
        params = [self.search_date, date]
        params.extend(value for route_pair in route_pairs for value in route_pair)

        connection = self._get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
        finally:
            connection.close()

        segments_by_route = defaultdict(list)
        for row in rows:
            key = (row["market_origin"].upper(), row["market_destination"].upper())
            segments_by_route[key].append(row)
        return segments_by_route

    @staticmethod
    def _format_duration(minutes):
        minutes = max(0, int(minutes or 0))
        hours, remaining_minutes = divmod(minutes, 60)
        return f"{hours}h{remaining_minutes}m"

    def _build_segment(self, row):
        return {
            "fromAirport": row["market_origin"],
            "toAirport": row["market_destination"],
            "airline": row["airline_name"] or "Unknown airline",
            "airlineCode": row["airline_code"] or "",
            "departureTime": row["departure_time_raw"],
            "arrivalTime": row["arrival_time_raw"],
            "price": float(row["lowest_price"]),
            "duration": self._format_duration(row["travel_duration_minutes"]),
            "aircraftModel": row["equipment_summary"] or "unknown",
        }

    def _best_connection(self, first_segments, second_segments):
        best = None
        best_score = None

        for first in first_segments:
            first_arrival = int(first["arrival_time_epoch"])
            for second in second_segments:
                second_departure = int(second["departure_time_epoch"])
                layover_seconds = second_departure - first_arrival
                if not self.MIN_CONNECTION_SECONDS <= layover_seconds <= self.MAX_CONNECTION_SECONDS:
                    continue

                journey_seconds = int(second["arrival_time_epoch"]) - int(
                    first["departure_time_epoch"]
                )
                if journey_seconds <= 0:
                    continue

                total_price = float(first["lowest_price"]) + float(
                    second["lowest_price"]
                )
                score = (
                    total_price,
                    journey_seconds,
                    int(first["departure_time_epoch"]),
                    first["quote_snapshot_id"],
                    second["quote_snapshot_id"],
                )
                if best_score is None or score < best_score:
                    best_score = score
                    best = (first, second, total_price, journey_seconds)

        return best

    @staticmethod
    def _get_cache_client():
        if not Config.SPLICE_REDIS_ENABLED:
            return None
        try:
            from app import redis_client

            return redis_client
        except ImportError:
            return None

    def get_spliced_routes(self, departure, destination, date, max_stops=2):
        if int(max_stops) < 1:
            return []

        departure = departure.upper()
        destination = destination.upper()
        cache_key = f"splice:{departure}:{destination}:{date}:{max_stops}"
        cache_client = self._get_cache_client()

        if cache_client:
            try:
                cached_data = cache_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as exc:
                print(f"[Splice Cache] Read failed: {exc}")

        midpoints = self._candidate_midpoints(departure, destination)
        segments_by_route = self._load_candidate_segments(
            departure, destination, date, midpoints
        )

        routes = []
        for midpoint in midpoints:
            best = self._best_connection(
                segments_by_route.get((departure, midpoint), []),
                segments_by_route.get((midpoint, destination), []),
            )
            if not best:
                continue

            first, second, total_price, journey_seconds = best
            routes.append(
                {
                    "_journeySeconds": journey_seconds,
                    "legId": (
                        f"spliced_{departure}_{midpoint}_{destination}_{date}_"
                        f"{first['departure_time_epoch']}_{second['departure_time_epoch']}"
                    ),
                    "totalPrice": round(total_price, 2),
                    "totalDuration": self._format_duration(journey_seconds // 60),
                    "stops": 1,
                    "segments": [
                        self._build_segment(first),
                        self._build_segment(second),
                    ],
                }
            )

        routes.sort(
            key=lambda route: (
                route["totalPrice"],
                route["_journeySeconds"],
                route["legId"],
            )
        )
        routes = routes[: self.MAX_RESULTS]
        for route in routes:
            route.pop("_journeySeconds")

        if cache_client and routes:
            try:
                cache_client.setex(
                    cache_key, 1800, json.dumps(routes, ensure_ascii=False)
                )
            except Exception as exc:
                print(f"[Splice Cache] Write failed: {exc}")

        return routes


splice_service = SpliceService()
