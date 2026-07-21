"""Aggregate DWD itinerary quotes into the Hive DWS tables."""

import argparse
import logging
import sys

from pyspark import StorageLevel
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F


LOG = logging.getLogger("dws-etl")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="flight_db")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--shuffle-partitions", type=int, default=24)
    return parser.parse_args()


def route_daily(source: DataFrame) -> DataFrame:
    grouped = source.groupBy(
        "search_date", "route_id", "market_origin", "market_destination"
    ).agg(
        F.count(F.lit(1)).alias("quote_count"),
        F.countDistinct("leg_id").alias("distinct_leg_count"),
        F.avg("total_fare").cast("decimal(12,2)").alias("avg_price"),
        F.min("total_fare").cast("decimal(12,2)").alias("min_price"),
        F.max("total_fare").cast("decimal(12,2)").alias("max_price"),
        F.avg("seats_remaining").cast("decimal(12,2)").alias("avg_seats"),
        F.avg("travel_duration_minutes")
        .cast("decimal(12,2)")
        .alias("avg_duration_minutes"),
        F.sum(F.when(F.col("is_non_stop"), 1).otherwise(0)).alias(
            "nonstop_quote_count"
        ),
    )

    return grouped.select(
        "route_id",
        "market_origin",
        "market_destination",
        "quote_count",
        "distinct_leg_count",
        "avg_price",
        "min_price",
        "max_price",
        "avg_seats",
        "avg_duration_minutes",
        "nonstop_quote_count",
        (
            F.col("nonstop_quote_count") / F.col("quote_count")
        ).cast("decimal(9,6)").alias("nonstop_quote_rate"),
        F.current_timestamp().alias("etl_time"),
        "search_date",
    )


def airline_daily(source: DataFrame) -> DataFrame:
    grouped = source.groupBy(
        "search_date", "first_airline_code", "first_airline_name"
    ).agg(
        F.count(F.lit(1)).alias("quote_count"),
        F.countDistinct("leg_id").alias("distinct_leg_count"),
        F.avg("total_fare").cast("decimal(12,2)").alias("avg_price"),
        F.min("total_fare").cast("decimal(12,2)").alias("min_price"),
        F.max("total_fare").cast("decimal(12,2)").alias("max_price"),
    )
    date_window = Window.partitionBy("search_date")

    return grouped.withColumn(
        "daily_quote_count", F.sum("quote_count").over(date_window)
    ).select(
        F.col("first_airline_code").alias("airline_code"),
        F.col("first_airline_name").alias("airline_name"),
        "quote_count",
        "distinct_leg_count",
        "avg_price",
        "min_price",
        "max_price",
        (
            F.col("quote_count") * F.lit(100) / F.col("daily_quote_count")
        ).cast("decimal(9,6)").alias("offer_share_pct"),
        F.current_timestamp().alias("etl_time"),
        "search_date",
    )


def airport_daily(source: DataFrame) -> DataFrame:
    origins = source.groupBy("search_date", "market_origin").agg(
        F.count(F.lit(1)).alias("origin_quote_count"),
        F.avg("total_fare").cast("decimal(12,2)").alias("avg_origin_price"),
    ).alias("origins")
    destinations = source.groupBy("search_date", "market_destination").agg(
        F.count(F.lit(1)).alias("destination_quote_count"),
        F.avg("total_fare")
        .cast("decimal(12,2)")
        .alias("avg_destination_price"),
    ).alias("destinations")

    joined = origins.join(
        destinations,
        (F.col("origins.search_date") == F.col("destinations.search_date"))
        & (
            F.col("origins.market_origin")
            == F.col("destinations.market_destination")
        ),
        "full",
    )
    return joined.select(
        F.coalesce(
            F.col("origins.market_origin"),
            F.col("destinations.market_destination"),
        ).alias("market_airport_code"),
        F.coalesce(F.col("origins.origin_quote_count"), F.lit(0))
        .cast("bigint")
        .alias("origin_quote_count"),
        F.coalesce(F.col("destinations.destination_quote_count"), F.lit(0))
        .cast("bigint")
        .alias("destination_quote_count"),
        F.col("origins.avg_origin_price").alias("avg_origin_price"),
        F.col("destinations.avg_destination_price").alias(
            "avg_destination_price"
        ),
        F.current_timestamp().alias("etl_time"),
        F.coalesce(
            F.col("origins.search_date"), F.col("destinations.search_date")
        ).alias("search_date"),
    )


