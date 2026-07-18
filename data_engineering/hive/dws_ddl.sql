-- ============================================================
-- DWS 层：汇总数据层
-- 说明：按主题进行轻度汇总
-- ============================================================

USE flight_db;

-- 1. DWS 航线日度统计
CREATE TABLE IF NOT EXISTS dws_route_daily_stats (
    route_id STRING COMMENT '航线ID',
    starting_airport STRING COMMENT '出发机场',
    destination_airport STRING COMMENT '到达机场',
    stat_date DATE COMMENT '统计日期',
    flight_count INT COMMENT '航班数量',
    avg_price DOUBLE COMMENT '平均价格',
    min_price DOUBLE COMMENT '最低价格',
    max_price DOUBLE COMMENT '最高价格',
    avg_seats DOUBLE COMMENT '平均剩余座位',
    avg_duration INT COMMENT '平均飞行时长'
)
COMMENT 'DWS层-航线日度统计'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS PARQUET;

-- 2. DWS 航司统计
CREATE TABLE IF NOT EXISTS dws_airline_stats (
    airline_code STRING COMMENT '航司代码',
    airline_name STRING COMMENT '航司名称',
    stat_date DATE COMMENT '统计日期',
    flight_count INT COMMENT '航班数量',
    avg_price DOUBLE COMMENT '平均票价',
    min_price DOUBLE COMMENT '最低票价',
    max_price DOUBLE COMMENT '最高票价',
    total_revenue DOUBLE COMMENT '总收入'
)
COMMENT 'DWS层-航司统计'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS PARQUET;

-- 3. DWS 机场统计
CREATE TABLE IF NOT EXISTS dws_airport_stats (
    airport_code STRING COMMENT '机场代码',
    stat_date DATE COMMENT '统计日期',
    departure_count INT COMMENT '出发航班数',
    arrival_count INT COMMENT '到达航班数',
    avg_price_departure DOUBLE COMMENT '出发平均票价',
    avg_price_arrival DOUBLE COMMENT '到达平均票价'
)
COMMENT 'DWS层-机场统计'
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS PARQUET;
