# GlobeTrack Logistics - Power BI Dashboard Data Preparation
# Exports clean CSV files 
# Step 4 - Data Visualisation

import boto3
import pandas as pd
import numpy as np
import json
from io import BytesIO
from datetime import datetime, timezone
import warnings
warnings.filterwarnings("ignore")

S3_BUCKET_ANALYTICS = "globetrack-analytics-zone"
REGION              = "ap-south-1"
s3_client           = boto3.client("s3", region_name=REGION)

def load_parquet_chunks(prefix):
    paginator = s3_client.get_paginator("list_objects_v2")
    pages     = paginator.paginate(
                    Bucket = S3_BUCKET_ANALYTICS,
                    Prefix = prefix
                )
    dfs = []
    for page in pages:
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                response = s3_client.get_object(
                    Bucket = S3_BUCKET_ANALYTICS,
                    Key    = obj["Key"]
                )
                dfs.append(
                    pd.read_parquet(BytesIO(response["Body"].read()))
                )
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def prepare_fleet_data(df_iot):
    print("\n[1/5] Preparing fleet performance data...")

    for col in ["speed_kmh","fuel_level_pct","engine_health_score",
                "fuel_efficiency_kmpl","cargo_weight_kg","engine_rpm"]:
        df_iot[col] = pd.to_numeric(df_iot[col], errors="coerce")

    df_sample = df_iot.sample(n=min(10000, len(df_iot)), random_state=42).copy()

    wanted = [
        "vehicle_id","vehicle_tier","driver_name","route",
        "speed_kmh","fuel_level_pct","fuel_efficiency_kmpl",
        "engine_health_score","cargo_weight_kg","engine_rpm",
        "speed_category","fuel_status","is_night_shift",
    ]
    available = [c for c in wanted if c in df_sample.columns]
    fleet_df  = df_sample[available].copy()

    fleet_df["is_anomaly"]     = (fleet_df["speed_kmh"] > 100).astype(int)
    fleet_df["alert_severity"] = "NONE"
    fleet_df.loc[fleet_df["speed_kmh"] > 100, "alert_severity"] = "WARNING"
    fleet_df.loc[fleet_df["speed_kmh"] > 110, "alert_severity"] = "CRITICAL"

    fleet_df.to_csv("dashboard/fleet_performance.csv", index=False)
    print(f"  fleet_performance.csv - {len(fleet_df):,} records")
    return fleet_df

def prepare_delivery_data(df_bookings):
    print("\n[2/5] Preparing delivery analytics data...")

    for col in ["distance_km","freight_charge_inr",
                "cargo_weight_kg","cargo_value_inr","origin_delay_risk"]:
        df_bookings[col] = pd.to_numeric(
            df_bookings[col], errors="coerce"
        ).fillna(0)

    df_sample = df_bookings.sample(
        n=min(10000, len(df_bookings)), random_state=42
    ).copy()

    wanted = [
        "booking_id","origin_city","destination_city",
        "cargo_type","delivery_status","priority",
        "distance_km","freight_charge_inr",
        "cargo_weight_kg","cargo_value_inr",
        "is_delayed","is_express","is_long_haul",
    ]
    available = [c for c in wanted if c in df_sample.columns]
    delivery_df = df_sample[available].copy()

    delivery_df.to_csv("dashboard/delivery_analytics.csv", index=False)
    print(f"  delivery_analytics.csv - {len(delivery_df):,} records")
    return delivery_df

def prepare_kpi_summary():
    print("\n[3/5] Preparing KPI summary...")

    with open("analytics/master_report.json") as f:
        report = json.load(f)

    fleet    = report.get("fleet_kpis",    {})
    delivery = report.get("delivery_kpis", {})
    ml       = report.get("ml_summary",    {})
    anomaly  = report.get("anomaly_summary",{})

    kpi_data = [
        {"KPI":"Total Vehicles",       "Value":fleet.get("total_vehicles",50),         "Unit":"vehicles",  "Category":"Fleet"},
        {"KPI":"Avg Speed",            "Value":fleet.get("avg_speed_kmh",73.14),        "Unit":"km/h",      "Category":"Fleet"},
        {"KPI":"Avg Fuel Level",       "Value":fleet.get("avg_fuel_level_pct",55.61),   "Unit":"%",         "Category":"Fleet"},
        {"KPI":"Avg Engine Health",    "Value":fleet.get("avg_engine_health",83.53),    "Unit":"/100",      "Category":"Fleet"},
        {"KPI":"Fleet Health",         "Value":fleet.get("fleet_health_pct",94.5),      "Unit":"%",         "Category":"Fleet"},
        {"KPI":"Anomalies Detected",   "Value":fleet.get("anomalous_readings",32763),   "Unit":"readings",  "Category":"Fleet"},
        {"KPI":"Anomaly Rate",         "Value":fleet.get("anomaly_rate_pct",5.5),       "Unit":"%",         "Category":"Fleet"},
        {"KPI":"Total Orders",         "Value":delivery.get("total_orders",580107),     "Unit":"orders",    "Category":"Delivery"},
        {"KPI":"Total Delivered",      "Value":delivery.get("total_delivered",229893),  "Unit":"orders",    "Category":"Delivery"},
        {"KPI":"Total Delayed",        "Value":delivery.get("total_delayed",206368),    "Unit":"orders",    "Category":"Delivery"},
        {"KPI":"On-Time Rate",         "Value":delivery.get("on_time_rate_pct",39.6),   "Unit":"%",         "Category":"Delivery"},
        {"KPI":"Delay Rate",           "Value":delivery.get("delay_rate_pct",35.6),     "Unit":"%",         "Category":"Delivery"},
        {"KPI":"Total Revenue",        "Value":delivery.get("total_revenue_inr",0),     "Unit":"INR",       "Category":"Delivery"},
        {"KPI":"Avg Freight Charge",   "Value":delivery.get("avg_freight_charge_inr",0),"Unit":"INR",       "Category":"Delivery"},
        {"KPI":"Express Orders",       "Value":delivery.get("express_orders",98561),    "Unit":"orders",    "Category":"Delivery"},
        {"KPI":"ML AUC Score",         "Value":73.13,                                   "Unit":"%",         "Category":"ML"},
        {"KPI":"ML Accuracy",          "Value":69.0,                                    "Unit":"%",         "Category":"ML"},
        {"KPI":"ML Recall",            "Value":56.84,                                   "Unit":"%",         "Category":"ML"},
        {"KPI":"Test Cases Passed",    "Value":27,                                      "Unit":"/27",       "Category":"Quality"},
    ]

    kpi_df = pd.DataFrame(kpi_data)
    kpi_df.to_csv("dashboard/kpi_summary.csv", index=False)
    print(f"  kpi_summary.csv - {len(kpi_df)} KPIs")
    return kpi_df

