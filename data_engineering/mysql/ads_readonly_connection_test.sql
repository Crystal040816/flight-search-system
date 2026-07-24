-- ADS read-only connection test.
-- Expected connection: 127.0.0.1:13306 / flight_ads / flight_ads_reader

SELECT
    DATABASE() AS database_name,
    CURRENT_USER() AS authenticated_account,
    @@hostname AS mysql_host,
    @@port AS mysql_port;

SELECT
    table_name,
    table_rows
FROM information_schema.tables
WHERE table_schema = 'flight_ads'
ORDER BY table_name;

SELECT 'ads_route_lowest_price' AS table_name, COUNT(*) AS row_count
FROM ads_route_lowest_price
UNION ALL
SELECT 'ads_route_cabin_lowest_price', COUNT(*)
FROM ads_route_cabin_lowest_price
UNION ALL
SELECT 'ads_route_offer_rank', COUNT(*)
FROM ads_route_offer_rank
UNION ALL
SELECT 'ads_airline_offer_share', COUNT(*)
FROM ads_airline_offer_share;

SELECT
    search_date,
    market_origin,
    origin_city,
    market_destination,
    destination_city,
    flight_date,
    departure_time_raw,
    arrival_time_raw,
    travel_duration_minutes,
    lowest_price,
    airline_code,
    seats_remaining,
    cabin_type,
    cabin_summary,
    equipment_summary,
    currency
FROM ads_route_lowest_price
ORDER BY search_date, lowest_price
LIMIT 10;

SELECT
    search_date,
    market_origin,
    market_destination,
    flight_date,
    departure_time_raw,
    arrival_time_raw,
    travel_duration_minutes,
    cabin_type,
    lowest_price,
    avg_price,
    offer_count,
    seats_remaining
FROM ads_route_cabin_lowest_price
ORDER BY
    search_date,
    market_origin,
    market_destination,
    flight_date,
    departure_time_epoch,
    cabin_type,
    lowest_price
LIMIT 20;
