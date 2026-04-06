# GlobeTrack Logistics - IoT Sensor ETL Pipeline
# Reads raw JSON from S3, cleans, transforms, writes Parquet
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
RAW_FOLDER          = "iot-sensor-data"
PROCESSED_FOLDER    = "iot-sensor-cleaned"

s3_client = boto3.client("s3", region_name=REGION)

def read_raw_iot_data():
    print("\n[1/5] Reading raw IoT sensor data from S3...")

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

    print(f"  Read {count} raw IoT records from S3")
    df = pd.DataFrame(records)
    print(f"  DataFrame shape: {df.shape}")
    return df

def clean_iot_data(df):
    print("\n[2/5] Cleaning IoT sensor data...")
    initial_rows = len(df)

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    numeric_cols = [
        "speed_kmh","fuel_level_pct","fuel_consumed_L",
        "engine_temp_C","engine_rpm","odometer_km",
        "battery_voltage","tyre_pressure_psi","cargo_weight_kg",
        "gps_latitude","gps_longitude","route_distance_km",
        "hour_of_day","is_night_shift",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    df["brake_status"]    = df["brake_status"].str.upper().fillna("UNKNOWN")
    df["ignition_status"] = df["ignition_status"].str.upper().fillna("UNKNOWN")
    df["vehicle_id"]      = df["vehicle_id"].str.upper().str.strip()
    df["vehicle_tier"]    = df["vehicle_tier"].str.upper().str.strip()

    before = len(df)
    df     = df.drop_duplicates()
    if before > len(df):
        print(f"  Removed {before - len(df)} duplicates")
    else:
        print(f"  No duplicates found")

    df = df[df["speed_kmh"]      >= 0]
    df = df[df["fuel_level_pct"].between(0, 100)]
    df = df[df["engine_temp_C"].between(50, 135)]

    print(f"  Rows after cleaning: {len(df)} (started: {initial_rows})")
    return df

def engineer_features(df):
    print("\n[3/5] Engineering features...")

    # Fuel efficiency
    df["fuel_efficiency_kmpl"] = (
        df["speed_kmh"] /
        df["fuel_consumed_L"].replace(0, 0.1)
    ).round(2)

    # Engine health score (0-100)
    df["engine_health_score"] = (
        100
        - ((df["engine_temp_C"] - 70) / 60 * 35)
        - ((df["engine_rpm"]    - 700) / 4300 * 25)
        + ((df["battery_voltage"] - 11.5) / 3.3 * 10)
    ).clip(0, 100).round(1)

    # Speed category
    df["speed_category"] = pd.cut(
        df["speed_kmh"],
        bins   = [-1, 0, 30, 60, 90, 200],
        labels = ["STOPPED","SLOW","MODERATE","FAST","OVERSPEEDING"]
    ).astype(str)

    # Fuel status
    df["fuel_status"] = pd.cut(
        df["fuel_level_pct"],
        bins   = [-1, 20, 50, 101],
        labels = ["CRITICAL","LOW","NORMAL"]
    ).astype(str)

    # Alert severity
    df["alert_severity"] = "NONE"
    df.loc[
        (df["alert_flag"].astype(str).isin(["True","true","1"])) |
        (df["brake_status"] == "WARN") |
        (df["engine_temp_C"] > 100),
        "alert_severity"
    ] = "WARNING"
    df.loc[
        (df["engine_temp_C"] > 108) |
        (df["fuel_level_pct"] < 15),
        "alert_severity"
    ] = "CRITICAL"

    # Tier performance flag
    df["is_old_truck"] = (df["vehicle_tier"] == "OLD").astype(int)

    df["processed_at"] = datetime.now(timezone.utc).isoformat()

    print(f"  Added: fuel_efficiency_kmpl, engine_health_score")
    print(f"  Added: speed_category, fuel_status, alert_severity")
    print(f"  Added: is_old_truck, processed_at")
    return df

def validate_data(df):
    print("\n[4/5] Running data quality checks...")

    null_ids = df["vehicle_id"].isnull().sum()
    if null_ids == 0:
        print(f"  Check 1 PASSED: No null vehicle IDs")
    else:
        print(f"  Check 1 FAILED: {null_ids} null vehicle IDs")

    invalid_speed = len(df[df["speed_kmh"] > 150])
    if invalid_speed == 0:
        print(f"  Check 2 PASSED: All speeds within valid range")
    else:
        print(f"  Check 2 WARNING: {invalid_speed} speeds above 150 km/h")

    tiers = df["vehicle_tier"].unique().tolist()
    if len(tiers) >= 2:
        print(f"  Check 3 PASSED: Multiple vehicle tiers present: {tiers}")
    else:
        print(f"  Check 3 WARNING: Only {tiers} tier found")

    future = df[df["timestamp"] > pd.Timestamp.now(tz="UTC")]
    if len(future) == 0:
        print(f"  Check 4 PASSED: No future timestamps")
    else:
        print(f"  Check 4 WARNING: {len(future)} future timestamps")

def write_parquet_to_s3(df):
    print("\n[5/5] Writing cleaned data as Parquet to S3...")

    df["timestamp"]    = df["timestamp"].astype(str)
    df["processed_at"] = df["processed_at"].astype(str)

    table  = pa.Table.from_pandas(df)
    buffer = BytesIO()
    pq.write_table(table, buffer, compression="snappy")
    buffer.seek(0)

    now    = datetime.now(timezone.utc)
    s3_key = (
        f"{PROCESSED_FOLDER}/"
        f"year={now.year}/month={now.month:02d}/day={now.day:02d}/"
        f"iot_sensor_cleaned_{now.strftime('%H%M%S')}.parquet"
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

def run_iot_etl():
    print("=" * 55)
    print("  GlobeTrack - IoT Sensor ETL STARTED")
    print("=" * 55)

    df = read_raw_iot_data()
    df = clean_iot_data(df)
    df = engineer_features(df)
    validate_data(df)
    s3_key = write_parquet_to_s3(df)

    print("\n" + "=" * 55)
    print("  IoT SENSOR ETL COMPLETE!")
    print("=" * 55)
    return df

if __name__ == "__main__":
    run_iot_etl()