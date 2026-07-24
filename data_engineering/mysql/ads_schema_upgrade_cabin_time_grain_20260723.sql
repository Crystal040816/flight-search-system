-- One-time upgrade changing cabin lowest price to departure-time + cabin grain.
-- Run only after validating the new staged ADS data and immediately before publish.
-- The current cabin table is emptied; use the release backup for rollback if needed.

TRUNCATE TABLE ads_route_cabin_lowest_price;

ALTER TABLE ads_route_cabin_lowest_price
    DROP PRIMARY KEY,
    MODIFY COLUMN departure_time_raw VARCHAR(64) NOT NULL,
    MODIFY COLUMN departure_time_epoch BIGINT NOT NULL,
    MODIFY COLUMN arrival_time_raw VARCHAR(64) NOT NULL,
    MODIFY COLUMN arrival_time_epoch BIGINT NOT NULL,
    MODIFY COLUMN travel_duration_minutes INT NOT NULL,
    DROP INDEX idx_cabin_lowest_route,
    ADD PRIMARY KEY (
        search_date,
        market_origin,
        market_destination,
        flight_date,
        departure_time_epoch,
        cabin_type
    ),
    ADD KEY idx_cabin_lowest_route (
        search_date,
        market_origin,
        market_destination,
        flight_date,
        departure_time_epoch,
        lowest_price
    );
