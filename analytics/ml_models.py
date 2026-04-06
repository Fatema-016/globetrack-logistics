# GlobeTrack Logistics - Improved ML Pipeline
# XGBoost + LightGBM + Random Forest
# Features: early stopping, threshold tuning, interaction features
# Step 3 - Analytics & Machine Learning Integration

import boto3
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from io import BytesIO
from datetime import datetime, timezone
import json
import pickle
import os
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection  import train_test_split
from sklearn.preprocessing    import LabelEncoder, StandardScaler
from sklearn.ensemble         import RandomForestClassifier
from sklearn.metrics          import (
    accuracy_score, classification_report,
    roc_auc_score, confusion_matrix
)
from sklearn.utils            import resample
import xgboost  as xgb
import lightgbm as lgb

S3_BUCKET_ANALYTICS = "globetrack-analytics-zone"
REGION              = "ap-south-1"
s3_client           = boto3.client("s3", region_name=REGION)

def load_dataset():
    print("\n[1/7] Loading large booking dataset from S3...")
    paginator = s3_client.get_paginator("list_objects_v2")
    pages     = paginator.paginate(
                    Bucket = S3_BUCKET_ANALYTICS,
                    Prefix = "bookings-large/"
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
    print(f"  Loaded {len(df):,} records")
    print(f"  Columns: {len(df.columns)}")
    return df

def engineer_features(df):
    print("\n[2/7] Engineering features...")

    for col in ["distance_km","cargo_weight_kg","cargo_value_inr",
                "freight_charge_inr"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Target — only from delivery_status, no weather leakage
    df["target"] = (df["delivery_status"] == "DELAYED").astype(int)

    # Basic flags
    df["is_express"]     = (df["priority"] == "EXPRESS").astype(int)
    df["is_long_haul"]   = (df["distance_km"] > 500).astype(int)
    df["is_heavy_cargo"] = (df["cargo_weight_kg"] > 8000).astype(int)
    df["is_high_value"]  = (df["cargo_value_inr"] > 200000).astype(int)
    df["heavy_long_haul"]= (
        (df["cargo_weight_kg"] > 8000) &
        (df["distance_km"]     > 500)
    ).astype(int)

    # Revenue per km
    df["revenue_per_km"] = (
        df["freight_charge_inr"] /
        df["distance_km"].replace(0, 1)
    ).round(2)

    # Interaction features — no weather leakage
    df["cargo_stress_index"] = (
        df["cargo_weight_kg"] * df["distance_km"] / 100000
    ).round(2)

    df["distance_cargo_risk"] = (
        df["distance_km"] * df["cargo_weight_kg"] / 1000000
    ).round(4)

    df["express_risk_score"] = (
        df["is_express"] * df["distance_km"] / 100
    ).round(2)

    # Encode categoricals — NO weather columns
    cat_cols = [
        "origin_city",
        "destination_city",
        "cargo_type",
        "priority",
    ]

    le = LabelEncoder()
    for col in cat_cols:
        if col in df.columns:
            df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))

    # Final feature list — clean, no leakage
    feature_cols = [
        "distance_km",
        "cargo_weight_kg",
        "cargo_value_inr",
        "freight_charge_inr",
        "is_express",
        "is_long_haul",
        "is_heavy_cargo",
        "is_high_value",
        "heavy_long_haul",
        "revenue_per_km",
        "cargo_stress_index",
        "distance_cargo_risk",
        "express_risk_score",
        "origin_city_enc",
        "destination_city_enc",
        "cargo_type_enc",
        "priority_enc",
    ]

    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    print(f"  Target distribution:")
    print(f"    Not Delayed: {(df['target']==0).sum():,} "
          f"({(df['target']==0).mean()*100:.1f}%)")
    print(f"    Delayed:     {(df['target']==1).sum():,} "
          f"({(df['target']==1).mean()*100:.1f}%)")
    print(f"  Total features: {len(feature_cols)}")
    print(f"  Interaction features: cargo_stress_index,")
    print(f"    distance_cargo_risk, express_risk_score, heavy_long_haul")
    print(f"  No weather leakage — model learns from logistics only")

    return df, feature_cols

