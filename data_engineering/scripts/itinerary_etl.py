"""Transform itinerary quotes from the Hive ODS table into DWD tables."""

import argparse
import logging
import sys

from pyspark import StorageLevel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


LOG = logging.getLogger("itinerary-etl")
ARRAY_SEPARATOR = r"\|\|"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="flight_db")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit source rows for a smoke test. Omit for the full load.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and count transformed rows without writing Hive tables.",
    )
    parser.add_argument(
        "--sample-write",
        action="store_true",
        help="Allow a limited sample to replace the itinerary DWD tables.",
    )
    parser.add_argument(
        "--shuffle-partitions",
        type=int,
        default=200,
        help="Partitions used when writing search_date-partitioned tables.",
    )
    return parser.parse_args()


def text(column_name: str):
    value = F.trim(F.col(column_name))
    return F.when(value == "", F.lit(None)).otherwise(value)


def boolean_value(column_name: str):
    value = F.lower(text(column_name))
    return (
        F.when(value == "true", F.lit(True))
        .when(value == "false", F.lit(False))
        .otherwise(F.lit(None).cast("boolean"))
    )


def string_array(column_name: str):
    values = F.split(F.coalesce(F.col(column_name), F.lit("")), ARRAY_SEPARATOR, -1)
    return F.transform(
        values,
        lambda item: F.when(F.trim(item) == "", F.lit(None)).otherwise(F.trim(item)),
    )


def typed_array(column_name: str, data_type: str):
    return F.transform(string_array(column_name), lambda item: item.cast(data_type))


def stable_snapshot_id(raw_columns):
    payload = F.to_json(F.struct(*[F.col(name).alias(name) for name in raw_columns]))
    return F.sha2(payload, 256)


def first_error(condition_and_details):
    error_code = None
    error_field = None
    error_message = None

    for condition, code, field, message in condition_and_details:
        if error_code is None:
            error_code = F.when(condition, F.lit(code))
            error_field = F.when(condition, F.lit(field))
            error_message = F.when(condition, F.lit(message))
        else:
            error_code = error_code.when(condition, F.lit(code))
            error_field = error_field.when(condition, F.lit(field))
            error_message = error_message.when(condition, F.lit(message))

    return (
        error_code.otherwise(F.lit(None).cast("string")),
        error_field.otherwise(F.lit(None).cast("string")),
        error_message.otherwise(F.lit(None).cast("string")),
    )


def prepare_source(spark: SparkSession, database: str, limit):
    source = spark.table("{}.ods_itineraries".format(database))
    normalized_leg_id = F.lower(
        F.trim(F.coalesce(F.col("legid"), F.lit("")))
    )
    source = source.filter(normalized_leg_id != "legid")
    if limit is not None:
        if limit <= 0:
            raise ValueError("--limit must be greater than zero")
        source = source.limit(limit)
    return source


