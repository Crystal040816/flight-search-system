-- One-time upgrade for an existing flight_ads database created before 2026-07-22.
-- Run this before publishing with the updated ads_etl.py.

ALTER TABLE ads_route_lowest_price
    ADD COLUMN origin_city VARCHAR(128) NULL AFTER market_origin,
    ADD COLUMN origin_country_code CHAR(2) NULL AFTER origin_city,
    ADD COLUMN origin_country_name VARCHAR(128) NULL AFTER origin_country_code,
    ADD COLUMN seats_remaining INT NULL AFTER airline_name,
    ADD COLUMN cabin_type VARCHAR(32) NOT NULL DEFAULT 'unknown' AFTER seats_remaining,
    ADD COLUMN cabin_summary VARCHAR(255) NOT NULL DEFAULT 'unknown' AFTER cabin_type,
    ADD COLUMN is_mixed_cabin BOOLEAN NOT NULL DEFAULT FALSE AFTER cabin_summary,
    ADD COLUMN equipment_summary VARCHAR(1024) NOT NULL DEFAULT 'unknown' AFTER is_mixed_cabin;

CREATE TABLE ads_route_cabin_lowest_price (
    search_date DATE NOT NULL,
    market_origin VARCHAR(8) NOT NULL,
    origin_city VARCHAR(128) NULL,
    origin_country_code CHAR(2) NULL,
    origin_country_name VARCHAR(128) NULL,
    market_destination VARCHAR(8) NOT NULL,
    destination_city VARCHAR(128) NULL,
    destination_country_code CHAR(2) NULL,
    destination_country_name VARCHAR(128) NULL,
    flight_date DATE NOT NULL,
    cabin_type VARCHAR(32) NOT NULL,
    cabin_summary VARCHAR(255) NOT NULL,
    is_mixed_cabin BOOLEAN NOT NULL,
    lowest_price DECIMAL(12,2) NOT NULL,
    avg_price DECIMAL(12,2) NOT NULL,
    offer_count BIGINT NOT NULL,
    quote_snapshot_id CHAR(64) NOT NULL,
    airline_code VARCHAR(8) NOT NULL,
    airline_name VARCHAR(128) NOT NULL,
    seats_remaining INT NULL,
    equipment_summary VARCHAR(1024) NOT NULL,
    currency CHAR(3) NOT NULL,
    etl_time DATETIME(6) NOT NULL,
    PRIMARY KEY (
        search_date,
        market_origin,
        market_destination,
        flight_date,
        cabin_type
    ),
    KEY idx_cabin_lowest_route (
        search_date,
        market_origin,
        market_destination,
        flight_date,
        lowest_price
    ),
    KEY idx_cabin_lowest_type (search_date, cabin_type, lowest_price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