def route_profile(source: DataFrame) -> DataFrame:
    grouped = source.groupBy(
        "route_id", "market_origin", "market_destination"
    ).agg(
        F.avg("total_distance_miles")
        .cast("decimal(12,2)")
        .alias("avg_distance_miles"),
        F.avg("travel_duration_minutes")
        .cast("decimal(12,2)")
        .alias("avg_duration_minutes"),
        F.min("search_date").alias("first_seen_date"),
        F.max("search_date").alias("last_seen_date"),
    )
    return grouped.withColumn("etl_time", F.current_timestamp())


def write_partitioned(frame: DataFrame, table_name: str, partitions: int):
    (
        frame.repartition(partitions, "search_date")
        .write.mode("overwrite")
        .insertInto(table_name, overwrite=True)
    )


def validate(
    source_count: int,
    routes: DataFrame,
    airlines: DataFrame,
    airports: DataFrame,
    profiles: DataFrame,
):
    route_metrics = routes.agg(
        F.count(F.lit(1)).alias("rows"),
        F.sum("quote_count").alias("quotes"),
        F.sum(
            F.when(
                (F.col("nonstop_quote_rate") < 0)
                | (F.col("nonstop_quote_rate") > 1),
                1,
            ).otherwise(0)
        ).alias("invalid_rates"),
    ).first()
    airline_metrics = airlines.agg(
        F.count(F.lit(1)).alias("rows"),
        F.sum("quote_count").alias("quotes"),
        F.sum(
            F.when(
                (F.col("offer_share_pct") < 0)
                | (F.col("offer_share_pct") > 100),
                1,
            ).otherwise(0)
        ).alias("invalid_shares"),
    ).first()
    airport_metrics = airports.agg(
        F.count(F.lit(1)).alias("rows"),
        F.sum("origin_quote_count").alias("origin_quotes"),
        F.sum("destination_quote_count").alias("destination_quotes"),
    ).first()
    profile_count = profiles.count()

    failures = []
    if route_metrics["quotes"] != source_count:
        failures.append("route quote conservation failed")
    if airline_metrics["quotes"] != source_count:
        failures.append("airline quote conservation failed")
    if airport_metrics["origin_quotes"] != source_count:
        failures.append("origin quote conservation failed")
    if airport_metrics["destination_quotes"] != source_count:
        failures.append("destination quote conservation failed")
    if route_metrics["invalid_rates"]:
        failures.append("invalid nonstop quote rates")
    if airline_metrics["invalid_shares"]:
        failures.append("invalid airline offer shares")

    LOG.info(
        "source_rows=%d route_daily_rows=%d airline_daily_rows=%d "
        "airport_daily_rows=%d route_profile_rows=%d",
        source_count,
        route_metrics["rows"],
        airline_metrics["rows"],
        airport_metrics["rows"],
        profile_count,
    )
    if failures:
        raise ValueError("; ".join(failures))


def run(spark: SparkSession, args):
    database = args.database
    source = spark.table("{}.dwd_flight_itinerary".format(database)).select(
        "quote_snapshot_id",
        "leg_id",
        "market_origin",
        "market_destination",
        "first_airline_code",
        "first_airline_name",
        "travel_duration_minutes",
        "is_non_stop",
        "total_fare",
        "seats_remaining",
        "total_distance_miles",
        "search_date",
    )
    source = source.withColumn(
        "route_id", F.concat_ws("-", "market_origin", "market_destination")
    ).persist(StorageLevel.MEMORY_AND_DISK)

    try:
        source_count = source.count()
        routes = route_daily(source)
        airlines = airline_daily(source)
        airports = airport_daily(source)
        profiles = route_profile(source)
        validate(source_count, routes, airlines, airports, profiles)

        if args.dry_run:
            LOG.info("action=validated")
            return

        for target in (
            "dws_route_daily_stats",
            "dws_airline_stats",
            "dws_airport_stats",
            "dws_route_profile",
        ):
            spark.sql("TRUNCATE TABLE {}.{}".format(database, target))

        write_partitioned(
            routes,
            "{}.dws_route_daily_stats".format(database),
            args.shuffle_partitions,
        )
        write_partitioned(
            airlines,
            "{}.dws_airline_stats".format(database),
            args.shuffle_partitions,
        )
        write_partitioned(
            airports,
            "{}.dws_airport_stats".format(database),
            args.shuffle_partitions,
        )
        profiles.coalesce(1).write.mode("overwrite").insertInto(
            "{}.dws_route_profile".format(database), overwrite=True
        )
        LOG.info("action=written")
    finally:
        source.unpersist()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if args.shuffle_partitions <= 0:
        LOG.error("--shuffle-partitions must be greater than zero")
        return 2

    spark = (
        SparkSession.builder.appName("flight-dwd-to-dws")
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
        LOG.exception("DWS ETL failed")
        return 1
    finally:
        spark.stop()


if __name__ == "__main__":
    sys.exit(main())