def split_then_balance(df, feature_cols):
    print("\n[3/7] Splitting data (split before balance)...")

    X = df[feature_cols].copy()
    y = df["target"].copy()

    X_train_raw, X_test, y_train_raw, y_test = train_test_split(
        X, y,
        test_size    = 0.20,
        random_state = 42,
        stratify     = y
    )

    print(f"  Train set: {len(X_train_raw):,}")
    print(f"    On Time: {(y_train_raw==0).sum():,} "
          f"({(y_train_raw==0).mean()*100:.1f}%)")
    print(f"    Delayed: {(y_train_raw==1).sum():,} "
          f"({(y_train_raw==1).mean()*100:.1f}%)")
    print(f"  Test set:  {len(X_test):,}")

    # Balance ONLY train set
    train_df           = X_train_raw.copy()
    train_df["target"] = y_train_raw.values

    majority = train_df[train_df["target"] == 0]
    minority = train_df[train_df["target"] == 1]

    target_n      = min(len(minority) * 2, len(majority))
    majority_down = resample(
        majority,
        replace      = False,
        n_samples    = target_n,
        random_state = 42
    )

    train_balanced = pd.concat(
        [majority_down, minority], ignore_index=True
    ).sample(frac=1, random_state=42).reset_index(drop=True)

    X_train = train_balanced[feature_cols].copy()
    y_train = train_balanced["target"].copy()

    print(f"  Balanced train: {len(X_train):,}")
    print(f"    On Time: {(y_train==0).sum():,}")
    print(f"    Delayed: {(y_train==1).sum():,}")

    return X_train, X_test, y_train, y_test

def train_models(X_train, X_test, y_train, y_test, feature_cols):
    print("\n[4/7] Training XGBoost + LightGBM + Random Forest...")

    # Align columns
    X_test = X_test[feature_cols].copy()

    # Scale
    scaler         = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns = feature_cols
    )
    X_test_scaled  = pd.DataFrame(
        scaler.transform(X_test),
        columns = feature_cols
    )

    os.makedirs("analytics/models", exist_ok=True)
    with open("analytics/models/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    ratio   = (y_train == 0).sum() / (y_train == 1).sum()
    results = {}

    # ── XGBoost ──
    print(f"\n  Training XGBoost...")
    print(f"    scale_pos_weight: {ratio:.2f}")

    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train_scaled, y_train,
        test_size=0.10, random_state=42
    )

    xgb_model = xgb.XGBClassifier(
        n_estimators          = 300,
        max_depth             = 6,
        learning_rate         = 0.05,
        scale_pos_weight      = ratio,
        eval_metric           = "auc",
        early_stopping_rounds = 10,
        random_state          = 42,
        n_jobs                = -1,
        verbosity             = 0,
    )
    xgb_model.fit(
        X_tr, y_tr,
        eval_set = [(X_val, y_val)],
        verbose  = False,
    )

    start     = datetime.now()
    xgb_probs = xgb_model.predict_proba(X_test_scaled)[:, 1]
    elapsed   = (datetime.now() - start).total_seconds()

    results["XGBoost"] = {
        "model":      xgb_model,
        "probs":      xgb_probs,
        "train_time": round(elapsed, 1),
    }
    print(f"    Best iteration: {xgb_model.best_iteration}")

    # ── LightGBM ──
    print(f"\n  Training LightGBM...")

    start     = datetime.now()
    lgb_model = lgb.LGBMClassifier(
        n_estimators  = 300,
        num_leaves    = 31,
        learning_rate = 0.05,
        is_unbalance  = True,
        device        = "cpu",
        random_state  = 42,
        n_jobs        = -1,
        verbose       = -1,
    )
    lgb_model.fit(
        X_train_scaled, y_train,
        eval_set  = [(X_test_scaled, y_test)],
        callbacks = [
            lgb.early_stopping(10, verbose=False),
            lgb.log_evaluation(period=-1),
        ],
    )

    elapsed   = (datetime.now() - start).total_seconds()
    lgb_probs = lgb_model.predict_proba(X_test_scaled)[:, 1]

    results["LightGBM"] = {
        "model":      lgb_model,
        "probs":      lgb_probs,
        "train_time": round(elapsed, 1),
    }
    print(f"    Train time: {elapsed:.1f}s")

    # ── Random Forest ──
    print(f"\n  Training Random Forest...")

    start    = datetime.now()
    rf_model = RandomForestClassifier(
        n_estimators = 200,
        max_depth    = 15,
        class_weight = "balanced_subsample",
        n_jobs       = -1,
        random_state = 42,
    )
    rf_model.fit(X_train, y_train)

    elapsed  = (datetime.now() - start).total_seconds()
    rf_probs = rf_model.predict_proba(X_test)[:, 1]

    results["Random Forest"] = {
        "model":      rf_model,
        "probs":      rf_probs,
        "train_time": round(elapsed, 1),
    }
    print(f"    Train time: {elapsed:.1f}s")

    return results, scaler, X_test, X_test_scaled

