# GlobeTrack Logistics - Test Cases & Scenarios
# Step 4 - Deployment & Monitoring


import boto3
import pandas as pd
import json
import sys
import os
from datetime import datetime, timezone
from io import BytesIO

S3_BUCKET_RAW       = "globetrack-raw-data-lake"
S3_BUCKET_PROCESSED = "globetrack-processed-data"
S3_BUCKET_ANALYTICS = "globetrack-analytics-zone"
REGION              = "ap-south-1"
s3_client           = boto3.client("s3", region_name=REGION)

class TestResult:
    def __init__(self):
        self.results = []
        self.passed  = 0
        self.failed  = 0
        self.total   = 0

    def add(self, case_id, name, expected, actual, status, priority="HIGH"):
        self.results.append({
            "case_id":   case_id,
            "test_name": name,
            "expected":  expected,
            "actual":    actual,
            "status":    status,
            "priority":  priority,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.total += 1
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1
        icon = "PASS" if status == "PASS" else "FAIL"
        print(f"  [{icon}] [{case_id}] {name}")
        print(f"         Expected: {expected}")
        print(f"         Actual:   {actual}")

    def summary(self):
        pct = round(self.passed / self.total * 100, 1) if self.total > 0 else 0
        print(f"\n  {'='*50}")
        print(f"  TEST SUMMARY")
        print(f"  {'='*50}")
        print(f"  Total:  {self.total}")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Pass %: {pct}%")
        print(f"  {'='*50}")
        return self.results

tr = TestResult()

def test_s3_infrastructure():
    print("\n  TEST SUITE 1 - S3 Infrastructure")
    print("  " + "-"*50)

    for bucket, name, tc in [
        (S3_BUCKET_RAW,       "Raw data lake",       "TC-001"),
        (S3_BUCKET_PROCESSED, "Processed data",      "TC-002"),
        (S3_BUCKET_ANALYTICS, "Analytics zone",      "TC-003"),
    ]:
        try:
            s3_client.head_bucket(Bucket=bucket)
            tr.add(tc, f"{name} bucket exists",
                   "Accessible", "Accessible", "PASS")
        except Exception as e:
            tr.add(tc, f"{name} bucket exists",
                   "Accessible", str(e), "FAIL")

    for folder, tc in [
        ("iot-sensor-data/",  "TC-004"),
        ("booking-logs/",     "TC-005"),
        ("weather-data/",     "TC-006"),
    ]:
        try:
            resp  = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET_RAW,
                        Prefix=folder, MaxKeys=1
                    )
            count = resp.get("KeyCount", 0)
            status = "PASS" if count > 0 else "FAIL"
            tr.add(tc, f"{folder} has files",
                   "Files present",
                   f"{count} file(s) found", status)
        except Exception as e:
            tr.add(tc, f"{folder} has files",
                   "Files present", str(e), "FAIL")

def test_data_ingestion():
    print("\n  TEST SUITE 2 - Data Ingestion")
    print("  " + "-"*50)

    for folder, tc, label in [
        ("iot-sensor-data",  "TC-007", "IoT"),
        ("booking-logs",     "TC-008", "Bookings"),
        ("weather-data",     "TC-009", "Weather"),
    ]:
        try:
            paginator = s3_client.get_paginator("list_objects_v2")
            pages     = paginator.paginate(
                            Bucket=S3_BUCKET_RAW,
                            Prefix=f"{folder}/large-dataset/"
                        )
            count = sum(
                1 for page in pages
                for obj in page.get("Contents", [])
                if obj["Key"].endswith(".csv")
            )
            status = "PASS" if count >= 60 else "FAIL"
            tr.add(tc, f"{label} large dataset has 60 chunks",
                   "60 chunks", f"{count} chunks", status)
        except Exception as e:
            tr.add(tc, f"{label} large dataset chunks",
                   "60 chunks", str(e), "FAIL")

    try:
        resp  = s3_client.list_objects_v2(
                    Bucket=S3_BUCKET_RAW,
                    Prefix="ingestion_manifest/", MaxKeys=1
                )
        count = resp.get("KeyCount", 0)
        status = "PASS" if count > 0 else "FAIL"
        tr.add("TC-010", "Ingestion manifest exists",
               "Manifest present",
               "Found" if count > 0 else "Not found", status)
    except Exception as e:
        tr.add("TC-010", "Ingestion manifest exists",
               "Manifest present", str(e), "FAIL")

def test_etl_processing():
    print("\n  TEST SUITE 3 - ETL Processing")
    print("  " + "-"*50)

    for folder, tc, label in [
        ("iot-sensor-cleaned/",    "TC-011", "IoT cleaned"),
        ("booking-logs-cleaned/",  "TC-012", "Bookings cleaned"),
        ("weather-data-cleaned/",  "TC-013", "Weather cleaned"),
    ]:
        try:
            resp  = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET_PROCESSED,
                        Prefix=folder, MaxKeys=1
                    )
            count  = resp.get("KeyCount", 0)
            status = "PASS" if count > 0 else "FAIL"
            tr.add(tc, f"{label} Parquet exists",
                   "Parquet present",
                   "Found" if count > 0 else "Not found", status)
        except Exception as e:
            tr.add(tc, f"{label} Parquet exists",
                   "Parquet present", str(e), "FAIL")

    for folder, tc, label in [
        ("bookings-large/", "TC-014", "Bookings large"),
        ("iot-large/",      "TC-015", "IoT large"),
    ]:
        try:
            paginator = s3_client.get_paginator("list_objects_v2")
            pages     = paginator.paginate(
                            Bucket=S3_BUCKET_ANALYTICS,
                            Prefix=folder
                        )
            count = sum(
                1 for page in pages
                for obj in page.get("Contents", [])
                if obj["Key"].endswith(".parquet")
            )
            status = "PASS" if count >= 6 else "FAIL"
            tr.add(tc, f"{label} has 6+ Parquet chunks",
                   "6+ chunks", f"{count} chunks", status)
        except Exception as e:
            tr.add(tc, f"{label} Parquet chunks",
                   "6+ chunks", str(e), "FAIL")

