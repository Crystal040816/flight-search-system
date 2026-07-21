"""Build serving-layer aggregates and publish them to MySQL."""

import argparse
import configparser
import logging
import os
import sys

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F


LOG = logging.getLogger("ads-etl")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="flight_db")
    parser.add_argument(
        "--mysql-config",
        default="~/.flight_ads_writer.cnf",
        help="MySQL client config containing the [client] connection settings.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def mysql_options(config_path: str):
    path = os.path.abspath(os.path.expanduser(config_path))
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(path):
        raise ValueError("MySQL config does not exist: {}".format(path))
    if "client" not in parser:
        raise ValueError("MySQL config is missing the [client] section")

    client = parser["client"]
    required = ("host", "port", "user", "password", "database")
    missing = [name for name in required if not client.get(name)]
    if missing:
        raise ValueError(
            "MySQL config is missing: {}".format(", ".join(sorted(missing)))
        )

    url = (
        "jdbc:mysql://{host}:{port}/{database}"
        "?serverTimezone=UTC&rewriteBatchedStatements=true"
    ).format(**client)
    return {
        "url": url,
        "user": client["user"],
        "password": client["password"],
        "driver": "com.mysql.cj.jdbc.Driver",
    }


def destination_dimension(spark: SparkSession, database: str) -> DataFrame:
    airports = spark.table("{}.dim_airport".format(database)).filter(
        F.col("iata_code").isNotNull()
    )
    priority = (
        F.when(F.col("airport_type") == "large_airport", 1)
        .when(F.col("airport_type") == "medium_airport", 2)
        .otherwise(3)
    )
    airport_window = Window.partitionBy("iata_code").orderBy(priority, "airport_id")
    airports = (
        airports.withColumn("airport_rank", F.row_number().over(airport_window))
        .filter(F.col("airport_rank") == 1)
        .select(
            F.col("iata_code").alias("destination_code"),
            F.col("municipality").alias("destination_city"),
            F.col("iso_country").alias("destination_country_code"),
        )
    )
    countries = spark.table("{}.dim_country".format(database)).select(
        F.col("country_code").alias("country_code"),
        F.col("country_name").alias("destination_country_name"),
    )
    return airports.join(
        countries,
        airports.destination_country_code == countries.country_code,
        "left",
    ).drop("country_code")


def route_lowest_price(spark: SparkSession, database: str) -> DataFrame:
    quotes = spark.table("{}.dwd_flight_itinerary".format(database))
    group_window = Window.partitionBy(
        "search_date", "market_origin", "market_destination", "flight_date"
    )
    lowest_window = group_window.orderBy(
        F.col("total_fare").asc(),
        F.col("travel_duration_minutes").asc(),
        F.col("quote_snapshot_id").asc(),
    )
    lowest = (
        quotes.withColumn(
            "avg_price",
            F.avg("total_fare").over(group_window).cast("decimal(12,2)"),
        )
        .withColumn("price_rank", F.row_number().over(lowest_window))
        .filter(F.col("price_rank") == 1)
    )
    destinations = destination_dimension(spark, database)

    return lowest.join(
        destinations,
        lowest.market_destination == destinations.destination_code,
        "left",
    ).select(
        "search_date",
        "market_origin",
        "market_destination",
        "destination_city",
        "destination_country_code",
        "destination_country_name",
        "flight_date",
        F.col("total_fare").cast("decimal(12,2)").alias("lowest_price"),
        "avg_price",
        "quote_snapshot_id",
        F.col("first_airline_code").alias("airline_code"),
        F.col("first_airline_name").alias("airline_name"),
        "currency",
        F.current_timestamp().alias("etl_time"),
    )


def route_offer_rank(spark: SparkSession, database: str) -> DataFrame:
    current = spark.table("{}.dws_route_daily_stats".format(database)).alias(
        "current"
    )
    previous = spark.table("{}.dws_route_daily_stats".format(database)).select(
        F.col("search_date").alias("previous_search_date"),
        F.col("route_id").alias("previous_route_id"),
        F.col("avg_price").alias("previous_day_avg_price"),
    ).alias("previous")
    joined = current.join(
        previous,
        (F.col("current.route_id") == F.col("previous.previous_route_id"))
        & (
            F.col("current.search_date")
            == F.date_add(F.col("previous.previous_search_date"), 1)
        ),
        "left",
    )
    rank_window = Window.partitionBy("current.search_date").orderBy(
        F.col("current.quote_count").desc(), F.col("current.route_id").asc()
    )

    return joined.withColumn("rank_num", F.row_number().over(rank_window)).select(
        F.col("current.search_date").alias("search_date"),
        "rank_num",
        F.col("current.route_id").alias("route_id"),
        F.col("current.market_origin").alias("market_origin"),
        F.col("current.market_destination").alias("market_destination"),
        F.col("current.quote_count").alias("quote_count"),
        F.col("current.distinct_leg_count").alias("distinct_leg_count"),
        F.col("current.avg_price").alias("avg_price"),
        F.col("previous.previous_day_avg_price").alias("previous_day_avg_price"),
        F.when(
            F.col("previous.previous_day_avg_price").isNotNull()
            & (F.col("previous.previous_day_avg_price") != 0),
            (
                (F.col("current.avg_price") - F.col("previous.previous_day_avg_price"))
                * F.lit(100)
                / F.col("previous.previous_day_avg_price")
            ).cast("decimal(9,4)"),
        ).alias("price_change_pct"),
        F.current_timestamp().alias("etl_time"),
    )


def airline_offer_share(spark: SparkSession, database: str) -> DataFrame:
    return spark.table("{}.dws_airline_stats".format(database)).select(
        "search_date",
        "airline_code",
        "airline_name",
        "quote_count",
        "offer_share_pct",
        "avg_price",
        F.current_timestamp().alias("etl_time"),
    )


def validate(lowest: DataFrame, routes: DataFrame, airlines: DataFrame):
    lowest_metrics = lowest.agg(
        F.count(F.lit(1)).alias("rows"),
        F.sum(
            F.when(
                F.col("quote_snapshot_id").isNull()
                | F.col("lowest_price").isNull()
                | F.col("avg_price").isNull(),
                1,
            ).otherwise(0)
        ).alias("invalid"),
    ).first()
    route_metrics = routes.agg(
        F.count(F.lit(1)).alias("rows"),
        F.sum(
            F.when(F.col("rank_num") <= 0, 1).otherwise(0)
        ).alias("invalid"),
    ).first()
    airline_metrics = airlines.agg(
        F.count(F.lit(1)).alias("rows"),
        F.sum(
            F.when(
                (F.col("offer_share_pct") < 0)
                | (F.col("offer_share_pct") > 100),
                1,
            ).otherwise(0)
        ).alias("invalid"),
    ).first()

    if not lowest_metrics["rows"] or lowest_metrics["invalid"]:
        raise ValueError("ads_route_lowest_price validation failed")
    if not route_metrics["rows"] or route_metrics["invalid"]:
        raise ValueError("ads_route_offer_rank validation failed")
    if not airline_metrics["rows"] or airline_metrics["invalid"]:
        raise ValueError("ads_airline_offer_share validation failed")

    LOG.info(
        "lowest_price_rows=%d route_rank_rows=%d airline_share_rows=%d",
        lowest_metrics["rows"],
        route_metrics["rows"],
        airline_metrics["rows"],
    )


def write_mysql(frame: DataFrame, table_name: str, options):
    (
        frame.coalesce(2)
        .write.format("jdbc")
        .options(**options)
        .option("dbtable", table_name)
        .option("batchsize", "5000")
        .option("isolationLevel", "READ_COMMITTED")
        .option("truncate", "true")
        .mode("overwrite")
        .save()
    )


def run(spark: SparkSession, args):
    lowest = route_lowest_price(spark, args.database).cache()
    routes = route_offer_rank(spark, args.database).cache()
    airlines = airline_offer_share(spark, args.database).cache()

    try:
        validate(lowest, routes, airlines)
        if args.dry_run:
            LOG.info("action=validated")
            return

        options = mysql_options(args.mysql_config)
        write_mysql(lowest, "ads_route_lowest_price", options)
        write_mysql(routes, "ads_route_offer_rank", options)
        write_mysql(airlines, "ads_airline_offer_share", options)
        LOG.info("action=written target=mysql")
    finally:
        lowest.unpersist()
        routes.unpersist()
        airlines.unpersist()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    spark = (
        SparkSession.builder.appName("flight-dws-to-ads-mysql")
        .enableHiveSupport()
        .getOrCreate()
    )
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    try:
        spark.sql("USE {}".format(args.database))
        run(spark, args)
        return 0
    except Exception:
        LOG.exception("ADS ETL failed")
        return 1
    finally:
        spark.stop()


if __name__ == "__main__":
    sys.exit(main())
