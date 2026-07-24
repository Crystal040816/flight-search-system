-- Read-only acceptance checks for the enriched ADS release.

SELECT '01_lowest_price_rows' AS metric, COUNT(*) AS metric_value
FROM ads_route_lowest_price
UNION ALL
SELECT '02_cabin_lowest_price_rows', COUNT(*)
FROM ads_route_cabin_lowest_price
UNION ALL
SELECT '03_invalid_price_or_seats', COUNT(*)
FROM ads_route_lowest_price
WHERE lowest_price < 0 OR avg_price < 0 OR lowest_price > avg_price
   OR seats_remaining IS NULL OR seats_remaining < 0
UNION ALL
SELECT '04_missing_origin_dimensions', COUNT(*)
FROM ads_route_lowest_price
WHERE origin_city IS NULL OR origin_country_code IS NULL
UNION ALL
SELECT '05_missing_destination_dimensions', COUNT(*)
FROM ads_route_lowest_price
WHERE destination_city IS NULL OR destination_country_code IS NULL
UNION ALL
SELECT '06_invalid_cabin_metrics', COUNT(*)
FROM ads_route_cabin_lowest_price
WHERE cabin_type = '' OR cabin_summary = '' OR offer_count <= 0
   OR lowest_price < 0 OR avg_price < 0 OR lowest_price > avg_price
   OR seats_remaining IS NULL OR seats_remaining < 0
UNION ALL
SELECT '07_duplicate_cabin_grain', COUNT(*)
FROM (
    SELECT
        search_date,
        market_origin,
        market_destination,
        flight_date,
        departure_time_epoch,
        cabin_type
    FROM ads_route_cabin_lowest_price
    GROUP BY
        search_date,
        market_origin,
        market_destination,
        flight_date,
        departure_time_epoch,
        cabin_type
    HAVING COUNT(*) > 1
) AS duplicates
UNION ALL
SELECT '08_lowest_quote_missing_from_cabin_table', COUNT(*)
FROM ads_route_lowest_price AS route_price
LEFT JOIN ads_route_cabin_lowest_price AS cabin_price
  ON route_price.search_date = cabin_price.search_date
 AND route_price.market_origin = cabin_price.market_origin
 AND route_price.market_destination = cabin_price.market_destination
 AND route_price.flight_date = cabin_price.flight_date
 AND route_price.quote_snapshot_id = cabin_price.quote_snapshot_id
WHERE cabin_price.quote_snapshot_id IS NULL
UNION ALL
SELECT '09_invalid_route_times', COUNT(*)
FROM ads_route_lowest_price
WHERE departure_time_raw IS NULL OR TRIM(departure_time_raw) = ''
   OR arrival_time_raw IS NULL OR TRIM(arrival_time_raw) = ''
   OR departure_time_epoch IS NULL OR departure_time_epoch <= 0
   OR arrival_time_epoch IS NULL OR arrival_time_epoch <= departure_time_epoch
   OR travel_duration_minutes IS NULL OR travel_duration_minutes <= 0
UNION ALL
SELECT '10_invalid_cabin_times', COUNT(*)
FROM ads_route_cabin_lowest_price
WHERE departure_time_raw IS NULL OR TRIM(departure_time_raw) = ''
   OR arrival_time_raw IS NULL OR TRIM(arrival_time_raw) = ''
   OR departure_time_epoch IS NULL OR departure_time_epoch <= 0
   OR arrival_time_epoch IS NULL OR arrival_time_epoch <= departure_time_epoch
   OR travel_duration_minutes IS NULL OR travel_duration_minutes <= 0;
