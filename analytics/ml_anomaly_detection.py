# GlobeTrack Logistics - IoT Anomaly Detection
# Isolation Forest + Local Outlier Factor
# Step 3 - Analytics & Machine Learning Integration

import boto3
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from io import BytesIO
from datetime import datetime, timezone
import json
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble      import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors     import LocalOutlierFactor

S3_BUCKET_ANALYTICS = "globetrack-analytics-zone"
REGION              = "ap-south-1"
s3_client           = boto3.client("s3", region_name=REGION)

def load_large_iot_data():
    print("\n[1/5] Loading large IoT dataset from S3...")

    paginator = s3_client.get_paginator("list_objects_v2")
    pages     = paginator.paginate(
                    Bucket = S3_BUCKET_ANALYTICS,
                    Prefix = "iot-large/"
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

    df = pd.concat(dfs, ignore_index=True)
    print(f"  Loaded {len(df):,} IoT records")
    return df

def prepare_features(df):
    print("\n[2/5] Preparing sensor features...")

    sensor_cols = [
        "speed_kmh",
        "fuel_level_pct",
        "engine_rpm",
        "battery_voltage",
        "tyre_pressure_psi",
        "cargo_weight_kg",
        "engine_health_score",
        "fuel_efficiency_kmpl",
    ]

    available = [c for c in sensor_cols if c in df.columns]
    print(f"  Sensor features: {available}")

    for col in available:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    X_full   = df[available].copy()
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X_full)

    print(f"  Full dataset: {len(df):,} records")
    print(f"  LOF sample:   50,000 records")

    return X_scaled, available, df

def detect_anomalies(X_scaled, df):
    print("\n[3/5] Running tier-aware anomaly detection...")

    sensor_cols = [
        "speed_kmh","fuel_level_pct","engine_rpm",
        "battery_voltage","tyre_pressure_psi",
        "cargo_weight_kg","engine_health_score",
        "fuel_efficiency_kmpl",
    ]
    available = [c for c in sensor_cols if c in df.columns]

    df["iso_forest_anomaly"] = 0
    df["iso_forest_score"]   = 0.0
    df["lof_anomaly"]        = 0

    TIER_CONTAMINATION = {
        "OLD": 0.09,
        "MID": 0.05,
        "NEW": 0.02,
    }

    tiers = df["vehicle_tier"].unique() \
            if "vehicle_tier" in df.columns \
            else ["ALL"]

    for tier in tiers:
        contamination = TIER_CONTAMINATION.get(tier, 0.05)
        if tier == "ALL":
            tier_mask = pd.Series([True]*len(df), index=df.index)
        else:
            tier_mask = df["vehicle_tier"] == tier

        tier_idx = df[tier_mask].index
        tier_X   = df.loc[tier_mask, available].copy()

        for col in available:
            tier_X[col] = pd.to_numeric(
                tier_X[col], errors="coerce"
            ).fillna(tier_X[col].median())

        scaler_t  = StandardScaler()
        tier_Xsc  = scaler_t.fit_transform(tier_X)
        tier_count= len(tier_X)

        print(f"\n  Tier {tier} (contamination={contamination}): "
              f"{tier_count:,} records")
        # Isolation Forest per tier
        iso = IsolationForest(
            contamination = contamination,
            random_state  = 42,
            n_estimators  = 100,
            n_jobs        = -1,
        )
        iso_preds  = iso.fit_predict(tier_Xsc)
        iso_scores = iso.decision_function(tier_Xsc)

        df.loc[tier_idx, "iso_forest_anomaly"] = (
            iso_preds == -1
        ).astype(int)
        df.loc[tier_idx, "iso_forest_score"] = iso_scores.round(4)

        iso_n = (iso_preds == -1).sum()
        print(f"    Isolation Forest: {iso_n:,} anomalies "
              f"({iso_n/tier_count*100:.1f}%)")

        # LOF on sample per tier
        sample_size = min(10000, tier_count)
        sample_idx  = np.random.choice(
            tier_count, size=sample_size, replace=False
        )
        X_sample    = tier_Xsc[sample_idx]

        lof = LocalOutlierFactor(
            n_neighbors   = 20,
            contamination = contamination,
            n_jobs        = -1,
        )
        lof_preds = lof.fit_predict(X_sample)
        lof_n     = (lof_preds == -1).sum()

        lof_anom_idx = tier_idx[sample_idx[lof_preds == -1]]
        df.loc[lof_anom_idx, "lof_anomaly"] = 1

        print(f"    LOF: {lof_n:,} anomalies in sample")

    df["confirmed_anomaly"] = df["iso_forest_anomaly"]
    df["anomaly_severity"]  = "NORMAL"
    df.loc[
        df["confirmed_anomaly"] == 1, "anomaly_severity"
    ] = "ANOMALY"

    confirmed = df["confirmed_anomaly"].sum()
    print(f"\n  Total confirmed anomalies: {confirmed:,} "
          f"({confirmed/len(df)*100:.1f}%)")

    return df