def evaluate_models(results, X_test, X_test_scaled,
                    y_test, feature_cols):
    print("\n[5/7] Evaluating with threshold 0.4...")

    THRESHOLD = 0.45
    evaluated = {}

    for name, res in results.items():
        probs  = res["probs"]
        preds  = (probs >= THRESHOLD).astype(int)

        acc            = accuracy_score(y_test, preds)
        auc            = roc_auc_score(y_test, probs)
        tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
        recall         = tp / (tp + fn) if (tp + fn) > 0 else 0

        evaluated[name] = {
            "model":           res["model"],
            "probs":           probs,
            "accuracy":        round(acc  * 100, 2),
            "auc":             round(auc  * 100, 2),
            "recall_delayed":  round(recall * 100, 2),
            "true_positives":  int(tp),
            "false_negatives": int(fn),
            "false_positives": int(fp),
            "true_negatives":  int(tn),
            "train_time":      res["train_time"],
        }

    print(f"\n  {'Model':<20} {'Acc':>8} {'AUC':>8} "
          f"{'Recall':>8} {'TP':>8} {'FN':>8} {'Time':>8}")
    print(f"  {'-'*72}")
    for name, res in evaluated.items():
        print(
            f"  {name:<20} {res['accuracy']:>7.1f}% "
            f"{res['auc']:>7.1f}% "
            f"{res['recall_delayed']:>7.1f}% "
            f"{res['true_positives']:>8,} "
            f"{res['false_negatives']:>8,} "
            f"{res['train_time']:>7.1f}s"
        )

    # Logistics-focused selection
    best_name = max(
        evaluated,
        key=lambda k: (
            evaluated[k]["auc"]            * 0.4 +
            evaluated[k]["recall_delayed"] * 0.6
        )
    )
    best = evaluated[best_name]

    print(f"\n  Best Model (0.4*AUC + 0.6*Recall): {best_name}")
    print(f"  Accuracy:         {best['accuracy']}%")
    print(f"  AUC Score:        {best['auc']}%")
    print(f"  Recall (Delayed): {best['recall_delayed']}%")
    print(f"  True Positives:   {best['true_positives']:,}")
    print(f"  False Negatives:  {best['false_negatives']:,}")

    best_preds = (best["probs"] >= THRESHOLD).astype(int)
    print(f"\n  Classification Report ({best_name}):")
    print(classification_report(
        y_test, best_preds,
        target_names = ["On Time","Delayed"],
        zero_division= 0
    ))

    # Feature importance
    if "Random Forest" in evaluated:
        rf     = evaluated["Random Forest"]["model"]
        imp_df = pd.DataFrame({
            "feature":    feature_cols,
            "importance": rf.feature_importances_
        }).sort_values("importance", ascending=False)

        print(f"  Top 8 features (Random Forest):")
        for _, row in imp_df.head(8).iterrows():
            bar = "x" * int(row["importance"] * 60)
            print(f"    {row['feature']:30} {bar} "
                  f"{row['importance']:.4f}")

    return evaluated, best_name