def prepare_records(source: DataFrame) -> DataFrame:
    raw_columns = source.columns
    duration = text("travelduration")
    duration_valid = F.coalesce(
        duration.rlike(r"^P(?:[0-9]+D)?T(?:[0-9]+H)?(?:[0-9]+M)?$")
        & ~duration.isin("PT", "P0DT"),
        F.lit(False),
    )
    duration_days = F.coalesce(
        F.regexp_extract(duration, r"^P([0-9]+)D", 1).cast("int"),
        F.lit(0),
    )
    duration_hours = F.coalesce(
        F.regexp_extract(duration, r"T([0-9]+)H", 1).cast("int"),
        F.lit(0),
    )
    duration_minutes = F.coalesce(
        F.regexp_extract(duration, r"([0-9]+)M$", 1).cast("int"),
        F.lit(0),
    )

    records = (
        source.withColumn("_quote_snapshot_id", stable_snapshot_id(raw_columns))
        .withColumn("_leg_id", text("legid"))
        .withColumn("_raw_search_date", text("searchdate"))
        .withColumn("_search_date", text("searchdate").cast("date"))
        .withColumn("_flight_date", text("flightdate").cast("date"))
        .withColumn("_market_origin", text("startingairport"))
        .withColumn("_market_destination", text("destinationairport"))
        .withColumn("_fare_basis_code", text("farebasiscode"))
        .withColumn(
            "_travel_duration_minutes",
            duration_days * F.lit(1440)
            + duration_hours * F.lit(60)
            + duration_minutes,
        )
        .withColumn("_elapsed_days", text("elapseddays").cast("int"))
        .withColumn("_is_basic_economy", boolean_value("isbasiceconomy"))
        .withColumn("_is_refundable", boolean_value("isrefundable"))
        .withColumn("_is_non_stop", boolean_value("isnonstop"))
        .withColumn("_base_fare", text("basefare").cast("decimal(12,2)"))
        .withColumn("_total_fare", text("totalfare").cast("decimal(12,2)"))
        .withColumn("_seats_remaining", text("seatsremaining").cast("int"))
        .withColumn(
            "_total_distance_miles", text("totaltraveldistance").cast("int")
        )
        .withColumn(
            "segment_departure_epochs",
            typed_array("segmentsdeparturetimeepochseconds", "bigint"),
        )
        .withColumn(
            "segment_departure_raw", string_array("segmentsdeparturetimeraw")
        )
        .withColumn(
            "segment_arrival_epochs",
            typed_array("segmentsarrivaltimeepochseconds", "bigint"),
        )
        .withColumn("segment_arrival_raw", string_array("segmentsarrivaltimeraw"))
        .withColumn(
            "segment_arrival_airports",
            string_array("segmentsarrivalairportcode"),
        )
        .withColumn(
            "segment_departure_airports",
            string_array("segmentsdepartureairportcode"),
        )
        .withColumn("segment_airline_names", string_array("segmentsairlinename"))
        .withColumn("segment_airline_codes", string_array("segmentsairlinecode"))
        .withColumn(
            "segment_equipment", string_array("segmentsequipmentdescription")
        )
        .withColumn(
            "segment_durations", typed_array("segmentsdurationinseconds", "int")
        )
        .withColumn("segment_distances", typed_array("segmentsdistance", "int"))
        .withColumn("segment_cabins", string_array("segmentscabincode"))
        .withColumn("_segment_count", F.size(F.col("segment_departure_epochs")))
        .withColumn(
            "_source_file",
            F.regexp_extract(F.input_file_name(), r"([^/]+)$", 1),
        )
        .withColumn("_etl_time", F.current_timestamp())
    )

    segment_arrays = [
        "segment_departure_epochs",
        "segment_departure_raw",
        "segment_arrival_epochs",
        "segment_arrival_raw",
        "segment_arrival_airports",
        "segment_departure_airports",
        "segment_airline_names",
        "segment_airline_codes",
        "segment_equipment",
        "segment_durations",
        "segment_distances",
        "segment_cabins",
    ]
    array_lengths_valid = F.lit(True)
    for column_name in segment_arrays:
        array_lengths_valid = array_lengths_valid & (
            F.size(F.col(column_name)) == F.col("_segment_count")
        )

    nullable_array_values = {"segment_equipment", "segment_distances"}
    required_arrays = [
        name for name in segment_arrays if name not in nullable_array_values
    ]
    required_array_values_valid = F.lit(True)
    for column_name in required_arrays:
        required_array_values_valid = required_array_values_valid & ~F.exists(
            F.col(column_name), lambda item: item.isNull()
        )

    required_values_missing = (
        F.col("_leg_id").isNull()
        | F.col("_market_origin").isNull()
        | F.col("_market_destination").isNull()
        | F.col("_fare_basis_code").isNull()
    )
    dates_invalid = (
        F.col("_search_date").isNull()
        | F.col("_flight_date").isNull()
        | (F.col("_flight_date") < F.col("_search_date"))
    )
    prices_invalid = (
        F.col("_base_fare").isNull()
        | F.col("_total_fare").isNull()
        | (F.col("_base_fare") <= 0)
        | (F.col("_total_fare") < F.col("_base_fare"))
    )
    seats_invalid = F.col("_seats_remaining").isNull() | (
        F.col("_seats_remaining") < 0
    )
    booleans_invalid = (
        F.col("_is_basic_economy").isNull()
        | F.col("_is_refundable").isNull()
        | F.col("_is_non_stop").isNull()
    )
    segments_invalid = (
        (F.col("_segment_count") < 1)
        | ~array_lengths_valid
        | ~required_array_values_valid
        | (F.col("_is_non_stop") != (F.col("_segment_count") == 1))
    )

    error_code, error_field, error_message = first_error(
        [
            (
                required_values_missing,
                "MISSING_REQUIRED",
                "required_fields",
                "A required business field is empty",
            ),
            (dates_invalid, "INVALID_DATE", "searchDate/flightDate", "Invalid dates"),
            (prices_invalid, "INVALID_PRICE", "baseFare/totalFare", "Invalid fare"),
            (seats_invalid, "INVALID_SEATS", "seatsRemaining", "Invalid seat count"),
            (
                ~duration_valid,
                "INVALID_DURATION",
                "travelDuration",
                "Invalid ISO-8601 duration",
            ),
            (
                booleans_invalid,
                "INVALID_BOOLEAN",
                "boolean_fields",
                "Invalid boolean value",
            ),
            (
                segments_invalid,
                "INVALID_SEGMENTS",
                "segment_fields",
                "Segment arrays are invalid or inconsistent",
            ),
        ]
    )

    records = records.withColumn("_error_code", error_code)
    records = records.withColumn("_error_field", error_field)
    records = records.withColumn("_error_message", error_message)
    records = records.withColumn(
        "_raw_record",
        F.when(
            F.col("_error_code").isNotNull(),
            F.to_json(F.struct(*[F.col(name).alias(name) for name in raw_columns])),
        ),
    )

    selected_columns = [
        "_quote_snapshot_id",
        "_leg_id",
        "_raw_search_date",
        "_search_date",
        "_flight_date",
        "_market_origin",
        "_market_destination",
        "_fare_basis_code",
        "_travel_duration_minutes",
        "_elapsed_days",
        "_is_basic_economy",
        "_is_refundable",
        "_is_non_stop",
        "_base_fare",
        "_total_fare",
        "_seats_remaining",
        "_total_distance_miles",
        "_segment_count",
        "_source_file",
        "_etl_time",
        "_error_code",
        "_error_field",
        "_error_message",
        "_raw_record",
    ] + segment_arrays
    return records.select(*selected_columns)


