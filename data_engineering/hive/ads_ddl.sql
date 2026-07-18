-- ============================================================
-- ADS 层：应用数据层
-- 说明：面向具体业务场景的汇总数据
-- ============================================================

USE flight_db;

-- 1. ADS 航线最低价（飞去哪功能）
CREATE TABLE IF NOT EXISTS ads_route_lowest_price (
    starting_airport STRING COMMENT '出发机场IATA',
    destination_airport STRING COMMENT '到达机场IATA',
    destination_city STRING COMMENT '目的地城市',
    country STRING COMMENT '国家',
    lowest_price DOUBLE COMMENT '最低价格',
    avg_price DOUBLE COMMENT '平均价格',
    flight_date DATE COMMENT '航班日期',
    airline_code STRING COMMENT '最低价航司',
    airline_name STRING COMMENT '最低价航司名称'
)
COMMENT 'ADS层-航线最低价'
STORED AS PARQUET;

-- 2. ADS 热门航线排行
CREATE TABLE IF NOT EXISTS ads_hot_routes (
    rank_num INT COMMENT '排名',
    starting_airport STRING COMMENT '出发机场',
    destination_airport STRING COMMENT '到达机场',
    flight_count INT COMMENT '航班总数',
    avg_price DOUBLE COMMENT '平均价格',
    price_change_pct DOUBLE COMMENT '价格变化百分比'
)
COMMENT 'ADS层-热门航线排行'
STORED AS PARQUET;

-- 3. ADS 航司市场份额
CREATE TABLE IF NOT EXISTS ads_airline_market_share (
    airline_code STRING COMMENT '航司代码',
    airline_name STRING COMMENT '航司名称',
    flight_count INT COMMENT '航班数量',
    market_share DECIMAL(5,2) COMMENT '市场份额(%)',
    avg_price DOUBLE COMMENT '平均票价'
)
COMMENT 'ADS层-航司市场份额'
STORED AS PARQUET;
