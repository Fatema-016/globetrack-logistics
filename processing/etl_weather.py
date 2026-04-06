# GlobeTrack Logistics - Weather & Traffic ETL Pipeline
# Reads raw weather JSONs from S3, cleans, transforms, writes Parquet
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
RAW_FOLDER          = "weather-data"
PROCESSED_FOLDER    = "weather-data-cleaned"

s3_client = boto3.client("s3", region_name=REGION)

def read_raw_weather_data():
    print("\n[1/5] Reading raw weather data from S3...")

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

    print(f"  Read {count} raw weather records from S3")
    df = pd.DataFrame(records)
    print(f"  DataFrame shape: {df.shape}")
    return df

def clean_weather_data(df):
    print("\n[2/5] Cleaning weather data...")
    initial_rows = len(df)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )

    numeric_cols = [
        "temperature_C","humidity_pct","wind_speed_kmh",
        "rainfall_mm","visibility_km","delay_risk_score",
        "latitude","longitude","traffic_congestion","usd_inr_rate",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    df["city"]              = df["city"].str.title().str.strip()
    df["weather_condition"] = df["weather_condition"].str.title().str.strip()
    df["road_condition"]    = df["road_condition"].str.title().str.strip()
    df["wind_direction"]    = df["wind_direction"].str.upper().str.strip()

    df["fog_alert"]   = df["fog_alert"].astype(bool)
    df["flood_alert"] = df["flood_alert"].astype(bool)

    df["humidity_pct"]     = df["humidity_pct"].clip(0, 100)
    df["delay_risk_score"] = df["delay_risk_score"].clip(0, 100)
    df["visibility_km"]    = df["visibility_km"].clip(0, 50)
    df["traffic_congestion"] = df["traffic_congestion"].clip(0, 100)

    before = len(df)
    df     = df.drop_duplicates()
    if before > len(df):
        print(f"  Removed {before - len(df)} duplicates")
    else:
        print(f"  No duplicates found")

    print(f"  Rows after cleaning: {len(df)} (started: {initial_rows})")
    return df

def engineer_features(df):
    print("\n[3/5] Engineering features...")

    # Weather severity
    df["weather_severity"] = pd.cut(
        df["delay_risk_score"],
        bins   = [-1, 20, 50, 75, 101],
        labels = ["LOW","MODERATE","HIGH","SEVERE"]
    ).astype(str)

    # Travel advisory
    df["travel_advisory"] = "CLEAR TO TRAVEL"
    df.loc[
        df["delay_risk_score"] >= 20, "travel_advisory"
    ] = "MINOR DELAYS EXPECTED"
    df.loc[
        df["delay_risk_score"] >= 50, "travel_advisory"
    ] = "TRAVEL WITH CAUTION"
    df.loc[
        df["delay_risk_score"] >= 75, "travel_advisory"
    ] = "DO NOT TRAVEL"

    # Heat index
    df["heat_index_C"] = (
        df["temperature_C"] +
        (0.33 * (df["humidity_pct"] / 100) * 6.105) -
        (0.70 * (df["wind_speed_kmh"] / 3.6)) - 4.0
    ).round(1)

    # Severe weather flag
    df["is_severe_weather"] = (
        (df["rainfall_mm"]        > 30) |
        (df["wind_speed_kmh"]     > 50) |
        (df["visibility_km"]      < 2)  |
        (df["fog_alert"]          == True) |
        (df["flood_alert"]        == True)
    ).astype(int)

    # Combined risk score (weather + traffic)
    df["combined_risk_score"] = (
        df["delay_risk_score"] * 0.6 +
        df["traffic_congestion"] * 0.4
    ).round(1)

    df["reading_hour"] = df["timestamp"].dt.hour
    df["processed_at"] = datetime.now(timezone.utc).isoformat()

    print(f"  Added: weather_severity, travel_advisory")
    print(f"  Added: heat_index_C, is_severe_weather")
    print(f"  Added: combined_risk_score, reading_hour")
    return df

def validate_data(df):
    print("\n[4/5] Running data quality checks...")

    city_count = df["city"].nunique()
    if city_count == 8:
        print(f"  Check 1 PASSED: All 8 cities present")
    else:
        print(f"  Check 1 WARNING: Only {city_count} cities found")

    invalid_temp = len(df[~df["temperature_C"].between(5, 50)])
    if invalid_temp == 0:
        print(f"  Check 2 PASSED: All temperatures in valid range")
    else:
        print(f"  Check 2 WARNING: {invalid_temp} temps out of range")

    invalid_risk = len(df[~df["delay_risk_score"].between(0, 100)])
    if invalid_risk == 0:
        print(f"  Check 3 PASSED: All delay risk scores valid")
    else:
        print(f"  Check 3 FAILED: {invalid_risk} invalid risk scores")

    print(f"  Check 4 INFO: Weather breakdown:")
    for cond, count in df["weather_condition"].value_counts().items():
        print(f"    {cond}: {count}")

def write_parquet_to_s3(df):
    print("\n[5/5] Writing cleaned weather data as Parquet to S3...")

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
        f"weather_cleaned_{now.strftime('%H%M%S')}.parquet"
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

def run_weather_etl():
    print("=" * 55)
    print("  GlobeTrack - Weather ETL STARTED")
    print("=" * 55)

    df = read_raw_weather_data()
    df = clean_weather_data(df)
    df = engineer_features(df)
    validate_data(df)
    s3_key = write_parquet_to_s3(df)

    print("\n" + "=" * 55)
    print("  WEATHER ETL COMPLETE!")
    print("=" * 55)
    return df

if __name__ == "__main__":
    run_weather_etl()