def itinerary_rows(valid: DataFrame) -> DataFrame:
    airport_path = F.concat(
        F.slice(F.col("segment_departure_airports"), 1, 1),
        F.col("segment_arrival_airports"),
    )
    return valid.select(
        F.col("_quote_snapshot_id").alias("quote_snapshot_id"),
        F.col("_leg_id").alias("leg_id"),
        F.col("_flight_date").alias("flight_date"),
        F.col("_market_origin").alias("market_origin"),
        F.col("_market_destination").alias("market_destination"),
        F.col("_fare_basis_code").alias("fare_basis_code"),
        F.element_at("segment_airline_codes", 1).alias("first_airline_code"),
        F.element_at("segment_airline_names", 1).alias("first_airline_name"),
        F.col("_travel_duration_minutes").alias("travel_duration_minutes"),
        F.col("_elapsed_days").alias("elapsed_days"),
        F.col("_is_basic_economy").alias("is_basic_economy"),
        F.col("_is_refundable").alias("is_refundable"),
        F.col("_is_non_stop").alias("is_non_stop"),
        F.col("_base_fare").alias("base_fare"),
        F.col("_total_fare").alias("total_fare"),
        F.lit("USD").alias("currency"),
        F.col("_seats_remaining").alias("seats_remaining"),
        F.col("_total_distance_miles").alias("total_distance_miles"),
        F.col("_segment_count").alias("segment_count"),
        (F.col("_segment_count") - 1).alias("stop_count"),
        F.concat_ws("->", airport_path).alias("actual_airport_path"),
        F.col("_source_file").alias("source_file"),
        F.col("_etl_time").alias("etl_time"),
        F.col("_search_date").alias("search_date"),
    )


