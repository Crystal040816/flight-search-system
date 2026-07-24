-- Logical ADS schemas. The production serving tables are stored in MySQL.

USE flight_db;

CREATE TABLE IF NOT EXISTS ads_route_lowest_price (
    market_origin STRING,
    origin_city STRING,
    origin_country_code STRING,
    origin_country_name STRING,
    market_destination STRING,
    destination_city STRING,
    destination_country_code STRING,
    destination_country_name STRING,
    flight_date DATE,
    lowest_price DECIMAL(12,2),
    avg_price DECIMAL(12,2),
    quote_snapshot_id STRING,
    airline_code STRING,
    airline_name STRING,
    seats_remaining INT,
    cabin_type STRING COMMENT 'Single cabin code, mixed, or unknown',
    cabin_summary STRING COMMENT 'Segment cabin sequence separated by ||',
    is_mixed_cabin BOOLEAN,
    equipment_summary STRING COMMENT 'Segment equipment sequence separated by ||',
    currency STRING,
    etl_time TIMESTAMP
)
COMMENT 'Lowest itinerary offer for each route and flight date'
PARTITIONED BY (search_date DATE)
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

CREATE TABLE IF NOT EXISTS ads_route_cabin_lowest_price (
    market_origin STRING,
    origin_city STRING,
    origin_country_code STRING,
    origin_country_name STRING,
    market_destination STRING,
    destination_city STRING,
    destination_country_code STRING,
    destination_country_name STRING,
    flight_date DATE,
    cabin_type STRING COMMENT 'Single cabin code, mixed, or unknown',
    cabin_summary STRING,
    is_mixed_cabin BOOLEAN,
    lowest_price DECIMAL(12,2),
    avg_price DECIMAL(12,2),
    offer_count BIGINT,
    quote_snapshot_id STRING,
    airline_code STRING,
    airline_name STRING,
    seats_remaining INT,
    equipment_summary STRING,
    currency STRING,
    etl_time TIMESTAMP
)
COMMENT 'Lowest itinerary offer grouped by route, flight date, and cabin type'
PARTITIONED BY (search_date DATE)
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

CREATE TABLE IF NOT EXISTS ads_route_offer_rank (
    rank_num INT,
    route_id STRING,
    market_origin STRING,
    market_destination STRING,
    quote_count BIGINT,
    distinct_leg_count BIGINT,
    avg_price DECIMAL(12,2),
    previous_day_avg_price DECIMAL(12,2),
    price_change_pct DECIMAL(9,4),
    etl_time TIMESTAMP
)
COMMENT 'Route offer-volume ranking; it is not passenger demand or sales'
PARTITIONED BY (search_date DATE)
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');

CREATE TABLE IF NOT EXISTS ads_airline_offer_share (
    airline_code STRING,
    airline_name STRING,
    quote_count BIGINT,
    offer_share_pct DECIMAL(9,6),
    avg_price DECIMAL(12,2),
    etl_time TIMESTAMP
)
COMMENT 'Airline quote share; it is not sales market share'
PARTITIONED BY (search_date DATE)
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');