def analyse_anomalies(df):
    print("\n[4/5] Analysing anomalies...")

    total     = len(df)
    anomalies = df[df["confirmed_anomaly"] == 1]

    print(f"\n  Fleet Summary:")
    print(f"    Total records:  {total:,}")
    print(f"    Normal:         "
          f"{(df['anomaly_severity']=='NORMAL').sum():,} "
          f"({(df['anomaly_severity']=='NORMAL').sum()/total*100:.1f}%)")
    print(f"    Anomalous:      {len(anomalies):,} "
          f"({len(anomalies)/total*100:.1f}%)")

    # Top anomalous vehicles
    if "vehicle_id" in df.columns:
        top_v = df[
            df["confirmed_anomaly"] == 1
        ]["vehicle_id"].value_counts().head(10)

        print(f"\n  Top 10 vehicles with most anomalous readings:")
        for vehicle, count in top_v.items():
            total_v = df[df["vehicle_id"]==vehicle].shape[0]
            pct     = count / total_v * 100
            print(f"    {vehicle}: {count:,} anomalous "
                  f"({pct:.1f}% of its readings)")

    # Tier breakdown
    if "vehicle_tier" in df.columns:
        print(f"\n  Anomaly rate by vehicle tier:")
        for tier in ["OLD","MID","NEW"]:
            tier_df    = df[df["vehicle_tier"] == tier]
            tier_anom  = tier_df["confirmed_anomaly"].sum()
            tier_rate  = tier_anom / len(tier_df) * 100 if len(tier_df) > 0 else 0
            print(f"    {tier}: {tier_anom:,} anomalies "
                  f"({tier_rate:.1f}%)")

    # Sensor comparison
    sensor_cols = [
        "speed_kmh","fuel_level_pct",
        "engine_rpm","battery_voltage"
    ]
    print(f"\n  Anomalous vs Normal sensor values:")
    for col in sensor_cols:
        if col in df.columns:
            norm_avg  = df[df["confirmed_anomaly"]==0][col].mean()
            anom_avg  = df[df["confirmed_anomaly"]==1][col].mean()
            print(f"    {col:<25} "
                  f"Normal: {norm_avg:>7.2f}  "
                  f"Anomaly: {anom_avg:>7.2f}")

    return df

