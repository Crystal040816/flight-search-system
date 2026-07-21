# backend/app/models/request.py
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date


@dataclass
class SearchRequest:
    """搜索请求"""
    departure: str                          # 出发地 IATA 三字码
    destination: str                        # 目的地 IATA 三字码
    flightDate: str                         # 出发日期 YYYY-MM-DD
    tripType: str = "ONE_WAY"               # ONE_WAY / ROUND_TRIP / MULTI_CITY
    returnDate: Optional[str] = None        # 返程日期（往返时必填）
    page: int = 1                           # 页码
    size: int = 20                          # 每页数量
    sortBy: str = "price"                   # price / duration / departureTime
    airlines: Optional[List[str]] = None    # 航空公司过滤
    maxStops: Optional[int] = None          # 最大中转次数
    minPrice: Optional[float] = None        # 最低价格
    maxPrice: Optional[float] = None        # 最高价格


@dataclass
class PredictRequest:
    """价格预测请求"""
    departure: str
    destination: str
    flightDate: str


@dataclass
class RecommendRequest:
    """智能推荐请求"""
    departure: str
    destination: str
    flightDate: str
    preferences: Optional[dict] = None


@dataclass
class SpliceRequest:
    """智能拼接请求"""
    departure: str
    destination: str
    date: str
    maxStops: int = 2


@dataclass
class DestinationsRequest:
    """飞去哪请求"""
    departure: str
    date: str