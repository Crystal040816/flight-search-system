-- One-time upgrade adding itinerary schedule fields to the two lowest-price tables.
-- Back up flight_ads and run this before publishing the updated ADS data.

ALTER TABLE ads_route_lowest_price
    ADD COLUMN departure_time_raw VARCHAR(64) NULL AFTER flight_date,
    ADD COLUMN departure_time_epoch BIGINT NULL AFTER departure_time_raw,
    ADD COLUMN arrival_time_raw VARCHAR(64) NULL AFTER departure_time_epoch,
    ADD COLUMN arrival_time_epoch BIGINT NULL AFTER arrival_time_raw,
    ADD COLUMN travel_duration_minutes INT NULL AFTER arrival_time_epoch;

ALTER TABLE ads_route_cabin_lowest_price
    ADD COLUMN departure_time_raw VARCHAR(64) NULL AFTER flight_date,
    ADD COLUMN departure_time_epoch BIGINT NULL AFTER departure_time_raw,
    ADD COLUMN arrival_time_raw VARCHAR(64) NULL AFTER departure_time_epoch,
    ADD COLUMN arrival_time_epoch BIGINT NULL AFTER arrival_time_raw,
    ADD COLUMN travel_duration_minutes INT NULL AFTER arrival_time_epoch;
