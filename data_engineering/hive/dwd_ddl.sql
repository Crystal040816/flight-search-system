-- ============================================================
-- DWD 层：清洗后的明细数据
-- 说明：一条行程记录代表一次搜索日期下的报价快照。
-- quote_snapshot_id 由 ETL 对最终确认的业务键做稳定哈希生成。
-- ============================================================

USE flight_db;

-- 1. 报价快照（一条有效原始报价一行）
CREATE TABLE IF NOT EXISTS dwd_flight_itinerary (
    quote_snapshot_id STRING COMMENT '报价快照稳定唯一标识',
    leg_id STRING COMMENT '航程标识，不单独作为唯一键',
    flight_date DATE COMMENT '出发日期',
    market_origin STRING COMMENT '搜索起点市场 IATA 代码',
    market_destination STRING COMMENT '搜索终点市场 IATA 代码',
    fare_basis_code STRING COMMENT '票价基础代码',
    first_airline_code STRING COMMENT '第一航段航司代码',
    first_airline_name STRING COMMENT '第一航段航司名称',
    travel_duration_minutes INT COMMENT '全程时长（分钟）',
    elapsed_days INT COMMENT '到达相对出发跨日数',
    is_basic_economy BOOLEAN COMMENT '是否基础经济舱',
    is_refundable BOOLEAN COMMENT '是否可退',
    is_non_stop BOOLEAN COMMENT '是否直飞',
    base_fare DECIMAL(12,2) COMMENT '基础票价（USD）',
    total_fare DECIMAL(12,2) COMMENT '含税总价（USD）',
    currency STRING COMMENT '币种，当前数据源为 USD',
    seats_remaining INT COMMENT '剩余座位数',
    total_distance_miles INT COMMENT '总距离（英里），可为空',
    segment_count INT COMMENT '航段数量',
    stop_count INT COMMENT '中转次数',
    actual_airport_path STRING COMMENT '实际航段机场路径',
    source_file STRING COMMENT '来源文件',
    etl_time TIMESTAMP COMMENT 'ETL 处理时间'
)
COMMENT 'DWD层-航班报价快照明细'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 2. 航段明细（一条报价快照中的一个实际航段一行）
CREATE TABLE IF NOT EXISTS dwd_flight_segments (
    quote_snapshot_id STRING COMMENT '关联报价快照标识',
    leg_id STRING COMMENT '航程标识',
    flight_date DATE COMMENT '行程出发日期',
    segment_index INT COMMENT '航段序号（从 0 开始）',
    departure_airport_code STRING COMMENT '实际出发机场 IATA 代码',
    arrival_airport_code STRING COMMENT '实际到达机场 IATA 代码',
    departure_time_raw STRING COMMENT '带时区的原始出发时间',
    arrival_time_raw STRING COMMENT '带时区的原始到达时间',
    departure_time_epoch BIGINT COMMENT '出发 Epoch 秒',
    arrival_time_epoch BIGINT COMMENT '到达 Epoch 秒',
    airline_code STRING COMMENT '航司代码',
    airline_name STRING COMMENT '航司名称',
    equipment_description STRING COMMENT '机型描述，可为空',
    duration_seconds INT COMMENT '实际飞行秒数',
    distance_miles INT COMMENT '航段距离（英里）',
    cabin_code STRING COMMENT '舱位代码',
    connection_wait_minutes INT COMMENT '到下一航段的等待分钟数，末段为空',
    source_file STRING COMMENT '来源文件',
    etl_time TIMESTAMP COMMENT 'ETL 处理时间'
)
COMMENT 'DWD层-报价快照航段明细'
PARTITIONED BY (search_date DATE COMMENT '搜索日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 3. 机场维表
CREATE TABLE IF NOT EXISTS dim_airport (
    airport_id BIGINT,
    ident STRING,
    airport_type STRING,
    airport_name STRING,
    latitude_deg DOUBLE,
    longitude_deg DOUBLE,
    elevation_ft INT,
    continent STRING,
    iso_country STRING,
    iso_region STRING,
    municipality STRING,
    scheduled_service BOOLEAN,
    gps_code STRING,
    iata_code STRING,
    local_code STRING,
    home_link STRING,
    wikipedia_link STRING,
    keywords STRING,
    etl_time TIMESTAMP
)
COMMENT '机场维表'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 4. 国家维表
CREATE TABLE IF NOT EXISTS dim_country (
    country_id BIGINT,
    country_code STRING,
    country_name STRING,
    continent STRING,
    wikipedia_link STRING,
    keywords STRING,
    etl_time TIMESTAMP
)
COMMENT '国家维表'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 5. 区域维表
CREATE TABLE IF NOT EXISTS dim_region (
    region_id BIGINT,
    region_code STRING,
    local_code STRING,
    region_name STRING,
    continent STRING,
    iso_country STRING,
    wikipedia_link STRING,
    keywords STRING,
    etl_time TIMESTAMP
)
COMMENT '区域维表'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 6. 跑道明细（机场能力增强数据）
CREATE TABLE IF NOT EXISTS dwd_airport_runway (
    runway_id BIGINT,
    airport_id BIGINT,
    airport_ident STRING,
    length_ft INT,
    width_ft INT,
    surface STRING,
    is_lighted BOOLEAN,
    is_closed BOOLEAN,
    le_ident STRING,
    le_latitude_deg DOUBLE,
    le_longitude_deg DOUBLE,
    le_elevation_ft INT,
    le_heading_deg_true DOUBLE,
    le_displaced_threshold_ft INT,
    he_ident STRING,
    he_latitude_deg DOUBLE,
    he_longitude_deg DOUBLE,
    he_elevation_ft INT,
    he_heading_deg_true DOUBLE,
    he_displaced_threshold_ft INT,
    etl_time TIMESTAMP
)
COMMENT 'DWD层-机场跑道明细'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 7. 机场频率明细（机场能力增强数据）
CREATE TABLE IF NOT EXISTS dwd_airport_frequency (
    frequency_id BIGINT,
    airport_id BIGINT,
    airport_ident STRING,
    frequency_type STRING,
    description STRING,
    frequency_mhz DECIMAL(8,3),
    etl_time TIMESTAMP
)
COMMENT 'DWD层-机场频率明细'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 8. 导航台明细（机场能力增强数据）
CREATE TABLE IF NOT EXISTS dwd_navaid (
    navaid_id BIGINT,
    source_filename STRING,
    ident STRING,
    navaid_name STRING,
    navaid_type STRING,
    frequency_khz INT,
    latitude_deg DOUBLE,
    longitude_deg DOUBLE,
    elevation_ft INT,
    iso_country STRING,
    dme_frequency_khz INT,
    dme_channel STRING,
    dme_latitude_deg DOUBLE,
    dme_longitude_deg DOUBLE,
    dme_elevation_ft INT,
    slaved_variation_deg DOUBLE,
    magnetic_variation_deg DOUBLE,
    usage_type STRING,
    power STRING,
    associated_airport_ident STRING COMMENT '关联 dim_airport.ident，可为空',
    etl_time TIMESTAMP
)
COMMENT 'DWD层-导航台明细'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 9. 航线基础信息（不在 DWD 保存平均值等聚合指标）
CREATE TABLE IF NOT EXISTS dwd_route_info (
    route_id STRING COMMENT '市场起点与终点组成的稳定航线标识',
    market_origin STRING,
    market_destination STRING,
    etl_time TIMESTAMP
)
COMMENT 'DWD层-市场航线基础信息'
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 10. 拒绝记录
CREATE TABLE IF NOT EXISTS dwd_itinerary_reject (
    source_file STRING,
    source_record_id STRING COMMENT '可追溯到原始记录的标识',
    leg_id STRING,
    raw_search_date STRING,
    error_code STRING,
    error_field STRING,
    error_message STRING,
    raw_record STRING,
    etl_time TIMESTAMP
)
COMMENT 'DWD层-报价与航段拒绝记录'
PARTITIONED BY (process_date DATE COMMENT '处理日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

-- 11. 数据质量检查结果
CREATE TABLE IF NOT EXISTS dq_check_result (
    run_id STRING,
    job_name STRING,
    check_code STRING,
    check_name STRING,
    check_level STRING COMMENT 'ERROR 或 WARN',
    check_status STRING COMMENT 'PASS 或 FAIL',
    input_count BIGINT,
    failed_count BIGINT,
    failure_rate DECIMAL(12,8),
    threshold_value STRING,
    details STRING,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
)
COMMENT '数据质量检查结果'
PARTITIONED BY (process_date DATE COMMENT '处理日期分区')
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');
