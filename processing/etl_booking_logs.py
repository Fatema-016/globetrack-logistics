# GlobeTrack Logistics - Booking Logs ETL Pipeline
# Reads raw booking JSONs from S3, cleans, transforms, writes Parquet
# Step 2 - Data Aggregation & Loading

import boto3
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
from datetime import datetime, timezone

S3_BUCKET_RAW       = "globetrack-raw-data-lake"
S3_BUCKET_PROCESSED = "globetrack-processed-data"
REGION              = "ap-south-1"
RAW_FOLDER          = "booking-logs"
PROCESSED_FOLDER    = "booking-logs-cleaned"

s3_client = boto3.client("s3", region_name=REGION)

def read_raw_booking_data():
    print("\n[1/5] Reading raw booking logs from S3...")

    paginator = s3_client.get_paginator("list_objects_v2")
    pages     = paginator.paginate(
                    Bucket = S3_BUCKET_RAW,
                    Prefix = f"{RAW_FOLDER}/"
                )

    records = []
    count   = 0
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".json"):
                response = s3_client.get_object(
                    Bucket = S3_BUCKET_RAW, Key = key
                )
                data = json.loads(
                    response["Body"].read().decode("utf-8")
                )
                records.append(data)
                count += 1

    print(f"  Read {count} raw booking records from S3")
    df = pd.DataFrame(records)
    print(f"  DataFrame shape: {df.shape}")
    return df

def clean_booking_data(df):
    print("\n[2/5] Cleaning booking log data...")
    initial_rows = len(df)

    df["booking_timestamp"]  = pd.to_datetime(
        df["booking_timestamp"], utc=True, errors="coerce"
    )
    df["estimated_delivery"] = pd.to_datetime(
        df["estimated_delivery"], utc=True, errors="coerce"
    )

    numeric_cols = [
        "cargo_weight_kg","cargo_value_inr",
        "distance_km","freight_charge_inr",
        "origin_delay_risk","origin_has_severe",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    df["delivery_status"]    = df["delivery_status"].str.upper().str.strip()
    df["origin_city"]        = df["origin_city"].str.title().str.strip()
    df["destination_city"]   = df["destination_city"].str.title().str.strip()
    df["priority"]           = df["priority"].str.upper().str.strip()
    df["cargo_type"]         = df["cargo_type"].str.title().str.strip()
    df["booking_id"]         = df["booking_id"].str.upper().str.strip()

    before = len(df)
    df     = df.drop_duplicates(subset=["booking_id"])
    if before > len(df):
        print(f"  Removed {before - len(df)} duplicate bookings")
    else:
        print(f"  No duplicate bookings found")

    df = df[df["distance_km"]        > 0]
    df = df[df["freight_charge_inr"] > 0]
    df = df.dropna(subset=["booking_id","origin_city","destination_city"])

    print(f"  Rows after cleaning: {len(df)} (started: {initial_rows})")
    return df

def engineer_features(df):
    print("\n[3/5] Engineering features...")

    # Delay flag
    df["is_delayed"] = (
        df["delivery_status"] == "DELAYED"
    ).astype(int)

    # Revenue per km
    df["revenue_per_km"] = (
        df["freight_charge_inr"] /
        df["distance_km"].replace(0, 1)
    ).round(2)

    # Cargo value category
    df["cargo_value_category"] = pd.cut(
        df["cargo_value_inr"],
        bins   = [0, 50000, 200000, float("inf")],
        labels = ["LOW","MEDIUM","HIGH"]
    ).astype(str)

    # Is express
    df["is_express"] = (df["priority"] == "EXPRESS").astype(int)

    # Is long haul
    df["is_long_haul"] = (df["distance_km"] > 500).astype(int)

    # Is heavy cargo
    df["is_heavy_cargo"] = (df["cargo_weight_kg"] > 8000).astype(int)

    # Booking hour
    df["booking_hour"] = df["booking_timestamp"].dt.hour

    # Booking day of week
    df["booking_day"] = df["booking_timestamp"].dt.day_name()

    # Weather intensity index (interaction feature)
    df["weather_distance_risk"] = (
        df["origin_delay_risk"] * df["distance_km"] / 100
    ).round(2)

    df["processed_at"] = datetime.now(timezone.utc).isoformat()

    print(f"  Added: is_delayed, revenue_per_km, cargo_value_category")
    print(f"  Added: is_express, is_long_haul, is_heavy_cargo")
    print(f"  Added: booking_hour, booking_day")
    print(f"  Added: weather_distance_risk (interaction feature)")
    return df

def validate_data(df):
    print("\n[4/5] Running data quality checks...")

    unique_pct = df["booking_id"].nunique() / len(df) * 100
    if unique_pct == 100:
        print(f"  Check 1 PASSED: All booking IDs unique")
    else:
        print(f"  Check 1 WARNING: {100-unique_pct:.1f}% duplicates")

    valid_statuses = {
        "BOOKED","IN_TRANSIT","DELIVERED","DELAYED","CANCELLED"
    }
    invalid = df[~df["delivery_status"].isin(valid_statuses)]
    if len(invalid) == 0:
        print(f"  Check 2 PASSED: All delivery statuses valid")
    else:
        print(f"  Check 2 WARNING: {len(invalid)} invalid statuses")

    negative = len(df[df["freight_charge_inr"] < 0])
    if negative == 0:
        print(f"  Check 3 PASSED: No negative freight charges")
    else:
        print(f"  Check 3 FAILED: {negative} negative charges")

    print(f"  Check 4 INFO: Status breakdown:")
    for status, count in df["delivery_status"].value_counts().items():
        print(f"    {status}: {count}")

def write_parquet_to_s3(df):
    print("\n[5/5] Writing cleaned bookings as Parquet to S3...")

    for col in ["booking_timestamp","estimated_delivery","processed_at"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    table  = pa.Table.from_pandas(df)
    buffer = BytesIO()
    pq.write_table(table, buffer, compression="snappy")
    buffer.seek(0)

    now    = datetime.now(timezone.utc)
    s3_key = (
        f"{PROCESSED_FOLDER}/"
        f"year={now.year}/month={now.month:02d}/day={now.day:02d}/"
        f"booking_logs_cleaned_{now.strftime('%H%M%S')}.parquet"
    )

    s3_client.put_object(
        Bucket      = S3_BUCKET_PROCESSED,
        Key         = s3_key,
        Body        = buffer.getvalue(),
        ContentType = "application/octet-stream",
    )

    print(f"  Parquet written to:")
    print(f"    s3://{S3_BUCKET_PROCESSED}/{s3_key}")
    print(f"  Total rows: {len(df)}")
    print(f"  Total columns: {len(df.columns)}")
    return s3_key

def run_booking_etl():
    print("=" * 55)
    print("  GlobeTrack - Booking Logs ETL STARTED")
    print("=" * 55)

    df = read_raw_booking_data()
    df = clean_booking_data(df)
    df = engineer_features(df)
    validate_data(df)
    s3_key = write_parquet_to_s3(df)

    print("\n" + "=" * 55)
    print("  BOOKING LOGS ETL COMPLETE!")
    print("=" * 55)
    return df

if __name__ == "__main__":
    run_booking_etl()