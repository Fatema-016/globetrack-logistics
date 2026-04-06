# GlobeTrack Logistics - Large Scale ETL Pipeline
# Processes 600,000 records from large dataset chunks
# Step 2 - Data Aggregation & Loading

import boto3
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
from datetime import datetime, timezone
import warnings
warnings.filterwarnings("ignore")

S3_BUCKET_RAW       = "globetrack-raw-data-lake"
S3_BUCKET_ANALYTICS = "globetrack-analytics-zone"
REGION              = "ap-south-1"

s3_client = boto3.client("s3", region_name=REGION)

WEATHER_RISK_MAP = {
    "Clear":5,"Partly Cloudy":15,"Overcast":25,
    "Light Rain":40,"Heavy Rain":70,"Fog":65,"Thunderstorm":85,
}

def read_large_csv_chunks(folder, max_chunks=60):
    print(f"  Reading chunks from {folder}/large-dataset/...")

    paginator = s3_client.get_paginator("list_objects_v2")
    pages     = paginator.paginate(
                    Bucket = S3_BUCKET_RAW,
                    Prefix = f"{folder}/large-dataset/"
                )

    keys = []
    for page in pages:
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".csv"):
                keys.append(obj["Key"])

    keys  = sorted(keys)[:max_chunks]
    print(f"  Found {len(keys)} CSV chunks")

    dfs = []
    for i, key in enumerate(keys, 1):
        response = s3_client.get_object(
            Bucket = S3_BUCKET_RAW, Key = key
        )
        df = pd.read_csv(BytesIO(response["Body"].read()))
        dfs.append(df)
        if i % 10 == 0:
            print(f"  Read {i}/{len(keys)} chunks...")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"  Total rows loaded: {len(combined):,}")
    return combined

