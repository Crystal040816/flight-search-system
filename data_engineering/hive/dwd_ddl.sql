-- ============================================================
-- DWD 层：明细数据层
-- 说明：数据清洗、类型转换、拆解分段数据
-- ============================================================

USE flight_db;

-- 1. DWD 航班行程明细表
CREATE TABLE IF NOT EXISTS dwd_flight_itinerary (
    leg_id STRING COMMENT '航班段ID',
    search_date DATE COMMENT '搜索日期',
    flight_date DATE COMMENT '航班日期',
    starting_airport STRING COMMENT '出发机场IATA',
    destination_airport STRING COMMENT '到达机场IATA',
    airline_code STRING COMMENT '航司代码(第一段)',
    airline_name STRING COMMENT '航司名称(第一段)',
    total_fare DOUBLE COMMENT '含税总价(USD)',
    base_fare DOUBLE COMMENT '基础票价(USD)',
    seats_remaining INT COMMENT '剩余座位数',
    is_non_stop BOOLEAN COMMENT '是否直飞',
    is_refundable BOOLEAN COMMENT '是否可退票',
    is_basic_economy BOOLEAN COMMENT '是否基础经济舱',
    travel_duration INT COMMENT '旅行时长(秒)',
    total_distance INT COMMENT '总飞行距离(英里)',
    segments_count INT COMMENT '航段数量',
    cabin_code STRING COMMENT '舱位代码(第一段)'
)
COMMENT 'DWD层-航班行程明细'
PARTITIONED BY (dt STRING COMMENT '航班日期分区')
STORED AS PARQUET;

-- 2. DWD 航段明细表（拆解 || 分隔的分段数据）
CREATE TABLE IF NOT EXISTS dwd_flight_segments (
    leg_id STRING COMMENT '航班段ID',
    segment_index INT COMMENT '航段序号(从0开始)',
    departure_airport_code STRING COMMENT '出发机场IATA',
    arrival_airport_code STRING COMMENT '到达机场IATA',
    departure_time_raw STRING COMMENT '出发时间(原始格式)',
    arrival_time_raw STRING COMMENT '到达时间(原始格式)',
    departure_time_epoch BIGINT COMMENT '出发时间(Unix时间戳)',
    arrival_time_epoch BIGINT COMMENT '到达时间(Unix时间戳)',
    airline_code STRING COMMENT '航司代码',
    airline_name STRING COMMENT '航司名称',
    equipment_description STRING COMMENT '机型描述',
    duration_seconds INT COMMENT '飞行秒数',
    distance_miles INT COMMENT '距离(英里)',
    cabin_code STRING COMMENT '舱位代码'
)
COMMENT 'DWD层-航段明细数据'
PARTITIONED BY (dt STRING COMMENT '航班日期分区')
STORED AS PARQUET;

-- 3. DWD 航线基础信息表
CREATE TABLE IF NOT EXISTS dwd_route_info (
    route_id STRING COMMENT '航线ID(起始机场+到达机场)',
    starting_airport STRING COMMENT '出发机场IATA',
    destination_airport STRING COMMENT '到达机场IATA',
    avg_distance INT COMMENT '平均距离',
    avg_duration INT COMMENT '平均飞行时长'
)
COMMENT 'DWD层-航线基础信息'
STORED AS PARQUET;
