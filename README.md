# GlobeTrack Logistics - End-to-End Cloud Big Data Solution 

This project is compeleted under Industry Honour Certification during my SemesterII - MSc Statistics Data Science| Vishwakarma University.
> **TCS iON AIP 135 - End-to-End Cloud Big Data Solution for Real-Time Logistics Intelligence** | cloud : AWS ap-south-1 

A Big Data Analytics pipeline for **GlobeTrack Logistics Ltd.** built on AWS cloud with Python, Scikit-learn, XGBoost, LightGBM,Random Forest, Apache Airflow and CloudWatch.

---

## Project Overview

At GlobeTrack Logistics Ltd., this system collects, processes and analyses simulated data from 3 real-time sources to optimise delivery routes, predict delays and monitor fleet health across Maharashtra and Goa, India.

| Metric | Value |
|--------|-------|
| Raw records ingested | 1,800,000 |
| Records processed | 1,180,107 |
| S3 data zones | 3 |
| ETL pipelines | 5 |
| ML models trained | 3 |
| Best ML AUC score | 73.1% (XGBoost) |
| ML Recall (Delayed) | 56.8% |
| ML Accuracy (XGBoost) | 69.0% |
| Anomalies detected | 32,763 (5.5%) |
| Fleet health | 94.5% |
| Total revenue tracked | Rs 6.43 Billion |
| Test cases | 27/27 passing |

---

## Architecture (see docs/architecture_diagram.html for the full diagram.)
Data Sources -> Ingestion -> Raw S3 Lake -> ETL Processing -> Processed S3 -> ML & Analytics -> Analytics S3 
-> Airflow Orchestration -> CloudWatch Monitoring

---

## Data Sources (Heterogeneous)

| Source | Type | Records | Key Fields |
|--------|------|---------|------------|
| Vehicle IoT Sensors | Telemetry | 600,000 | GPS, fuel, engine, speed, tiers |
| Customer Booking Logs | Operational | 600,000 | Orders, routes, timestamps, status |
| Weather & Traffic APIs | External Feed | 600,000 | City climate, congestion, currency |

---
```
## Project Structure

globetrack-logistics/
│
├── ingestion/
│     iot_simulator.py           - Vehicle IoT sensor simulator
│     booking_simulator.py       - Customer booking log simulator
│     weather_simulator.py       - Weather and traffic feed simulator
│     generate_large_datasets.py - 1.8M record generator with patterns
│     manifest_logger.py         - Ingestion metadata tracker
│
├── processing/
│     etl_iot_sensor.py          - IoT ETL pipeline
│     etl_booking_logs.py        - Booking logs ETL pipeline
│     etl_weather.py             - Weather ETL pipeline
│     etl_enrichment.py          - Data enrichment joins all 3
│     etl_large_scale.py         - Large scale ETL 1.18M records
│
├── analytics/
│     ml_models.py               - XGBoost + LightGBM + Random Forest
│     ml_anomaly_detection.py    - IoT (tier) anomaly detection
│     master_analytics.py        - KPI dashboard report
│     models/
│       best_model.pkl           - Saved XGBoost model
│       scaler.pkl               - Saved StandardScaler
│       model_metadata.json      - Model metrics and config
│
├── dags/
│     globetrack_pipeline_dag.py - Apache Airflow DAG 14 tasks
│
├── monitoring/
│     cloudwatch_monitoring.py   - CloudWatch metrics alarms dashboard
│
├── tests/
│     test_cases.py              - 27 automated test cases
│
└── docs/
architecture_diagram.html  
runbook.html               - Operational runbook 
ingestion_manifest.csv     - Sample ingestion manifest
```
---

## Machine Learning Models

### Delivery Delay Prediction

Three models trained on 580,107 booking records.

| Model | Accuracy | AUC | Recall | Selection |
|-------|----------|-----|--------|-----------|
| XGBoost | 69.0% | 73.1% | 56.8% | Best |
| LightGBM | 70.8% | 72.9% | 52.3% | fastest in speed |
| Random Forest | 69.4% | 72.8% | 55.5% | Feature importance |

Selection method: Logistics Score = 0.4 x AUC + 0.6 x Recall

Key engineering decisions:
- Split before balance — no data leakage
- Threshold 0.45 — optimised for logistics recall
- scale_pos_weight on XGBoost
- is_unbalance on LightGBM
- balanced_subsample on Random Forest
- Early stopping on XGBoost and LightGBM
- Interaction features: cargo_stress_index, distance_cargo_risk, express_risk_score
- No weather features — removed to prevent data leakage

### IoT Anomaly Detection

Tier-based Isolation Forest + Local Outlier Factor on 600,000 sensor readings.

| Vehicle Tier | Contamination | Anomaly Rate | Reason |
|-------------|--------------|--------------|--------|
| OLD (GT-001 to GT-017) | 9% | 9.0% | Worn engines, fuel issues |
| MID (GT-018 to GT-035) | 5% | 5.0% | Standard wear and tear |
| NEW (GT-036 to GT-050) | 2% | 2.0% | Modern sensors, reliable |

Fleet health: 94.5% | Total anomalies: 32,763

---

## AWS Infrastructure

| Resource | Name | Purpose |
|----------|------|---------|
| S3 Bucket | globetrack-raw-data-lake | Raw JSON and CSV storage |
| S3 Bucket | globetrack-processed-data | Cleaned Parquet files |
| S3 Bucket | globetrack-analytics-zone | ML outputs and reports |
| Glue Crawler | globetrack-iot-crawler | Auto schema detection |
| Glue Crawler | globetrack-bookings-crawler | Auto schema detection |
| Glue Database | globetrack_db | Athena query catalog |
| CloudWatch | GlobeTrack-Logistics-Dashboard | Live monitoring |
| SNS Topic | globetrack-pipeline-alerts | Alert notifications |

---

## Setup & Execution

### Prerequisites
```bash
pip install boto3 pandas pyarrow scikit-learn xgboost lightgbm
pip install apache-airflow awscli python-dotenv fastparquet requests
```

### AWS Configuration
```bash
aws configure
# Region: ap-south-1
# Output: json
```

### Run Pipeline
```bash
python ingestion/iot_simulator.py
python ingestion/booking_simulator.py
python ingestion/weather_simulator.py
python ingestion/generate_large_datasets.py
python ingestion/manifest_logger.py

python processing/etl_iot_sensor.py
python processing/etl_booking_logs.py
python processing/etl_weather.py
python processing/etl_enrichment.py
python processing/etl_large_scale.py

python analytics/ml_models.py
python analytics/ml_anomaly_detection.py
python analytics/master_analytics.py

python dags/globetrack_pipeline_dag.py
python monitoring/cloudwatch_monitoring.py
python tests/test_cases.py
```

---

## Test Results

Suite 1 - S3 Infrastructure      6/6
Suite 2 - Data Ingestion         4/4
Suite 3 - ETL Processing         5/5
Suite 4 - ML Models              7/7
Suite 5 - Analytics              5/5
Total: 27/27 PASSED


---

## Key Insights

- Fleet health is 94.5% — OLD trucks show 9% anomaly rate vs 2% for NEW trucks
- Delay rate is 35.6% — Thunderstorm and Fog conditions cause highest delays
- EXPRESS orders show 53.94% delay vs 46.06% for NORMAL 
- Revenue tracked — Rs 6.43 Billion across 580,107 orders
- Anomalous vehicles average 82.76 km/h vs 72.58 km/h normal — overspeeding pattern

---

**Fatema Habil Saifuddin** 

fatemahab.786@gmail.com

[LinkedIn](https://www.linkedin.com/in/fatema-habil-saifuddin)