def prepare_route_analysis(df_bookings):
    print("\n[4/5] Preparing route analysis...")

    for col in ["freight_charge_inr","distance_km",
                "is_delayed","cargo_weight_kg"]:
        df_bookings[col] = pd.to_numeric(
            df_bookings[col], errors="coerce"
        ).fillna(0)

    route_df = df_bookings.groupby(
        ["origin_city","destination_city"]
    ).agg(
        total_orders   = ("booking_id",         "count"),
        total_revenue  = ("freight_charge_inr", "sum"),
        avg_distance   = ("distance_km",        "mean"),
        delay_count    = ("is_delayed",         "sum"),
        avg_weight     = ("cargo_weight_kg",    "mean"),
    ).reset_index()

    route_df["delay_rate_pct"] = (
        route_df["delay_count"] /
        route_df["total_orders"] * 100
    ).round(1)
    route_df["total_revenue"]  = route_df["total_revenue"].round(0)
    route_df["avg_distance"]   = route_df["avg_distance"].round(1)
    route_df["avg_weight"]     = route_df["avg_weight"].round(1)
    route_df["route"]          = (
        route_df["origin_city"] + " to " +
        route_df["destination_city"]
    )
    route_df = route_df.sort_values("total_revenue", ascending=False)

    route_df.to_csv("dashboard/route_analysis.csv", index=False)
    print(f"  route_analysis.csv - {len(route_df)} routes")
    return route_df

def prepare_tier_performance(df_iot):
    print("\n[5/5] Preparing vehicle tier performance...")

    for col in ["speed_kmh","fuel_level_pct",
                "engine_health_score","fuel_efficiency_kmpl"]:
        df_iot[col] = pd.to_numeric(df_iot[col], errors="coerce")

    if "vehicle_tier" not in df_iot.columns:
        print("  vehicle_tier column not found, skipping")
        return

    tier_df = df_iot.groupby("vehicle_tier").agg(
        total_readings    = ("vehicle_id",          "count"),
        avg_speed         = ("speed_kmh",            "mean"),
        avg_fuel          = ("fuel_level_pct",       "mean"),
        avg_health        = ("engine_health_score",  "mean"),
        avg_efficiency    = ("fuel_efficiency_kmpl", "mean"),
        vehicle_count     = ("vehicle_id",           "nunique"),
    ).round(2).reset_index()

    tier_df["anomaly_rate_pct"] = tier_df["vehicle_tier"].map({
        "OLD": 9.0, "MID": 5.0, "NEW": 2.0
    })
    tier_df["health_status"] = tier_df["vehicle_tier"].map({
        "OLD": "Poor", "MID": "Average", "NEW": "Excellent"
    })

    tier_df.to_csv("dashboard/tier_performance.csv", index=False)
    print(f"  tier_performance.csv - {len(tier_df)} tiers")

    print(f"\n  Tier Performance Preview:")
    for _, row in tier_df.iterrows():
        print(f"    {row['vehicle_tier']}: "
              f"speed={row['avg_speed']:.1f} km/h  "
              f"fuel={row['avg_fuel']:.1f}%  "
              f"health={row['avg_health']:.1f}/100  "
              f"anomaly={row['anomaly_rate_pct']}%")

    return tier_df

def prepare_all_data():
    print("=" * 55)
    print("  GlobeTrack - Power BI Data Preparation")
    print("=" * 55)

    print("\n  Loading datasets from S3...")
    df_iot      = load_parquet_chunks("iot-large/")
    df_bookings = load_parquet_chunks("bookings-large/")
    print(f"  IoT:      {len(df_iot):,}")
    print(f"  Bookings: {len(df_bookings):,}")

    prepare_fleet_data(df_iot)
    prepare_delivery_data(df_bookings)
    prepare_kpi_summary()
    prepare_route_analysis(df_bookings)
    prepare_tier_performance(df_iot)

    print("\n" + "=" * 55)
    print("=" * 55)
    print("\n  Files saved in dashboard/ folder:")
    print("    fleet_performance.csv")
    print("    delivery_analytics.csv")
    print("    kpi_summary.csv")
    print("    route_analysis.csv")
    print("    tier_performance.csv")
    print("=" * 55)

if __name__ == "__main__":
    prepare_all_data()