def test_ml_models():
    print("\n  TEST SUITE 4 - ML Models")
    print("  " + "-"*50)

    model_path  = "analytics/models/best_model.pkl"
    scaler_path = "analytics/models/scaler.pkl"
    meta_path   = "analytics/models/model_metadata.json"

    for path, tc, label in [
        (model_path,  "TC-016", "best_model.pkl"),
        (scaler_path, "TC-017", "scaler.pkl"),
        (meta_path,   "TC-018", "model_metadata.json"),
    ]:
        exists = os.path.exists(path)
        tr.add(tc, f"{label} exists",
               "File present",
               f"Found ({os.path.getsize(path)//1024}KB)"
               if exists else "Not found",
               "PASS" if exists else "FAIL")

    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)

        auc    = meta.get("auc", 0)
        recall = meta.get("recall_delayed", 0)

        tr.add("TC-019", "ML AUC > 70%",
               "AUC > 70%", f"AUC: {auc}%",
               "PASS" if auc > 70 else "FAIL")

        tr.add("TC-020", "ML Recall > 50%",
               "Recall > 50%", f"Recall: {recall}%",
               "PASS" if recall > 50 else "FAIL")
    else:
        tr.add("TC-019", "ML AUC check",
               "AUC > 70%", "Metadata not found", "FAIL")
        tr.add("TC-020", "ML Recall check",
               "Recall > 50%", "Metadata not found", "FAIL")