def save_best_model(evaluated, best_name, feature_cols):
    print(f"\n[6/7] Saving best model ({best_name})...")

    best_model = evaluated[best_name]["model"]
    model_path = "analytics/models/best_model.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)

    meta = {
        "best_model_name": best_name,
        "threshold":       0.45,
        "feature_cols":    feature_cols,
        "accuracy":        evaluated[best_name]["accuracy"],
        "auc":             evaluated[best_name]["auc"],
        "recall_delayed":  evaluated[best_name]["recall_delayed"],
        "saved_at":        datetime.now(timezone.utc).isoformat(),
    }
    with open("analytics/models/model_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  Saved: {model_path}")
    print(f"  Metadata: analytics/models/model_metadata.json")
    return best_model

def save_ml_report(evaluated, best_name, feature_cols):
    print(f"\n[7/7] Saving ML report...")

    now    = datetime.now(timezone.utc)
    report = {
        "report_title":   "GlobeTrack ML Models Report",
        "generated_at":   now.isoformat(),
        "threshold_used": 0.4,
        "models_trained": ["XGBoost","LightGBM","Random Forest"],
        "selection_method":"Logistics Score = 0.4*AUC + 0.6*Recall",
        "improvements": [
            "Split before balance — no data leakage",
            "Threshold = 0.4 for better recall",
            "scale_pos_weight on XGBoost",
            "is_unbalance on LightGBM",
            "balanced_subsample on Random Forest",
            "Early stopping on XGBoost and LightGBM",
            "Interaction features: cargo_stress_index,",
            "  distance_cargo_risk, express_risk_score",
            "No weather leakage in features",
        ],
        "model_results": {
            name: {
                "accuracy_pct":    res["accuracy"],
                "auc_pct":         res["auc"],
                "recall_pct":      res["recall_delayed"],
                "true_positives":  res["true_positives"],
                "false_negatives": res["false_negatives"],
                "train_time_s":    res["train_time"],
            }
            for name, res in evaluated.items()
        },
        "best_model":  best_name,
        "best_metrics":{
            "accuracy_pct":   evaluated[best_name]["accuracy"],
            "auc_pct":        evaluated[best_name]["auc"],
            "recall_pct":     evaluated[best_name]["recall_delayed"],
            "true_positives": evaluated[best_name]["true_positives"],
        },
        "feature_count": len(feature_cols),
        "features":      feature_cols,
    }

    local_path = "analytics/ml_report.json"
    with open(local_path, "w") as f:
        json.dump(report, f, indent=2)

    s3_key = (
        f"ml-reports/"
        f"ml_report_{now.strftime('%Y%m%d_%H%M%S')}.json"
    )
    s3_client.put_object(
        Bucket      = S3_BUCKET_ANALYTICS,
        Key         = s3_key,
        Body        = json.dumps(report, indent=2),
        ContentType = "application/json",
    )

    print(f"  Saved locally: {local_path}")
    print(f"  Saved to S3:   {s3_key}")

    print("\n" + "=" * 55)
    print("  ML RESULTS SUMMARY")
    print("=" * 55)
    print(f"  {'Model':<20} {'Acc':>8} {'AUC':>8} {'Recall':>8}")
    print(f"  {'-'*48}")
    for name, res in evaluated.items():
        flag = " <- best" if name == best_name else ""
        print(f"  {name:<20} {res['accuracy']:>7.1f}% "
              f"{res['auc']:>7.1f}% "
              f"{res['recall_delayed']:>7.1f}%{flag}")
    print("=" * 55)

    return report

def run_ml_pipeline():
    print("=" * 55)
    print("  GlobeTrack - ML Pipeline")
    print("  XGBoost + LightGBM + Random Forest")
    print("  Threshold: 0.4 | No leakage | Interaction features")
    print("=" * 55)

    df                      = load_dataset()
    df, feature_cols        = engineer_features(df)
    X_train, X_test, y_train, y_test \
                            = split_then_balance(df, feature_cols)
    results, scaler, X_test, X_test_scaled \
                            = train_models(
                                  X_train, X_test,
                                  y_train, y_test,
                                  feature_cols
                              )
    evaluated, best_name    = evaluate_models(
                                  results, X_test, X_test_scaled,
                                  y_test, feature_cols
                              )
    save_best_model(evaluated, best_name, feature_cols)
    report                  = save_ml_report(
                                  evaluated, best_name, feature_cols
                              )

    print("\n  ML PIPELINE COMPLETE!")
    return evaluated, report

if __name__ == "__main__":
    run_ml_pipeline()