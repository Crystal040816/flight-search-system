"""Load the small OpenFlights ODS tables into typed Hive DWD tables."""

import argparse
import logging
import sys
from collections import OrderedDict

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


LOG = logging.getLogger("small-table-etl")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="flight_db")
    parser.add_argument(
        "--tables",
        default="all",
        help="Comma-separated target table names, or 'all'.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and transform sources without writing target tables.",
    )
    return parser.parse_args()


def clean_text(column_name: str):
    value = F.trim(F.col(column_name))
    return F.when(value == "", F.lit(None)).otherwise(value)


def typed(column_name: str, data_type: str):
    return clean_text(column_name).cast(data_type)


def boolean_value(column_name: str):
    value = F.lower(clean_text(column_name))
    return (
        F.when(value.isin("1", "true", "yes", "y"), F.lit(True))
        .when(value.isin("0", "false", "no", "n"), F.lit(False))
        .otherwise(F.lit(None).cast("boolean"))
    )


def with_etl_time(expressions):
    return expressions + [F.current_timestamp().alias("etl_time")]


def transform_country(source: DataFrame) -> DataFrame:
    return source.select(
        *with_etl_time(
            [
                typed("id", "bigint").alias("country_id"),
                clean_text("code").alias("country_code"),
                clean_text("name").alias("country_name"),
                clean_text("continent").alias("continent"),
                clean_text("wikipedia_link").alias("wikipedia_link"),
                clean_text("keywords").alias("keywords"),
            ]
        )
    )


def transform_region(source: DataFrame) -> DataFrame:
    return source.select(
        *with_etl_time(
            [
                typed("id", "bigint").alias("region_id"),
                clean_text("code").alias("region_code"),
                clean_text("local_code").alias("local_code"),
                clean_text("name").alias("region_name"),
                clean_text("continent").alias("continent"),
                clean_text("iso_country").alias("iso_country"),
                clean_text("wikipedia_link").alias("wikipedia_link"),
                clean_text("keywords").alias("keywords"),
            ]
        )
    )


def transform_airport(source: DataFrame) -> DataFrame:
    return source.select(
        *with_etl_time(
            [
                typed("id", "bigint").alias("airport_id"),
                clean_text("ident").alias("ident"),
                clean_text("type").alias("airport_type"),
                clean_text("name").alias("airport_name"),
                typed("latitude_deg", "double").alias("latitude_deg"),
                typed("longitude_deg", "double").alias("longitude_deg"),
                typed("elevation_ft", "int").alias("elevation_ft"),
                clean_text("continent").alias("continent"),
                clean_text("iso_country").alias("iso_country"),
                clean_text("iso_region").alias("iso_region"),
                clean_text("municipality").alias("municipality"),
                boolean_value("scheduled_service").alias("scheduled_service"),
                clean_text("gps_code").alias("gps_code"),
                clean_text("iata_code").alias("iata_code"),
                clean_text("local_code").alias("local_code"),
                clean_text("home_link").alias("home_link"),
                clean_text("wikipedia_link").alias("wikipedia_link"),
                clean_text("keywords").alias("keywords"),
            ]
        )
    )


def transform_runway(source: DataFrame) -> DataFrame:
    return source.select(
        *with_etl_time(
            [
                typed("id", "bigint").alias("runway_id"),
                typed("airport_ref", "bigint").alias("airport_id"),
                clean_text("airport_ident").alias("airport_ident"),
                typed("length_ft", "int").alias("length_ft"),
                typed("width_ft", "int").alias("width_ft"),
                clean_text("surface").alias("surface"),
                boolean_value("lighted").alias("is_lighted"),
                boolean_value("closed").alias("is_closed"),
                clean_text("le_ident").alias("le_ident"),
                typed("le_latitude_deg", "double").alias("le_latitude_deg"),
                typed("le_longitude_deg", "double").alias("le_longitude_deg"),
                typed("le_elevation_ft", "int").alias("le_elevation_ft"),
                typed("le_heading_degt", "double").alias("le_heading_deg_true"),
                typed("le_displaced_threshold_ft", "int").alias(
                    "le_displaced_threshold_ft"
                ),
                clean_text("he_ident").alias("he_ident"),
                typed("he_latitude_deg", "double").alias("he_latitude_deg"),
                typed("he_longitude_deg", "double").alias("he_longitude_deg"),
                typed("he_elevation_ft", "int").alias("he_elevation_ft"),
                typed("he_heading_degt", "double").alias("he_heading_deg_true"),
                typed("he_displaced_threshold_ft", "int").alias(
                    "he_displaced_threshold_ft"
                ),
            ]
        )
    )


def transform_frequency(source: DataFrame) -> DataFrame:
    return source.select(
        *with_etl_time(
            [
                typed("id", "bigint").alias("frequency_id"),
                typed("airport_ref", "bigint").alias("airport_id"),
                clean_text("airport_ident").alias("airport_ident"),
                clean_text("type").alias("frequency_type"),
                clean_text("description").alias("description"),
                typed("frequency_mhz", "decimal(8,3)").alias("frequency_mhz"),
            ]
        )
    )


