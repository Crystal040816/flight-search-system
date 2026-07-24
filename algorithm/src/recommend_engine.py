#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能推荐引擎
多因素综合评分推荐航班
"""
import pandas as pd
import numpy as np
import joblib
import os


class RecommendEngine:
    """智能推荐引擎"""

    def __init__(self, weights=None):
        self.weights = weights or {
            'price': 0.30,
            'stops': 0.25,
            'seats': 0.15,
            'airline': 0.15,
            'direct': 0.10,
            'duration': 0.05
        }
        self.airline_scores = {
            'DL': 0.9, 'AA': 0.85, 'UA': 0.85,
            'B6': 0.75, 'WN': 0.80, 'NK': 0.60,
            'F9': 0.55, 'AS': 0.85, 'HA': 0.80
        }

    def normalize(self, series):
        """归一化"""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series([0.5] * len(series))
        return (series - min_val) / (max_val - min_val)

    def get_airline_score(self, airline_code):
        """获取航司评分"""
        if pd.isna(airline_code):
            return 0.5
        first = str(airline_code).split('||')[0] if '||' in str(airline_code) else str(airline_code)
        return self.airline_scores.get(first, 0.5)

    def score_flights(self, df):
        """
        计算航班综合得分
        df 必须包含: totalfare, stop_count, seatsremaining,
                    segmentsairlinecode, duration_hours
        """
        df = df.copy()

        # 价格得分 (越低越好)
        df['price_score'] = 1 - self.normalize(df['totalfare'])

        # 中转得分 (越少越好)
        df['stops_score'] = 1 / (df['stop_count'] + 1)

        # 座位得分 (越多越好)
        df['seats_score'] = self.normalize(df['seatsremaining'])

        # 直飞得分
        df['direct_score'] = (df['stop_count'] == 0).astype(float)

        # 航司得分
        df['airline_score'] = df['segmentsairlinecode'].apply(self.get_airline_score)

        # 时长得分 (越短越好)
        if 'duration_hours' in df.columns:
            df['duration_score'] = 1 - self.normalize(df['duration_hours'])
        else:
            df['duration_score'] = 0.5

        # 综合得分
        df['total_score'] = (
                df['price_score'] * self.weights['price'] +
                df['stops_score'] * self.weights['stops'] +
                df['seats_score'] * self.weights['seats'] +
                df['airline_score'] * self.weights['airline'] +
                df['direct_score'] * self.weights['direct'] +
                df['duration_score'] * self.weights['duration']
        )

        return df

    def recommend(self, df, top_n=10, min_score=0):
        """推荐 Top N 航班"""
        scored = self.score_flights(df)
        result = scored[scored['total_score'] >= min_score].nlargest(top_n, 'total_score')
        return result

    def explain_recommendation(self, flight):
        """解释推荐理由"""
        reasons = []
        if flight.get('price_score', 0) > 0.7:
            reasons.append("价格优惠")
        if flight.get('stops_score', 0) > 0.7:
            reasons.append("中转少")
        if flight.get('direct_score', 0) == 1:
            reasons.append("直飞航班")
        if flight.get('airline_score', 0) > 0.8:
            reasons.append("优质航司")
        if flight.get('seats_score', 0) > 0.7:
            reasons.append("座位充足")
        if flight.get('duration_score', 0) > 0.7:
            reasons.append("飞行时间短")
        return reasons if reasons else ["综合推荐"]

    def save(self, filepath):
        """保存配置"""
        config = {
            'weights': self.weights,
            'airline_scores': self.airline_scores
        }
        joblib.dump(config, filepath)
        print(f"✅ 推荐配置已保存: {filepath}")

    def load(self, filepath):
        """加载配置"""
        config = joblib.load(filepath)
        self.weights = config.get('weights', self.weights)
        self.airline_scores = config.get('airline_scores', self.airline_scores)


if __name__ == "__main__":
    # 测试
    engine = RecommendEngine()
    print("推荐引擎已创建")
    print(f"权重配置: {engine.weights}")

    # 模拟数据测试
    test_df = pd.DataFrame({
        'legid': ['A', 'B', 'C', 'D', 'E'],
        'totalfare': [300, 250, 400, 350, 200],
        'stop_count': [0, 1, 0, 2, 1],
        'seatsremaining': [10, 5, 20, 15, 8],
        'segmentsairlinecode': ['DL', 'AA', 'UA', 'B6', 'NK'],
        'duration_hours': [2.5, 3.0, 2.0, 4.0, 2.8]
    })

    result = engine.recommend(test_df, top_n=3)
    print("\n测试推荐结果:")
    print(result[['legid', 'totalfare', 'total_score']])