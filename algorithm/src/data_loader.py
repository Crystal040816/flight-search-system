#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载模块
从 Hive 加载数据供算法使用
"""
import pandas as pd
import os
from pyhive import hive


def get_hive_connection():
    """获取 Hive 连接"""
    return hive.Connection(
        host='localhost',
        port=10000,
        username='hadoop',
        database='flight_db'
    )


def load_itinerary_data(limit=None):
    """
    从 DWD 加载行程数据
    """
    conn = get_hive_connection()
    sql = "SELECT * FROM dwd_flight_itinerary"
    if limit:
        sql += f" LIMIT {limit}"
    return pd.read_sql(sql, conn)


def load_segments_data(limit=None):
    """
    从 DWD 加载航段数据
    """
    conn = get_hive_connection()
    sql = "SELECT * FROM dwd_flight_segments"
    if limit:
        sql += f" LIMIT {limit}"
    return pd.read_sql(sql, conn)


def load_ods_data(limit=None):
    """
    从 ODS 加载原始数据（CSV 格式，稳定读取）
    """
    conn = get_hive_connection()
    sql = """
    SELECT 
        legId,
        searchDate,
        flightDate,
        startingAirport,
        destinationAirport,
        CAST(totalFare AS DOUBLE) as totalFare,
        CAST(seatsRemaining AS INT) as seatsRemaining,
        segmentsAirlineCode,
        segmentsDurationInSeconds,
        totalTravelDistance
    FROM ods_itineraries
    WHERE totalFare IS NOT NULL 
      AND CAST(totalFare AS DOUBLE) > 0
    """
    if limit:
        sql += f" LIMIT {limit}"
    df = pd.read_sql(sql, conn)
    df.columns = df.columns.str.lower()
    return df


def load_from_csv(file_path):
    """
    从本地 CSV 加载数据
    """
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None


def save_to_csv(df, file_path):
    """
    保存数据到本地 CSV
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    print(f"✅ 数据已保存到: {file_path}")


if __name__ == "__main__":
    print("测试数据加载...")
    df = load_ods_data(1000)
    print(f"加载了 {len(df)} 条数据")
    print(df.columns.tolist())