def segment_rows(valid: DataFrame) -> DataFrame:
    zipped = F.arrays_zip(
        "segment_departure_airports",
        "segment_arrival_airports",
        "segment_departure_raw",
        "segment_arrival_raw",
        "segment_departure_epochs",
        "segment_arrival_epochs",
        "segment_airline_codes",
        "segment_airline_names",
        "segment_equipment",
        "segment_durations",
        "segment_distances",
        "segment_cabins",
    )
    exploded = valid.select("*", F.posexplode(zipped).alias("segment_index", "segment"))
    next_departure = F.element_at(
        F.col("segment_departure_epochs"), F.col("segment_index") + F.lit(2)
    )

    return exploded.select(
        F.col("_quote_snapshot_id").alias("quote_snapshot_id"),
        F.col("_leg_id").alias("leg_id"),
        F.col("_flight_date").alias("flight_date"),
        F.col("segment_index").cast("int").alias("segment_index"),
        F.col("segment.segment_departure_airports").alias(
            "departure_airport_code"
        ),
        F.col("segment.segment_arrival_airports").alias("arrival_airport_code"),
        F.col("segment.segment_departure_raw").alias("departure_time_raw"),
        F.col("segment.segment_arrival_raw").alias("arrival_time_raw"),
        F.col("segment.segment_departure_epochs").alias("departure_time_epoch"),
        F.col("segment.segment_arrival_epochs").alias("arrival_time_epoch"),
        F.col("segment.segment_airline_codes").alias("airline_code"),
        F.col("segment.segment_airline_names").alias("airline_name"),
        F.col("segment.segment_equipment").alias("equipment_description"),
        F.col("segment.segment_durations").alias("duration_seconds"),
        F.col("segment.segment_distances").alias("distance_miles"),
        F.col("segment.segment_cabins").alias("cabin_code"),
        F.when(
            F.col("segment_index") < F.col("_segment_count") - 1,
            ((next_departure - F.col("segment.segment_arrival_epochs")) / 60).cast(
                "int"
            ),
        ).alias("connection_wait_minutes"),
        F.col("_source_file").alias("source_file"),
        F.col("_etl_time").alias("etl_time"),
        F.col("_search_date").alias("search_date"),
    )


def route_rows(valid: DataFrame) -> DataFrame:
    return valid.select(
        F.concat_ws("-", "_market_origin", "_market_destination").alias("route_id"),
        F.col("_market_origin").alias("market_origin"),
        F.col("_market_destination").alias("market_destination"),
        F.col("_etl_time").alias("etl_time"),
    ).dropDuplicates(["route_id"])


def reject_rows(rejected: DataFrame) -> DataFrame:
    return rejected.select(
        F.col("_source_file").alias("source_file"),
        F.col("_quote_snapshot_id").alias("source_record_id"),
        F.col("_leg_id").alias("leg_id"),
        F.col("_raw_search_date").alias("raw_search_date"),
        F.col("_error_code").alias("error_code"),
        F.col("_error_field").alias("error_field"),
        F.col("_error_message").alias("error_message"),
        F.col("_raw_record").alias("raw_record"),
        F.col("_etl_time").alias("etl_time"),
        F.current_date().alias("process_date"),
    )


def write_partitioned(frame: DataFrame, table_name: str, partitions: int):
    (
        frame.repartition(partitions, "search_date")
        .write.mode("overwrite")
        .insertInto(table_name, overwrite=True)
    )


