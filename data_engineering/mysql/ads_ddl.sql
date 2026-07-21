-- Serving-layer tables consumed by Superset and the application API.
-- Run this file against the flight_ads MySQL database.

CREATE TABLE IF NOT EXISTS ads_route_lowest_price (
    search_date DATE NOT NULL,
    market_origin VARCHAR(8) NOT NULL,
    market_destination VARCHAR(8) NOT NULL,
    destination_city VARCHAR(128) NULL,
    destination_country_code CHAR(2) NULL,
    destination_country_name VARCHAR(128) NULL,
    flight_date DATE NOT NULL,
    lowest_price DECIMAL(12,2) NOT NULL,
    avg_price DECIMAL(12,2) NOT NULL,
    quote_snapshot_id CHAR(64) NOT NULL,
    airline_code VARCHAR(8) NOT NULL,
    airline_name VARCHAR(128) NOT NULL,
    currency CHAR(3) NOT NULL,
    etl_time DATETIME(6) NOT NULL,
    PRIMARY KEY (
        search_date,
        market_origin,
        market_destination,
        flight_date
    ),
    KEY idx_route_lowest_destination (
        search_date,
        market_destination,
        lowest_price
    ),
    KEY idx_route_lowest_flight_date (flight_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ads_route_offer_rank (
    search_date DATE NOT NULL,
    rank_num INT NOT NULL,
    route_id VARCHAR(32) NOT NULL,
    market_origin VARCHAR(8) NOT NULL,
    market_destination VARCHAR(8) NOT NULL,
    quote_count BIGINT NOT NULL,
    distinct_leg_count BIGINT NOT NULL,
    avg_price DECIMAL(12,2) NOT NULL,
    previous_day_avg_price DECIMAL(12,2) NULL,
    price_change_pct DECIMAL(9,4) NULL,
    etl_time DATETIME(6) NOT NULL,
    PRIMARY KEY (search_date, route_id),
    UNIQUE KEY uk_route_offer_rank (search_date, rank_num),
    KEY idx_route_offer_volume (search_date, quote_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ads_airline_offer_share (
    search_date DATE NOT NULL,
    airline_code VARCHAR(8) NOT NULL,
    airline_name VARCHAR(128) NOT NULL,
    quote_count BIGINT NOT NULL,
    offer_share_pct DECIMAL(9,6) NOT NULL,
    avg_price DECIMAL(12,2) NOT NULL,
    etl_time DATETIME(6) NOT NULL,
    PRIMARY KEY (search_date, airline_code),
    KEY idx_airline_offer_share (search_date, offer_share_pct)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
