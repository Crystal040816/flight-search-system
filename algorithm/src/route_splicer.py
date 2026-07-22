#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能拼接引擎
多段航班组合搜索
"""
from collections import defaultdict
import pandas as pd
import numpy as np
import joblib
import os


class RouteSplicer:
    """智能拼接引擎"""

    def __init__(self, segments_df=None):
        self.graph = defaultdict(list)
        self.airports = set()
        if segments_df is not None:
            self.build_graph(segments_df)

    def build_graph(self, segments_df):
        """构建航线图"""
        print("构建航线图...")
        self.graph = defaultdict(list)
        self.airports = set()

        for _, row in segments_df.iterrows():
            dep = str(row.get('departure_airport_code', ''))
            arr = str(row.get('arrival_airport_code', ''))

            if dep and arr and dep != 'nan' and arr != 'nan':
                self.graph[dep].append({
                    'to': arr,
                    'airline': row.get('airline_name', ''),
                    'airline_code': row.get('airline_code', ''),
                    'duration': int(row.get('duration_seconds', 0)) // 60,
                    'distance': int(row.get('distance_miles', 0))
                })
                self.airports.add(dep)
                self.airports.add(arr)

        # 去重（保留最短时长）
        for airport in self.graph:
            unique_routes = {}
            for r in self.graph[airport]:
                key = r['to']
                if key not in unique_routes or r['duration'] < unique_routes[key]['duration']:
                    unique_routes[key] = r
            self.graph[airport] = list(unique_routes.values())

        print(f"✅ 航线图构建完成: {len(self.airports)} 个机场, {sum(len(v) for v in self.graph.values())} 条航线")

    def find_routes(self, origin, destination, max_stops=2):
        """
        搜索拼接路线
        """
        results = []
        queue = [(origin, [origin], 0, 0, [])]  # (current, path, total_duration, total_price, segments)

        while queue:
            airport, path, total_duration, total_price, segments = queue.pop(0)

            if len(path) - 1 > max_stops:
                continue

            if airport == destination and len(path) > 1:
                results.append({
                    'path': ' → '.join(path),
                    'stops': len(path) - 2,
                    'total_duration': total_duration,
                    'total_price': total_price,
                    'segments': segments
                })
                continue

            for seg in self.graph.get(airport, []):
                if seg['to'] not in path:
                    new_path = path + [seg['to']]
                    new_segments = segments + [seg]
                    # 简单价格估算
                    est_price = seg.get('duration', 60) * 0.08
                    queue.append((
                        seg['to'],
                        new_path,
                        total_duration + seg.get('duration', 60),
                        total_price + est_price,
                        new_segments
                    ))

        # 按价格排序
        return sorted(results, key=lambda x: x['total_price'])[:10]

    def find_cheapest(self, origin, destination, max_stops=2):
        """找最便宜的路线"""
        routes = self.find_routes(origin, destination, max_stops)
        return sorted(routes, key=lambda x: x['total_price'])

    def find_shortest(self, origin, destination, max_stops=2):
        """找最短的路线"""
        routes = self.find_routes(origin, destination, max_stops)
        return sorted(routes, key=lambda x: x['total_duration'])

    def get_airports(self):
        """获取所有机场列表"""
        return list(self.airports)

    def get_routes_from(self, airport):
        """获取从某机场出发的航线"""
        return self.graph.get(airport, [])

    def save(self, filepath):
        """保存拼接模型"""
        config = {
            'route_graph': dict(self.graph),
            'airports': list(self.airports)
        }
        joblib.dump(config, filepath)
        print(f"✅ 拼接模型已保存: {filepath}")

    def load(self, filepath):
        """加载拼接模型"""
        config = joblib.load(filepath)
        self.graph = defaultdict(list, config.get('route_graph', {}))
        self.airports = set(config.get('airports', []))


if __name__ == "__main__":
    # 测试
    test_segments = pd.DataFrame({
        'departure_airport_code': ['ATL', 'ATL', 'JFK', 'JFK', 'ORD'],
        'arrival_airport_code': ['JFK', 'ORD', 'BOS', 'ORD', 'BOS'],
        'airline_name': ['Delta', 'American', 'Delta', 'United', 'American'],
        'airline_code': ['DL', 'AA', 'DL', 'UA', 'AA'],
        'duration_seconds': [7200, 5400, 3600, 4800, 4200],
        'distance_miles': [800, 600, 200, 700, 500]
    })

    splicer = RouteSplicer(test_segments)
    routes = splicer.find_routes('ATL', 'BOS', max_stops=2)
    print(f"\n找到 {len(routes)} 条路线:")
    for r in routes:
        print(f"  {r['path']} | 时长: {r['total_duration']}分钟 | 价格: ${r['total_price']:.0f}")