def test_analytics():
    print("\n  TEST SUITE 5 - Analytics & Reporting")
    print("  " + "-"*50)

    for prefix, tc, label in [
        ("master-reports/",  "TC-021", "Master report"),
        ("ml-reports/",      "TC-022", "ML report"),
        ("anomaly-reports/", "TC-023", "Anomaly report"),
    ]:
        try:
            resp  = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET_ANALYTICS,
                        Prefix=prefix, MaxKeys=1
                    )
            count  = resp.get("KeyCount", 0)
            status = "PASS" if count > 0 else "FAIL"
            tr.add(tc, f"{label} exists in S3",
                   "Report present",
                   "Found" if count > 0 else "Not found", status)
        except Exception as e:
            tr.add(tc, f"{label} in S3",
                   "Present", str(e), "FAIL")

    if os.path.exists("analytics/master_report.json"):
        with open("analytics/master_report.json") as f:
            report = json.load(f)
        fleet    = report.get("fleet_kpis", {})
        delivery = report.get("delivery_kpis", {})
        vehicles = fleet.get("total_vehicles", 0)
        orders   = delivery.get("total_orders", 0)
        status   = "PASS" if vehicles >= 50 and orders >= 500000 else "FAIL"
        tr.add("TC-024",
               "Master report has 50 vehicles & 500K+ orders",
               "50 vehicles, 500K+ orders",
               f"{vehicles} vehicles, {orders:,} orders",
               status)
    else:
        tr.add("TC-024", "Master report local check",
               "Report present", "Not found", "FAIL")

    if os.path.exists("monitoring/cloudwatch_config.json"):
        with open("monitoring/cloudwatch_config.json") as f:
            config = json.load(f)
        alarms = len(config.get("alarms", []))
        tr.add("TC-025", "CloudWatch has 5 alarms",
               "5 alarms", f"{alarms} alarms",
               "PASS" if alarms >= 5 else "FAIL")
    else:
        tr.add("TC-025", "CloudWatch config exists",
               "Config present", "Not found", "FAIL")

    if os.path.exists("dags/globetrack_pipeline_dag.py"):
        try:
            with open("dags/globetrack_pipeline_dag.py") as f:
                code = f.read()
            compile(code, "globetrack_pipeline_dag.py", "exec")
            tr.add("TC-026", "Airflow DAG valid Python syntax",
                   "Valid syntax", "DAG parsed successfully", "PASS")
        except SyntaxError as e:
            tr.add("TC-026", "Airflow DAG syntax",
                   "Valid syntax", str(e), "FAIL")
    else:
        tr.add("TC-026", "Airflow DAG exists",
               "DAG present", "Not found", "FAIL")

    if os.path.exists("analytics/anomaly_report.json"):
        with open("analytics/anomaly_report.json") as f:
            report = json.load(f)
        health = report.get("fleet_health", {}).get("healthy_pct", 0)
        tr.add("TC-027", "Fleet health > 90%",
               "Health > 90%", f"Health: {health}%",
               "PASS" if health > 90 else "FAIL")
    else:
        tr.add("TC-027", "Anomaly report exists",
               "Report present", "Not found", "FAIL")

def save_test_report(results):
    now    = datetime.now(timezone.utc)
    report = {
        "report_title":  "GlobeTrack Logistics Test Design Document",
        "project":       "TCS iON AIP-135",
        "generated_at":  now.isoformat(),
        "total_tests":   tr.total,
        "passed":        tr.passed,
        "failed":        tr.failed,
        "pass_rate_pct": round(tr.passed/tr.total*100, 1),
        "test_suites": {
            "Suite 1 - S3 Infrastructure":  "TC-001 to TC-006",
            "Suite 2 - Data Ingestion":     "TC-007 to TC-010",
            "Suite 3 - ETL Processing":     "TC-011 to TC-015",
            "Suite 4 - ML Models":          "TC-016 to TC-020",
            "Suite 5 - Analytics":          "TC-021 to TC-027",
        },
        "test_results": results,
    }

    local_path = "tests/test_report.json"
    with open(local_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  Test report saved: {local_path}")
    return report

def run_all_tests():
    print("=" * 55)
    print("  GlobeTrack - Test Suite Runner")
    print("  27 test cases across 5 suites")
    print("=" * 55)

    test_s3_infrastructure()
    test_data_ingestion()
    test_etl_processing()
    test_ml_models()
    test_analytics()

    results = tr.summary()
    save_test_report(results)

    print("\n  TEST SUITE COMPLETE")
    return tr.passed == tr.total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)