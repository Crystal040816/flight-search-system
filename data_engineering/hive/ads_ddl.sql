-- ============================================================
-- ADS 层：面向应用的报价与供给指标
-- 注意：所有排名和份额均基于搜索报价快照，不代表销量或客流。
-- ============================================================

USE flight_db;

-- 1. 指定搜索日、出发日和市场航线的最低报价
CREATE TABLE IF NOT EXISTS ads_route_lowest_price (
    market_origin STRING,
    market_destination STRING,
    destination_city STRING,
    destination_country_code STRING,
    destination_country_name STRING,
    flight_date DATE,
    lowest_price DECIMAL(12,2),
    avg_price DECIMAL(12,2),
    quote_snapshot_id STRING COMMENT '最低价对应的报价快照',
    airline_code STRING,
    airline_name STRING,
    currency STRING,
    etl_time TIMESTAMP
)
COMMENT 'ADS层-市场航线最低报价'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 2. 航线报价供给排行
CREATE TABLE IF NOT EXISTS ads_route_offer_rank (
    rank_num INT,
    route_id STRING,
    market_origin STRING,
    market_destination STRING,
    quote_count BIGINT,
    distinct_leg_count BIGINT,
    avg_price DECIMAL(12,2),
    previous_day_avg_price DECIMAL(12,2),
    price_change_pct DECIMAL(9,4) COMMENT '相对前一搜索日平均价的变化百分比',
    etl_time TIMESTAMP
)
COMMENT 'ADS层-航线报价供给排行，不代表真实客流热度'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 3. 航司报价供给占比
CREATE TABLE IF NOT EXISTS ads_airline_offer_share (
    airline_code STRING,
    airline_name STRING,
    quote_count BIGINT,
    offer_share_pct DECIMAL(9,6),
    avg_price DECIMAL(12,2),
    etl_time TIMESTAMP
)
COMMENT 'ADS层-航司报价供给占比，不代表销售市场份额'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');
