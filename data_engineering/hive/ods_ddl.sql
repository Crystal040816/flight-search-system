-- ============================================================
-- ODS 层：原始数据层
-- 说明：字段顺序与源 CSV 完全一致，统一按 STRING 接入。
-- 类型转换、业务校验和异常分流统一在 DWD ETL 中完成。
-- ============================================================

USE flight_db;

-- 1. ODS 航班报价快照
CREATE EXTERNAL TABLE IF NOT EXISTS ods_itineraries (
    legId STRING COMMENT '航程标识，不是报价快照唯一键',
    searchDate STRING COMMENT '搜索日期',
    flightDate STRING COMMENT '出发日期',
    startingAirport STRING COMMENT '搜索起点市场 IATA 代码',
    destinationAirport STRING COMMENT '搜索终点市场 IATA 代码',
    fareBasisCode STRING COMMENT '票价基础代码',
    travelDuration STRING COMMENT 'ISO-8601 全程时长',
    elapsedDays STRING COMMENT '到达相对出发跨日数',
    isBasicEconomy STRING COMMENT '是否基础经济舱',
    isRefundable STRING COMMENT '是否可退',
    isNonStop STRING COMMENT '是否直飞',
    baseFare STRING COMMENT '基础票价',
    totalFare STRING COMMENT '含税总价',
    seatsRemaining STRING COMMENT '剩余座位数',
    totalTravelDistance STRING COMMENT '总距离（英里），可为空',
    segmentsDepartureTimeEpochSeconds STRING COMMENT '各航段出发 Epoch 秒，|| 分隔',
    segmentsDepartureTimeRaw STRING COMMENT '各航段原始出发时间，|| 分隔',
    segmentsArrivalTimeEpochSeconds STRING COMMENT '各航段到达 Epoch 秒，|| 分隔',
    segmentsArrivalTimeRaw STRING COMMENT '各航段原始到达时间，|| 分隔',
    segmentsArrivalAirportCode STRING COMMENT '各航段实际到达机场，|| 分隔',
    segmentsDepartureAirportCode STRING COMMENT '各航段实际出发机场，|| 分隔',
    segmentsAirlineName STRING COMMENT '各航段航司名称，|| 分隔',
    segmentsAirlineCode STRING COMMENT '各航段航司代码，|| 分隔',
    segmentsEquipmentDescription STRING COMMENT '各航段机型，可为空，|| 分隔',
    segmentsDurationInSeconds STRING COMMENT '各航段飞行秒数，|| 分隔',
    segmentsDistance STRING COMMENT '各航段距离（英里），|| 分隔',
    segmentsCabinCode STRING COMMENT '各航段舱位代码，|| 分隔'
)
COMMENT 'ODS层-原始航班报价快照'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\"",
    "escapeChar" = "\\"
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_itineraries'
TBLPROPERTIES ("skip.header.line.count" = "1");

-- 2. ODS 机场
CREATE EXTERNAL TABLE IF NOT EXISTS ods_airports (
    id STRING,
    ident STRING,
    type STRING,
    name STRING,
    latitude_deg STRING,
    longitude_deg STRING,
    elevation_ft STRING,
    continent STRING,
    iso_country STRING,
    iso_region STRING,
    municipality STRING,
    scheduled_service STRING,
    gps_code STRING,
    iata_code STRING,
    local_code STRING,
    home_link STRING,
    wikipedia_link STRING,
    keywords STRING
)
COMMENT 'ODS层-原始机场数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\"",
    "escapeChar" = "\\"
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_airports'
TBLPROPERTIES ("skip.header.line.count" = "1");

-- 3. ODS 跑道
CREATE EXTERNAL TABLE IF NOT EXISTS ods_runways (
    id STRING,
    airport_ref STRING,
    airport_ident STRING,
    length_ft STRING,
    width_ft STRING,
    surface STRING,
    lighted STRING,
    closed STRING,
    le_ident STRING,
    le_latitude_deg STRING,
    le_longitude_deg STRING,
    le_elevation_ft STRING,
    le_heading_degT STRING,
    le_displaced_threshold_ft STRING,
    he_ident STRING,
    he_latitude_deg STRING,
    he_longitude_deg STRING,
    he_elevation_ft STRING,
    he_heading_degT STRING,
    he_displaced_threshold_ft STRING
)
COMMENT 'ODS层-原始跑道数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\"",
    "escapeChar" = "\\"
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_runways'
TBLPROPERTIES ("skip.header.line.count" = "1");

-- 4. ODS 机场频率
CREATE EXTERNAL TABLE IF NOT EXISTS ods_airport_frequencies (
    id STRING,
    airport_ref STRING,
    airport_ident STRING,
    type STRING,
    description STRING,
    frequency_mhz STRING
)
COMMENT 'ODS层-原始机场频率数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\"",
    "escapeChar" = "\\"
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_airport_frequencies'
TBLPROPERTIES ("skip.header.line.count" = "1");

-- 5. ODS 国家
CREATE EXTERNAL TABLE IF NOT EXISTS ods_countries (
    id STRING,
    code STRING,
    name STRING,
    continent STRING,
    wikipedia_link STRING,
    keywords STRING
)
COMMENT 'ODS层-原始国家数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\"",
    "escapeChar" = "\\"
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_countries'
TBLPROPERTIES ("skip.header.line.count" = "1");

-- 6. ODS 区域
CREATE EXTERNAL TABLE IF NOT EXISTS ods_regions (
    id STRING,
    code STRING,
    local_code STRING,
    name STRING,
    continent STRING,
    iso_country STRING,
    wikipedia_link STRING,
    keywords STRING
)
COMMENT 'ODS层-原始区域数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\"",
    "escapeChar" = "\\"
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_regions'
TBLPROPERTIES ("skip.header.line.count" = "1");
