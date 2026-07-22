#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格预测模型训练脚本
使用 XGBoost 训练价格预测模型
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib
import os
import time
import warnings

warnings.filterwarnings('ignore')

from data_loader import load_ods_data


class PricePredictor:
    """价格预测器"""

    def __init__(self):
        self.model = None
        self.encoders = {}
        self.features = []
        self.model_dir = "/home/hadoop/flight-search-system/algorithm/models"

    def create_features(self, df):
        """创建特征"""
        df = df.copy()

        # 日期特征
        df['search_date'] = pd.to_datetime(df['searchdate'])
        df['flight_date'] = pd.to_datetime(df['flightdate'])
        df['days_to_departure'] = (df['flight_date'] - df['search_date']).dt.days
        df['days_to_departure'] = df['days_to_departure'].clip(0, 365)
        df['flight_month'] = df['flight_date'].dt.month
        df['flight_dayofweek'] = df['flight_date'].dt.dayofweek
        df['is_weekend'] = df['flight_dayofweek'].isin([5, 6]).astype(int)
        df['is_summer'] = df['flight_month'].isin([6, 7, 8]).astype(int)
        df['is_holiday'] = df['flight_month'].isin([7, 8, 12]).astype(int)

        # 航段特征
        df['segment_count'] = df['segmentsairlinecode'].str.split('||').str.len()
        df['stop_count'] = df['segment_count'] - 1
        df['stop_count'] = df['stop_count'].clip(0, 3)
        df['seatsremaining'] = pd.to_numeric(df['seatsremaining'], errors='coerce')
        df['totalfare'] = pd.to_numeric(df['totalfare'], errors='coerce')

        # 距离特征
        df['distance'] = pd.to_numeric(df['totaltraveldistance'], errors='coerce').fillna(500)

        # 时长特征
        def parse_duration(val):
            if pd.isna(val):
                return 0
            parts = str(val).split('||')
            total = 0
            for p in parts:
                try:
                    total += int(p)
                except:
                    pass
            return total / 3600

        df['duration_hours'] = df['segmentsdurationinseconds'].apply(parse_duration)

        # 交叉特征
        df['price_per_stop'] = df['totalfare'] / (df['stop_count'] + 1)
        df['duration_per_stop'] = df['duration_hours'] / (df['stop_count'] + 1)
        df['price_per_hour'] = df['totalfare'] / (df['duration_hours'] + 0.1)
        df['price_per_mile'] = df['totalfare'] / (df['distance'] + 0.1)

        # 航司评分
        airline_rank = {
            'DL': 0.9, 'AA': 0.85, 'UA': 0.85, 'B6': 0.75,
            'WN': 0.80, 'NK': 0.60, 'F9': 0.55, 'AS': 0.85
        }

        def get_airline_score(code):
            if pd.isna(code):
                return 0.5
            first = str(code).split('||')[0] if '||' in str(code) else str(code)
            return airline_rank.get(first, 0.5)

        df['airline_score'] = df['segmentsairlinecode'].apply(get_airline_score)

        return df

    def train(self, df, test_size=0.2):
        """训练模型"""
        print("=" * 60)
        print("价格预测模型训练")
        print("=" * 60)

        # 特征工程
        print("\n[1/5] 特征工程...")
        df = self.create_features(df)

        # 定义特征
        self.features = [
            'days_to_departure', 'flight_month', 'flight_dayofweek', 'is_weekend',
            'is_summer', 'is_holiday', 'segment_count', 'stop_count',
            'seatsremaining', 'distance', 'duration_hours', 'airline_score',
            'price_per_stop', 'duration_per_stop', 'price_per_hour', 'price_per_mile'
        ]

        # 编码分类变量
        categorical = ['startingairport', 'destinationairport']
        for col in categorical:
            le = LabelEncoder()
            df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
            self.encoders[col] = le
            self.features.append(col + '_encoded')

        # 清理数据
        df = df.dropna(subset=self.features + ['totalfare'])
        df = df[df['totalfare'] > 0]
        df = df[df['totalfare'] < 3000]

        # IQR 去除异常值
        Q1 = df['totalfare'].quantile(0.25)
        Q3 = df['totalfare'].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df = df[(df['totalfare'] >= lower) & (df['totalfare'] <= upper)]

        print(f"✅ 清洗后数据: {len(df)} 条")

        # 准备数据
        print("\n[2/5] 准备训练数据...")
        X = df[self.features]
        y = df['totalfare']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        print(f"✅ 训练集: {len(X_train)} 条")
        print(f"✅ 测试集: {len(X_test)} 条")

        # 训练模型
        print("\n[3/5] 训练 XGBoost 模型...")
        self.model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            random_state=42,
            verbosity=0,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)

        # 评估
        print("\n[4/5] 评估模型...")
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        print(f"\n📊 模型评估结果:")
        print(f"  MAE:  {mae:.2f} USD")
        print(f"  RMSE: {rmse:.2f} USD")
        print(f"  R²:   {r2:.4f}")

        # 特征重要性
        importance = pd.DataFrame({
            'feature': self.features,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print(f"\n📊 特征重要性 Top 10:")
        print(importance.head(10))

        # 保存模型
        print("\n[5/5] 保存模型...")
        os.makedirs(self.model_dir, exist_ok=True)
        joblib.dump(self.model, f"{self.model_dir}/price_predict_model.pkl")
        joblib.dump(self.encoders, f"{self.model_dir}/encoders.pkl")
        print(f"✅ 模型已保存到: {self.model_dir}")

        return {'mae': mae, 'rmse': rmse, 'r2': r2}

    def predict(self, features_dict):
        """预测价格"""
        if self.model is None:
            print("模型未加载，请先训练")
            return None
        df = pd.DataFrame([features_dict])
        return float(self.model.predict(df[self.features])[0])


if __name__ == "__main__":
    # 加载数据
    print("加载数据...")
    df = load_ods_data(100000)
    print(f"✅ 加载了 {len(df)} 条数据")

    # 训练
    predictor = PricePredictor()
    results = predictor.train(df)
    print("\n🎉 训练完成！")