SET hive.exec.dynamic.partition.mode=nonstrict;
USE flight_db;

INSERT OVERWRITE TABLE dwd_flight_itinerary PARTITION(dt)
SELECT 
    legid as leg_id,
    to_date(searchdate) as search_date,
    to_date(flightdate) as flight_date,
    startingairport as starting_airport,
    destinationairport as destination_airport,
    split(segmentsairlinecode, '\\|\\|')[0] as airline_code,
    split(segmentsairlinename, '\\|\\|')[0] as airline_name,
    CAST(totalfare AS DOUBLE) as total_fare,
    CAST(basefare AS DOUBLE) as base_fare,
    CAST(seatsremaining AS INT) as seats_remaining,
    (isnonstop = 'true') as is_non_stop,
    (isrefundable = 'true') as is_refundable,
    (isbasiceconomy = 'true') as is_basic_economy,
    CAST(REGEXP_REPLACE(travelduration, 'h', '') AS INT) * 3600 as travel_duration,
    CAST(totaltraveldistance AS INT) as total_distance,
    size(split(segmentsairlinecode, '\\|\\|')) as segments_count,
    split(segmentscabincode, '\\|\\|')[0] as cabin_code,
    flightdate as dt
FROM ods_itineraries
WHERE legid IS NOT NULL 
  AND flightdate IS NOT NULL 
  AND totalfare IS NOT NULL 
  AND CAST(totalfare AS DOUBLE) > 0;