def run(spark: SparkSession, args):
    if args.sample_write and (args.limit is None or args.dry_run):
        raise ValueError("--sample-write requires --limit and cannot use --dry-run")
    if args.limit is not None and not (args.dry_run or args.sample_write):
        raise ValueError(
            "--limit requires either --dry-run or the explicit --sample-write flag"
        )
    if args.sample_write:
        LOG.warning(
            "data_scope=SAMPLE sample_method=FIRST_N_ROWS sample_size=%d "
            "source_total_rows=82138753",
            args.limit,
        )

    source = prepare_source(spark, args.database, args.limit)
    prepared = prepare_records(source).persist(StorageLevel.DISK_ONLY)

    try:
        counts = prepared.agg(
            F.count(F.lit(1)).alias("total_rows"),
            F.sum(F.when(F.col("_error_code").isNull(), 1).otherwise(0)).alias(
                "valid_rows"
            ),
        ).first()
        total_rows = counts["total_rows"]
        valid_count = counts["valid_rows"]
        valid = prepared.filter(F.col("_error_code").isNull())
        rejected = prepared.filter(F.col("_error_code").isNotNull())
        rejected_count = total_rows - valid_count

        LOG.info(
            "source_rows=%d valid_rows=%d rejected_rows=%d dry_run=%s limit=%s",
            total_rows,
            valid_count,
            rejected_count,
            args.dry_run,
            args.limit,
        )

        if rejected_count:
            error_counts = (
                rejected.groupBy("_error_code", "_error_field")
                .agg(
                    F.count(F.lit(1)).alias("count"),
                    F.first("_raw_record", ignorenulls=True).alias("sample"),
                )
                .orderBy(F.desc("count"), "_error_code")
                .collect()
            )
            for row in error_counts:
                LOG.warning(
                    "reject_summary error_code=%s error_field=%s rows=%d",
                    row["_error_code"],
                    row["_error_field"],
                    row["count"],
                )
                if args.dry_run:
                    LOG.warning(
                        "reject_sample error_code=%s error_field=%s raw_record=%s",
                        row["_error_code"],
                        row["_error_field"],
                        row["sample"],
                    )

        itineraries = itinerary_rows(valid)
        segments = segment_rows(valid)

        if args.dry_run:
            segment_count = segments.count()
            route_count = route_rows(valid).count()
            LOG.info(
                "validated itinerary_rows=%d segment_rows=%d route_rows=%d rejected_rows=%d",
                valid_count,
                segment_count,
                route_count,
                rejected_count,
            )
            return

        database = args.database
        if args.sample_write:
            for target in (
                "dwd_flight_itinerary",
                "dwd_flight_segments",
                "dwd_route_info",
                "dwd_itinerary_reject",
            ):
                spark.sql("TRUNCATE TABLE {}.{}".format(database, target))

        write_partitioned(
            itineraries,
            "{}.dwd_flight_itinerary".format(database),
            args.shuffle_partitions,
        )
        write_partitioned(
            segments,
            "{}.dwd_flight_segments".format(database),
            args.shuffle_partitions,
        )
        route_rows(valid).write.mode("overwrite").insertInto(
            "{}.dwd_route_info".format(database), overwrite=True
        )
        if rejected_count:
            reject_rows(rejected).write.mode("overwrite").insertInto(
                "{}.dwd_itinerary_reject".format(database), overwrite=True
            )

        LOG.info(
            "written itinerary_rows=%d route_table=dwd_route_info rejected_rows=%d",
            valid_count,
            rejected_count,
        )
    finally:
        prepared.unpersist()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    spark = (
        SparkSession.builder.appName("flight-itinerary-ods-to-dwd")
        .enableHiveSupport()
        .getOrCreate()
    )
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    spark.conf.set("spark.sql.shuffle.partitions", str(args.shuffle_partitions))
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    spark.sql("SET hive.exec.dynamic.partition=true")
    spark.sql("SET hive.exec.dynamic.partition.mode=nonstrict")

    try:
        spark.sql("USE {}".format(args.database))
        run(spark, args)
        return 0
    except Exception:
        LOG.exception("Itinerary ETL failed")
        return 1
    finally:
        spark.stop()


if __name__ == "__main__":
    sys.exit(main())