def process_large_bookings(df):
    print("\n[2/5] Processing large booking dataset...")

    numeric_cols = [
        "cargo_weight_kg","cargo_value_inr",
        "distance_km","freight_charge_inr","origin_delay_risk",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    df["delivery_status"]  = df["delivery_status"].str.upper().str.strip()
    df["origin_city"]      = df["origin_city"].str.title().str.strip()
    df["destination_city"] = df["destination_city"].str.title().str.strip()
    df["priority"]         = df["priority"].str.upper().str.strip()
    df["cargo_type"]       = df["cargo_type"].str.title().str.strip()

    before = len(df)
    df     = df.drop_duplicates(subset=["booking_id"])
    print(f"  Removed {before - len(df):,} duplicate booking IDs")

    # Feature engineering
    df["is_delayed"]     = (df["delivery_status"] == "DELAYED").astype(int)
    df["is_express"]     = (df["priority"] == "EXPRESS").astype(int)
    df["is_long_haul"]   = (df["distance_km"] > 500).astype(int)
    df["is_heavy_cargo"] = (df["cargo_weight_kg"] > 8000).astype(int)

    df["revenue_per_km"] = (
        df["freight_charge_inr"] /
        df["distance_km"].replace(0, 1)
    ).round(2)

    # KEY interaction feature for ML
    df["weather_distance_risk"] = (
        df["origin_delay_risk"] * df["distance_km"] / 100
    ).round(2)

    # Cargo value category
    df["cargo_value_category"] = pd.cut(
        df["cargo_value_inr"],
        bins   = [0, 50000, 200000, float("inf")],
        labels = ["LOW","MEDIUM","HIGH"]
    ).astype(str)

    df["processed_at"] = datetime.now(timezone.utc).isoformat()

    print(f"  Records after dedup:  {len(df):,}")
    print(f"  Delayed orders:       "
          f"{df['is_delayed'].sum():,} "
          f"({df['is_delayed'].mean()*100:.1f}%)")
    print(f"  Express orders:       {df['is_express'].sum():,}")

    return df

def process_large_iot(df):
    print("\n[3/5] Processing large IoT dataset...")

    numeric_cols = [
        "speed_kmh","fuel_level_pct","fuel_consumed_L",
        "engine_temp_C","engine_rpm","battery_voltage",
        "tyre_pressure_psi","cargo_weight_kg",
        "route_distance_km","hour_of_day","is_night_shift",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    # Feature engineering
    df["fuel_efficiency_kmpl"] = (
        df["speed_kmh"] /
        df["fuel_consumed_L"].replace(0, 0.1)
    ).round(2)

    df["engine_health_score"] = (
        100
        - ((df["engine_temp_C"] - 70) / 60 * 35)
        - ((df["engine_rpm"]    - 700) / 4300 * 25)
        + ((df["battery_voltage"] - 11.5) / 3.3 * 10)
    ).clip(0, 100).round(1)

    df["speed_category"] = pd.cut(
        df["speed_kmh"],
        bins   = [-1, 0, 30, 60, 90, 200],
        labels = ["STOPPED","SLOW","MODERATE","FAST","OVERSPEEDING"]
    ).astype(str)

    df["fuel_status"] = pd.cut(
        df["fuel_level_pct"],
        bins   = [-1, 20, 50, 101],
        labels = ["CRITICAL","LOW","NORMAL"]
    ).astype(str)

    df["is_old_truck"] = (
        df["vehicle_tier"] == "OLD"
    ).astype(int) if "vehicle_tier" in df.columns else 0

    df["processed_at"] = datetime.now(timezone.utc).isoformat()

    print(f"  IoT records processed: {len(df):,}")
    print(f"  Avg speed:             {df['speed_kmh'].mean():.2f} km/h")
    print(f"  Avg fuel level:        {df['fuel_level_pct'].mean():.2f}%")
    print(f"  Avg engine health:     {df['engine_health_score'].mean():.2f}/100")

    # Show tier breakdown if available
    if "vehicle_tier" in df.columns:
        print(f"  Vehicle tier breakdown:")
        for tier, count in df["vehicle_tier"].value_counts().items():
            print(f"    {tier}: {count:,}")

    return df

def save_large_parquet(df, name, chunk_size=100000):
    print(f"\n[4/5] Saving {name} ({len(df):,} rows) to S3...")

    now         = datetime.now(timezone.utc)
    total_saved = 0
    chunk_num   = 0

    for start in range(0, len(df), chunk_size):
        chunk     = df.iloc[start:start+chunk_size].copy()
        chunk_num += 1

        for col in chunk.select_dtypes(include=["object"]).columns:
            chunk[col] = chunk[col].astype(str)

        table  = pa.Table.from_pandas(chunk)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)

        s3_key = (
            f"{name}-large/"
            f"year={now.year}/month={now.month:02d}/"
            f"{name}_chunk_{chunk_num:03d}.parquet"
        )
        s3_client.put_object(
            Bucket      = S3_BUCKET_ANALYTICS,
            Key         = s3_key,
            Body        = buffer.getvalue(),
            ContentType = "application/octet-stream",
        )
        total_saved += len(chunk)
        print(f"  Chunk {chunk_num}: {len(chunk):,} rows saved")

    print(f"  Total saved: {total_saved:,} rows in {chunk_num} files")
    return name

def print_summary(df_bookings, df_iot):
    print("\n[5/5] Large Scale ETL Summary...")
    print("\n" + "=" * 55)
    print("  LARGE SCALE ETL COMPLETE!")
    print("=" * 55)
    print(f"  Bookings processed:  {len(df_bookings):,}")
    print(f"  IoT processed:       {len(df_iot):,}")
    print(f"\n  Booking status breakdown:")
    for status, count in df_bookings["delivery_status"].value_counts().items():
        pct = count / len(df_bookings) * 100
        print(f"    {status:<15} {count:>8,}  ({pct:.1f}%)")
    print(f"\n  Data saved to:")
    print(f"    s3://{S3_BUCKET_ANALYTICS}/bookings-large/")
    print(f"    s3://{S3_BUCKET_ANALYTICS}/iot-large/")
    print("=" * 55)

def run_large_scale_etl():
    print("=" * 55)
    print("  GlobeTrack - Large Scale ETL STARTED")
    print("  Processing 600,000 records per dataset")
    print("=" * 55)

    print("\n[1/5] Reading large booking dataset from S3...")
    df_bookings = read_large_csv_chunks("booking-logs")
    df_bookings = process_large_bookings(df_bookings)
    save_large_parquet(df_bookings, "bookings")

    print("\n[1/5] Reading large IoT dataset from S3...")
    df_iot = read_large_csv_chunks("iot-sensor-data")
    df_iot = process_large_iot(df_iot)
    save_large_parquet(df_iot, "iot")

    print_summary(df_bookings, df_iot)
    return df_bookings, df_iot

if __name__ == "__main__":
    run_large_scale_etl()