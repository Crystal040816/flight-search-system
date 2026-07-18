-- ============================================================
-- ODS 层：原始数据层
-- 说明：与 CSV 字段完全一致，不做任何处理
-- ============================================================

USE flight_db;

-- 1. ODS 航班行程数据
CREATE EXTERNAL TABLE IF NOT EXISTS ods_itineraries (
    legId STRING COMMENT '航班段ID',
    searchDate STRING COMMENT '搜索日期',
    flightDate STRING COMMENT '航班日期',
    startingAirport STRING COMMENT '出发机场IATA',
    destinationAirport STRING COMMENT '到达机场IATA',
    fareBasisCode STRING COMMENT '舱位代码',
    travelDuration STRING COMMENT '旅行时长(时:分)',
    elapsedDays INT COMMENT '跨越天数',
    isBasicEconomy BOOLEAN COMMENT '是否基础经济舱',
    isRefundable BOOLEAN COMMENT '是否可退票',
    isNonStop BOOLEAN COMMENT '是否直飞',
    baseFare DOUBLE COMMENT '基础票价(USD)',
    totalFare DOUBLE COMMENT '含税总价(USD)',
    seatsRemaining INT COMMENT '剩余座位数',
    totalTravelDistance INT COMMENT '总飞行距离(英里)',
    segmentsDepartureTimeEpochSeconds STRING COMMENT '分段出发时间(Unix时间戳)',
    segmentsDepartureTimeRaw STRING COMMENT '分段出发时间(原始格式)',
    segmentsArrivalTimeEpochSeconds STRING COMMENT '分段到达时间(Unix时间戳)',
    segmentsArrivalTimeRaw STRING COMMENT '分段到达时间(原始格式)',
    segmentsArrivalAirportCode STRING COMMENT '分段到达机场IATA',
    segmentsDepartureAirportCode STRING COMMENT '分段出发机场IATA',
    segmentsAirlineName STRING COMMENT '分段航司名称',
    segmentsAirlineCode STRING COMMENT '分段航司代码',
    segmentsEquipmentDescription STRING COMMENT '分段机型描述',
    segmentsDurationInSeconds STRING COMMENT '分段飞行秒数',
    segmentsDistance STRING COMMENT '分段距离(英里)',
    segmentsCabinCode STRING COMMENT '分段舱位代码'
)
COMMENT 'ODS层-原始航班行程数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\"",
    "escapeChar" = "\\"
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_itineraries'
TBLPROPERTIES ("skip.header.line.count"="1");

-- 2. ODS 机场数据
CREATE EXTERNAL TABLE IF NOT EXISTS ods_airports (
    airport_id STRING COMMENT '机场ID',
    name STRING COMMENT '机场名称',
    city STRING COMMENT '所在城市',
    country STRING COMMENT '所在国家',
    iata_code STRING COMMENT 'IATA三字码',
    icao_code STRING COMMENT 'ICAO四字码',
    latitude DOUBLE COMMENT '纬度',
    longitude DOUBLE COMMENT '经度',
    altitude INT COMMENT '海拔',
    timezone INT COMMENT '时区',
    dst STRING COMMENT '夏令时',
    tz_database STRING COMMENT '时区数据库'
)
COMMENT 'ODS层-原始机场数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_airports'
TBLPROPERTIES ("skip.header.line.count"="1");

-- 3. ODS 国家数据
CREATE EXTERNAL TABLE IF NOT EXISTS ods_countries (
    country_code STRING COMMENT '国家代码',
    country_name STRING COMMENT '国家名称'
)
COMMENT 'ODS层-原始国家数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_countries'
TBLPROPERTIES ("skip.header.line.count"="1");

-- 4. ODS 区域数据
CREATE EXTERNAL TABLE IF NOT EXISTS ods_regions (
    region_id STRING COMMENT '区域ID',
    region_name STRING COMMENT '区域名称'
)
COMMENT 'ODS层-原始区域数据'
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = "\""
)
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/flight_db/ods_regions'
TBLPROPERTIES ("skip.header.line.count"="1");
