# GlobeTrack Logistics - Data Enrichment Pipeline
# Joins IoT + Booking + Weather into enriched datasets
# Step 2 - Data Aggregation & Loading

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
from datetime import datetime, timezone

S3_BUCKET_PROCESSED = "globetrack-processed-data"
S3_BUCKET_ANALYTICS = "globetrack-analytics-zone"
REGION              = "ap-south-1"

s3_client = boto3.client("s3", region_name=REGION)

CITY_COORDS = {
    "Mumbai":     (19.0760, 72.8777),
    "Pune":       (18.5204, 73.8567),
    "Nashik":     (19.9975, 73.7898),
    "Nagpur":     (21.1458, 79.0882),
    "Aurangabad": (19.8762, 75.3433),
    "Kolhapur":   (16.7050, 74.2433),
    "Goa":        (15.2993, 74.1240),
    "Solapur":    (17.6599, 75.9064),
}

def read_latest_parquet(bucket, folder):
    paginator = s3_client.get_paginator("list_objects_v2")
    pages     = paginator.paginate(
                    Bucket = bucket, Prefix = f"{folder}/"
                )
    files = []
    for page in pages:
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                files.append((obj["LastModified"], obj["Key"]))

    if not files:
        raise FileNotFoundError(f"No parquet files in {folder}/")

    latest_key = sorted(files, reverse=True)[0][1]
    print(f"  Reading: {latest_key}")

    response = s3_client.get_object(Bucket=bucket, Key=latest_key)
    buffer   = BytesIO(response["Body"].read())
    return pd.read_parquet(buffer)

def load_all_datasets():
    print("\n[1/4] Loading cleaned datasets...")
    df_iot      = read_latest_parquet(
                      S3_BUCKET_PROCESSED, "iot-sensor-cleaned"
                  )
    df_bookings = read_latest_parquet(
                      S3_BUCKET_PROCESSED, "booking-logs-cleaned"
                  )
    df_weather  = read_latest_parquet(
                      S3_BUCKET_PROCESSED, "weather-data-cleaned"
                  )
    print(f"  IoT:      {df_iot.shape}")
    print(f"  Bookings: {df_bookings.shape}")
    print(f"  Weather:  {df_weather.shape}")
    return df_iot, df_bookings, df_weather

def enrich_iot_with_weather(df_iot, df_weather):
    print("\n[2/4] Enriching IoT data with weather...")

    def nearest_city(lat, lon):
        min_dist = float("inf")
        nearest  = "Mumbai"
        for city, (clat, clon) in CITY_COORDS.items():
            dist = ((lat - clat)**2 + (lon - clon)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest  = city
        return nearest

    df_iot["nearest_city"] = df_iot.apply(
        lambda r: nearest_city(
            r["gps_latitude"], r["gps_longitude"]
        ), axis=1
    )

    weather_summary = df_weather.groupby("city").agg(
        avg_temp_C          = ("temperature_C",    "mean"),
        avg_humidity_pct    = ("humidity_pct",     "mean"),
        avg_delay_risk      = ("delay_risk_score", "mean"),
        avg_congestion      = ("traffic_congestion","mean"),
        dominant_condition  = ("weather_condition", "first"),
        avg_visibility_km   = ("visibility_km",    "mean"),
        has_severe_weather  = ("is_severe_weather", "max"),
        travel_advisory     = ("travel_advisory",   "first"),
        combined_risk       = ("combined_risk_score","mean"),
    ).reset_index()

    weather_summary.columns = [
        "nearest_city","avg_temp_C","avg_humidity_pct",
        "avg_delay_risk","avg_congestion","weather_condition",
        "avg_visibility_km","has_severe_weather",
        "travel_advisory","combined_risk_score",
    ]

    df_enriched = df_iot.merge(
        weather_summary, on="nearest_city", how="left"
    )

    print(f"  IoT records enriched: {len(df_enriched)}")
    print(f"  New columns: avg_delay_risk, avg_congestion,")
    print(f"    weather_condition, travel_advisory, combined_risk_score")
    return df_enriched

def enrich_bookings_with_weather(df_bookings, df_weather):
    print("\n[3/4] Enriching bookings with weather...")

    weather_origin = df_weather.groupby("city").agg(
        origin_weather       = ("weather_condition",  "first"),
        origin_delay_risk_w  = ("delay_risk_score",   "mean"),
        origin_visibility_km = ("visibility_km",      "mean"),
        origin_congestion    = ("traffic_congestion", "mean"),
        origin_has_severe    = ("is_severe_weather",  "max"),
        origin_combined_risk = ("combined_risk_score","mean"),
    ).reset_index()

    weather_origin.columns = [
        "origin_city","origin_weather_w",
        "origin_delay_risk_w","origin_visibility_km",
        "origin_congestion","origin_has_severe_w",
        "origin_combined_risk",
    ]

    df_enriched = df_bookings.merge(
        weather_origin, on="origin_city", how="left"
    )

    for col in ["origin_weather_w","origin_delay_risk_w",
                "origin_visibility_km","origin_congestion",
                "origin_combined_risk"]:
        if col in df_enriched.columns:
            df_enriched[col] = df_enriched[col].fillna(
                df_enriched[col].median()
                if df_enriched[col].dtype in ["float64","int64"]
                else "Unknown"
            )

    print(f"  Booking records enriched: {len(df_enriched)}")
    print(f"  New columns: origin_weather_w, origin_delay_risk_w,")
    print(f"    origin_congestion, origin_combined_risk")
    return df_enriched

def save_enriched_datasets(df_iot_enriched, df_bookings_enriched):
    print("\n[4/4] Saving enriched datasets to analytics zone...")

    now = datetime.now(timezone.utc)

    def save_parquet(df, name):
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str)

        table  = pa.Table.from_pandas(df)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)

        s3_key = (
            f"{name}/"
            f"year={now.year}/month={now.month:02d}/"
            f"day={now.day:02d}/"
            f"{name}_{now.strftime('%H%M%S')}.parquet"
        )
        s3_client.put_object(
            Bucket      = S3_BUCKET_ANALYTICS,
            Key         = s3_key,
            Body        = buffer.getvalue(),
            ContentType = "application/octet-stream",
        )
        print(f"  Saved: s3://{S3_BUCKET_ANALYTICS}/{s3_key}")
        print(f"    Rows: {len(df)}  Columns: {len(df.columns)}")

    save_parquet(df_iot_enriched,      "iot-enriched")
    save_parquet(df_bookings_enriched, "bookings-enriched")

def run_enrichment():
    print("=" * 55)
    print("  GlobeTrack - Data Enrichment Pipeline STARTED")
    print("=" * 55)

    df_iot, df_bookings, df_weather = load_all_datasets()
    df_iot_enriched      = enrich_iot_with_weather(
                               df_iot, df_weather
                           )
    df_bookings_enriched = enrich_bookings_with_weather(
                               df_bookings, df_weather
                           )
    save_enriched_datasets(df_iot_enriched, df_bookings_enriched)

    print("\n" + "=" * 55)
    print("  ENRICHMENT PIPELINE COMPLETE!")
    print(f"  IoT enriched:      {df_iot_enriched.shape}")
    print(f"  Bookings enriched: {df_bookings_enriched.shape}")
    print("=" * 55)
    return df_iot_enriched, df_bookings_enriched

if __name__ == "__main__":
    run_enrichment()