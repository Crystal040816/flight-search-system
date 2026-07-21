"""Read and validate the delivered DWD algorithm sample."""

from pathlib import Path

import pandas as pd


SAMPLE_PATH = Path(__file__).with_name("dwd_sample.parquet")
TARGET_COLUMN = "total_fare"
IDENTIFIER_COLUMNS = ["quote_snapshot_id"]
EXPECTED_COLUMNS = [
    "quote_snapshot_id",
    "search_date",
    "flight_date",
    "days_to_departure",
    "route_id",
    "market_origin",
    "market_destination",
    "first_airline_code",
    "travel_duration_minutes",
    "elapsed_days",
    "is_basic_economy",
    "is_refundable",
    "is_non_stop",
    "seats_remaining",
    "total_distance_miles",
    "segment_count",
    "stop_count",
    "total_fare",
]


def main() -> None:
    frame = pd.read_parquet(SAMPLE_PATH, engine="pyarrow")

    assert list(frame.columns) == EXPECTED_COLUMNS, "Unexpected sample schema"
    assert len(frame) == 50_000, "Unexpected sample row count"
    assert frame["quote_snapshot_id"].notna().all(), "Null quote ID found"
    assert frame["quote_snapshot_id"].is_unique, "Duplicate quote ID found"
    assert frame[TARGET_COLUMN].notna().all(), "Null target value found"

    target = pd.to_numeric(frame[TARGET_COLUMN])
    features = frame.drop(columns=IDENTIFIER_COLUMNS + [TARGET_COLUMN])

    print(f"sample={SAMPLE_PATH}")
    print(f"shape={frame.shape}")
    print(
        "search_date_range="
        f"{frame['search_date'].min()}..{frame['search_date'].max()}"
    )
    print(f"routes={frame['route_id'].nunique()}")
    print(f"airlines={frame['first_airline_code'].nunique()}")
    print(f"target={TARGET_COLUMN}, mean={target.mean():.2f}")
    print(f"feature_columns={list(features.columns)}")
    print("null_counts:")
    print(frame.isna().sum().to_string())


if __name__ == "__main__":
    main()
