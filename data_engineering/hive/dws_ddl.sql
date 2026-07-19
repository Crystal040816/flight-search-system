-- ============================================================
-- DWS 层：按搜索日期汇总报价供给
-- 注意：源数据是搜索报价快照，不代表实际执行航班或成交订单。
-- ============================================================

USE flight_db;

-- 1. 市场航线日度报价统计
CREATE TABLE IF NOT EXISTS dws_route_daily_stats (
    route_id STRING,
    market_origin STRING,
    market_destination STRING,
    quote_count BIGINT COMMENT '报价快照数量',
    distinct_leg_count BIGINT COMMENT '不同 leg_id 数量',
    avg_price DECIMAL(12,2),
    min_price DECIMAL(12,2),
    max_price DECIMAL(12,2),
    avg_seats DECIMAL(12,2),
    avg_duration_minutes DECIMAL(12,2),
    nonstop_quote_count BIGINT,
    nonstop_quote_rate DECIMAL(9,6),
    etl_time TIMESTAMP
)
COMMENT 'DWS层-市场航线日度报价统计'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 2. 航司日度报价供给统计
CREATE TABLE IF NOT EXISTS dws_airline_stats (
    airline_code STRING,
    airline_name STRING,
    quote_count BIGINT COMMENT '以第一航段航司归属的报价数',
    distinct_leg_count BIGINT,
    avg_price DECIMAL(12,2),
    min_price DECIMAL(12,2),
    max_price DECIMAL(12,2),
    offer_share_pct DECIMAL(9,6) COMMENT '当日报价供给占比，不是销售市场份额',
    etl_time TIMESTAMP
)
COMMENT 'DWS层-航司日度报价供给统计'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 3. 市场机场日度报价统计
CREATE TABLE IF NOT EXISTS dws_airport_stats (
    market_airport_code STRING COMMENT '用户搜索使用的市场机场代码',
    origin_quote_count BIGINT,
    destination_quote_count BIGINT,
    avg_origin_price DECIMAL(12,2),
    avg_destination_price DECIMAL(12,2),
    etl_time TIMESTAMP
)
COMMENT 'DWS层-市场机场日度报价统计'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 4. 航线基础统计
CREATE TABLE IF NOT EXISTS dws_route_profile (
    route_id STRING,
    market_origin STRING,
    market_destination STRING,
    avg_distance_miles DECIMAL(12,2),
    avg_duration_minutes DECIMAL(12,2),
    first_seen_date DATE,
    last_seen_date DATE,
    etl_time TIMESTAMP
)
COMMENT 'DWS层-市场航线基础统计'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');