def transform_navaid(source: DataFrame) -> DataFrame:
    return source.select(
        *with_etl_time(
            [
                typed("id", "bigint").alias("navaid_id"),
                clean_text("filename").alias("source_filename"),
                clean_text("ident").alias("ident"),
                clean_text("name").alias("navaid_name"),
                clean_text("type").alias("navaid_type"),
                typed("frequency_khz", "int").alias("frequency_khz"),
                typed("latitude_deg", "double").alias("latitude_deg"),
                typed("longitude_deg", "double").alias("longitude_deg"),
                typed("elevation_ft", "int").alias("elevation_ft"),
                clean_text("iso_country").alias("iso_country"),
                typed("dme_frequency_khz", "int").alias("dme_frequency_khz"),
                clean_text("dme_channel").alias("dme_channel"),
                typed("dme_latitude_deg", "double").alias("dme_latitude_deg"),
                typed("dme_longitude_deg", "double").alias("dme_longitude_deg"),
                typed("dme_elevation_ft", "int").alias("dme_elevation_ft"),
                typed("slaved_variation_deg", "double").alias(
                    "slaved_variation_deg"
                ),
                typed("magnetic_variation_deg", "double").alias(
                    "magnetic_variation_deg"
                ),
                clean_text("usagetype").alias("usage_type"),
                clean_text("power").alias("power"),
                clean_text("associated_airport").alias(
                    "associated_airport_ident"
                ),
            ]
        )
    )


TABLES = OrderedDict(
    [
        ("dim_country", ("ods_countries", transform_country)),
        ("dim_region", ("ods_regions", transform_region)),
        ("dim_airport", ("ods_airports", transform_airport)),
        ("dwd_airport_runway", ("ods_runways", transform_runway)),
        (
            "dwd_airport_frequency",
            ("ods_airport_frequencies", transform_frequency),
        ),
        ("dwd_navaid", ("ods_navaids", transform_navaid)),
    ]
)


def selected_tables(raw_selection: str):
    if raw_selection.strip().lower() == "all":
        return list(TABLES)

    selection = [name.strip().lower() for name in raw_selection.split(",")]
    unknown = sorted(set(selection) - set(TABLES))
    if unknown:
        raise ValueError("Unknown target table(s): {}".format(", ".join(unknown)))
    return selection


def validated_source(spark: SparkSession, database: str, table_name: str):
    full_name = "{}.{}".format(database, table_name)
    raw = spark.table(full_name)

    # Spark does not honor Hive's skip.header.line.count for OpenCSVSerde tables.
    normalized_id = F.lower(
        F.trim(F.coalesce(F.col("id"), F.lit("")))
    )
    source = raw.filter(normalized_id != "id").cache()
    source_rows = source.count()
    invalid_ids = source.filter(typed("id", "bigint").isNull()).count()
    duplicate_ids = (
        source.groupBy(clean_text("id").alias("source_id"))
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    if invalid_ids or duplicate_ids:
        source.unpersist()
        raise ValueError(
            "{} failed validation: rows={}, invalid_ids={}, duplicate_ids={}".format(
                full_name, source_rows, invalid_ids, duplicate_ids
            )
        )

    return source, source_rows


def run_table(
    spark: SparkSession,
    database: str,
    target_name: str,
    dry_run: bool,
):
    source_name, transform = TABLES[target_name]
    source, source_rows = validated_source(spark, database, source_name)

    try:
        result = transform(source)
        if dry_run:
            target_rows = result.count()
            action = "validated"
        else:
            full_target = "{}.{}".format(database, target_name)
            result.write.mode("overwrite").insertInto(full_target, overwrite=True)
            target_rows = spark.table(full_target).count()
            action = "written"

        if target_rows != source_rows:
            raise RuntimeError(
                "Row count mismatch for {}: source={}, target={}".format(
                    target_name, source_rows, target_rows
                )
            )

        LOG.info(
            "table=%s source=%s rows=%d action=%s",
            target_name,
            source_name,
            target_rows,
            action,
        )
    finally:
        source.unpersist()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        targets = selected_tables(args.tables)
    except ValueError as exc:
        LOG.error(str(exc))
        return 2

    spark = (
        SparkSession.builder.appName("flight-small-table-ods-to-dwd")
        .enableHiveSupport()
        .getOrCreate()
    )
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    try:
        spark.sql("USE {}".format(args.database))
        for target_name in targets:
            run_table(spark, args.database, target_name, args.dry_run)
        return 0
    except Exception:
        LOG.exception("Small-table ETL failed")
        return 1
    finally:
        spark.stop()


if __name__ == "__main__":
    sys.exit(main())
