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
SELECT 'ads_route_offer_rank', COUNT(*)
FROM ads_route_offer_rank
UNION ALL
SELECT 'ads_airline_offer_share', COUNT(*)
FROM ads_airline_offer_share;

SELECT
    search_date,
    market_origin,
    market_destination,
    flight_date,
    lowest_price,
    airline_code,
    currency
FROM ads_route_lowest_price
ORDER BY search_date, lowest_price
LIMIT 10;