def save_results(df):
    print("\n[5/5] Saving anomaly detection results...")

    now   = datetime.now(timezone.utc)
    total = len(df)

    anomalous_vehicles = []
    if "vehicle_id" in df.columns:
        top_v = df[
            df["confirmed_anomaly"] == 1
        ]["vehicle_id"].value_counts().head(10)

        for vehicle, count in top_v.items():
            tier = df[df["vehicle_id"]==vehicle]["vehicle_tier"].iloc[0] \
                   if "vehicle_tier" in df.columns else "UNKNOWN"
            anomalous_vehicles.append({
                "vehicle_id":       vehicle,
                "vehicle_tier":     str(tier),
                "anomaly_count":    int(count),
                "anomaly_rate_pct": round(
                    count /
                    df[df["vehicle_id"]==vehicle].shape[0] * 100, 1
                ),
                "avg_speed":        round(float(
                    df[df["vehicle_id"]==vehicle]["speed_kmh"].mean()
                ), 1),
                "avg_fuel_pct":     round(float(
                    df[df["vehicle_id"]==vehicle]["fuel_level_pct"].mean()
                ), 1),
            })

    # Tier anomaly rates
    tier_breakdown = {}
    if "vehicle_tier" in df.columns:
        for tier in ["OLD","MID","NEW"]:
            tier_df   = df[df["vehicle_tier"] == tier]
            tier_anom = int(tier_df["confirmed_anomaly"].sum())
            tier_rate = round(
                tier_anom / len(tier_df) * 100
                if len(tier_df) > 0 else 0, 1
            )
            tier_breakdown[tier] = {
                "anomaly_count": tier_anom,
                "anomaly_rate_pct": tier_rate,
            }

    report = {
        "report_title":  "GlobeTrack IoT Anomaly Detection Report",
        "generated_at":  now.isoformat(),
        "dataset_size":  f"{total:,} IoT sensor records",
        "models_used":   [
            "Isolation Forest (full 600K dataset)",
            "Local Outlier Factor (50K sample)",
        ],
        "summary": {
            "total_records":  total,
            "normal":         int(
                (df["anomaly_severity"]=="NORMAL").sum()
            ),
            "anomaly":        int(
                (df["confirmed_anomaly"]==1).sum()
            ),
        },
        "fleet_health": {
            "healthy_pct":  round(
                (df["anomaly_severity"]=="NORMAL").sum()
                / total * 100, 1
            ),
            "anomaly_pct":  round(
                (df["confirmed_anomaly"]==1).sum()
                / total * 100, 1
            ),
        },
        "tier_breakdown":      tier_breakdown,
        "anomalous_vehicles":  anomalous_vehicles,
    }

    # Save to S3
    s3_key = (
        f"anomaly-reports/"
        f"globetrack_anomaly_{now.strftime('%Y%m%d_%H%M%S')}.json"
    )
    s3_client.put_object(
        Bucket      = S3_BUCKET_ANALYTICS,
        Key         = s3_key,
        Body        = json.dumps(report, indent=2, default=str),
        ContentType = "application/json",
    )

    # Save locally
    local_path = "analytics/anomaly_report.json"
    with open(local_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"  Saved to S3:   {s3_key}")
    print(f"  Saved locally: {local_path}")
    print(f"\n  Fleet Health Summary:")
    print(f"    Total:     {total:,}")
    print(f"    Normal:    {report['summary']['normal']:,}")
    print(f"    Anomalous: {report['summary']['anomaly']:,}")
    print(f"    Health:    {report['fleet_health']['healthy_pct']}%")

    if tier_breakdown:
        print(f"\n  Anomaly rate by tier:")
        for tier, data in tier_breakdown.items():
            print(f"    {tier}: {data['anomaly_rate_pct']}%")

    return report

def run_anomaly_detection():
    print("=" * 55)
    print("  GlobeTrack - IoT Anomaly Detection")
    print("  Dataset: 600,000 IoT sensor records")
    print("=" * 55)

    df                     = load_large_iot_data()
    X_scaled, features, df = prepare_features(df)
    df                     = detect_anomalies(X_scaled, df)
    df                     = analyse_anomalies(df)
    report                 = save_results(df)

    print("\n" + "=" * 55)
    print("  ANOMALY DETECTION COMPLETE!")
    print("=" * 55)

    return df, report

if __name__ == "__main__":
    run_anomaly_detection()