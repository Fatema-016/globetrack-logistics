# GlobeTrack Logistics - Documentation Generator
# Generates architecture diagram + runbook as HTML
# Step 4 - Final Documentation

from datetime import datetime
import json
import os

def generate_architecture_diagram():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GlobeTrack - Architecture Diagram</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',Arial,sans-serif; background:#f0f4f8; padding:30px; }
  .page { max-width:1100px; margin:0 auto; background:white; border-radius:12px; padding:40px; box-shadow:0 4px 20px rgba(0,0,0,0.1); }
  h1 { text-align:center; color:#1a365d; font-size:22px; margin-bottom:6px; }
  .subtitle { text-align:center; color:#666; font-size:13px; margin-bottom:24px; }
  .stats { display:flex; justify-content:center; gap:20px; margin-bottom:24px; flex-wrap:wrap; }
  .stat { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 18px; text-align:center; }
  .stat-val { font-size:20px; font-weight:700; color:#1e40af; }
  .stat-lbl { font-size:11px; color:#64748b; }
  .pipeline { display:flex; flex-direction:column; gap:12px; }
  .layer { border-radius:10px; padding:14px 18px; border:2px solid; }
  .layer-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; }
  .boxes { display:flex; gap:10px; flex-wrap:wrap; }
  .box { border-radius:8px; padding:8px 12px; font-size:11px; font-weight:600; text-align:center; min-width:120px; flex:1; }
  .box .sub { font-size:10px; font-weight:400; margin-top:2px; opacity:0.85; }
  .arrow { text-align:center; font-size:20px; color:#94a3b8; margin:-2px 0; }
  .l-source   { background:#eff6ff; border-color:#bfdbfe; }
  .l-source   .layer-title { color:#1d4ed8; }
  .l-source   .box { background:#dbeafe; color:#1e40af; }
  .l-ingest   { background:#f0fdf4; border-color:#bbf7d0; }
  .l-ingest   .layer-title { color:#15803d; }
  .l-ingest   .box { background:#dcfce7; color:#166534; }
  .l-storage  { background:#fefce8; border-color:#fde68a; }
  .l-storage  .layer-title { color:#b45309; }
  .l-storage  .box { background:#fef3c7; color:#92400e; }
  .l-process  { background:#fdf4ff; border-color:#e9d5ff; }
  .l-process  .layer-title { color:#7e22ce; }
  .l-process  .box { background:#f3e8ff; color:#6b21a8; }
  .l-ml       { background:#fff1f2; border-color:#fecdd3; }
  .l-ml       .layer-title { color:#be123c; }
  .l-ml       .box { background:#ffe4e6; color:#9f1239; }
  .l-analytics{ background:#fff7ed; border-color:#fed7aa; }
  .l-analytics .layer-title { color:#c2410c; }
  .l-analytics .box { background:#ffedd5; color:#9a3412; }
  .l-orch     { background:#f8fafc; border-color:#cbd5e1; }
  .l-orch     .layer-title { color:#334155; }
  .l-orch     .box { background:#f1f5f9; color:#1e293b; }
  .l-monitor  { background:#f0f9ff; border-color:#bae6fd; }
  .l-monitor  .layer-title { color:#0369a1; }
  .l-monitor  .box { background:#e0f2fe; color:#075985; }
  .footer { text-align:center; margin-top:20px; font-size:11px; color:#94a3b8; }
</style>
</head>
<body>
<div class="page">
  <h1>GlobeTrack Logistics Ltd.</h1>
  <div class="subtitle">End-to-End Cloud Big Data Solution | AWS ap-south-1 Mumbai | TCS iON AIP-135</div>

  <div class="stats">
    <div class="stat"><div class="stat-val">1.8M</div><div class="stat-lbl">Records Ingested</div></div>
    <div class="stat"><div class="stat-val">3</div><div class="stat-lbl">S3 Data Zones</div></div>
    <div class="stat"><div class="stat-val">5</div><div class="stat-lbl">ETL Pipelines</div></div>
    <div class="stat"><div class="stat-val">73.1%</div><div class="stat-lbl">ML AUC Score</div></div>
    <div class="stat"><div class="stat-val">94.5%</div><div class="stat-lbl">Fleet Health</div></div>
    <div class="stat"><div class="stat-val">27/27</div><div class="stat-lbl">Tests Passed</div></div>
  </div>

  <div class="pipeline">
    <div class="layer l-source">
      <div class="layer-title">Layer 1 - Data Sources(Simulated Data)</div>
      <div class="boxes">
        <div class="box">Vehicle IoT Sensors<div class="sub">GPS, Fuel, Engine, Speed, Tiers</div></div>
        <div class="box">Customer Booking Logs<div class="sub">Orders, Routes, Timestamps</div></div>
        <div class="box">External Feeds<div class="sub">Weather, Traffic, Currency APIs</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-ingest">
      <div class="layer-title">Layer 2 - Data Ingestion </div>
      <div class="boxes">
        <div class="box">IoT Simulator<div class="sub">50 vehicles, 3 tiers</div></div>
        <div class="box">Booking Simulator<div class="sub">8 delay rules injected</div></div>
        <div class="box">Weather Simulator<div class="sub">8 cities, climate patterns</div></div>
        <div class="box">Large Dataset Gen<div class="sub">600K rows x 3 = 1.8M</div></div>
        <div class="box">Manifest Logger<div class="sub">File tracking + metadata</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-storage">
      <div class="layer-title">Layer 3 - Raw Data Lake (globetrack-raw-data-lake)</div>
      <div class="boxes">
        <div class="box">iot-sensor-data/<div class="sub">600K CSV records</div></div>
        <div class="box">booking-logs/<div class="sub">600K CSV records</div></div>
        <div class="box">weather-data/<div class="sub">600K CSV records</div></div>
        <div class="box">ingestion_manifest/<div class="sub">Metadata tracking</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-process">
      <div class="layer-title">Layer 4 - ETL Processing </div>
      <div class="boxes">
        <div class="box">IoT ETL<div class="sub">Clean, tier features</div></div>
        <div class="box">Booking ETL<div class="sub">interaction features</div></div>
        <div class="box">Weather ETL<div class="sub">Severity, combined risk</div></div>
        <div class="box">Enrichment ETL<div class="sub">Join all 3 datasets</div></div>
        <div class="box">Large Scale ETL<div class="sub">1.18M records, Parquet</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-storage">
      <div class="layer-title">Layer 5 - Processed Zone (globetrack-processed-data)</div>
      <div class="boxes">
        <div class="box">iot-sensor-cleaned/<div class="sub">Parquet, Snappy, 28 cols</div></div>
        <div class="box">booking-logs-cleaned/<div class="sub">Parquet, Snappy, 28 cols</div></div>
        <div class="box">weather-data-cleaned/<div class="sub">Parquet, Snappy, 25 cols</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-ml">
      <div class="layer-title">Layer 6 - ML and Analytics </div>
      <div class="boxes">
        <div class="box">XGBoost<div class="sub">AUC 73.1%, Recall 56.8%</div></div>
        <div class="box">LightGBM<div class="sub">AUC 72.9%, fast training</div></div>
        <div class="box">Random Forest<div class="sub">AUC 72.8%, feature importance</div></div>
        <div class="box">Anomaly Detection<div class="sub">Tier-aware: OLD 9%, NEW 2%</div></div>
        <div class="box">AWS Athena<div class="sub">SQL on Parquet, Glue Catalog</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-analytics">
      <div class="layer-title">Layer 7 - Analytics Zone (globetrack-analytics-zone)</div>
      <div class="boxes">
        <div class="box">bookings-large/<div class="sub">6 Parquet chunks</div></div>
        <div class="box">iot-large/<div class="sub">6 Parquet chunks</div></div>
        <div class="box">ml-reports/<div class="sub">Model results JSON</div></div>
        <div class="box">anomaly-reports/<div class="sub">32,763 anomalies</div></div>
        <div class="box">master-reports/<div class="sub">KPI dashboard JSON</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-orchestration">
      <div class="layer-title">Layer 8 - Orchestration (Step 4)</div>
      <div class="boxes">
        <div class="box">Apache Airflow DAG<div class="sub">14 tasks, daily 6AM</div></div>
        <div class="box">AWS Step Functions<div class="sub">Pipeline state machine</div></div>
        <div class="box">Scheduled Retraining<div class="sub">Daily ML model update</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-monitor">
      <div class="layer-title">Layer 9 - Monitoring and Alerting (Step 4)</div>
      <div class="boxes">
        <div class="box">CloudWatch<div class="sub">12 metrics, 5 alarms</div></div>
        <div class="box">SNS Alerts<div class="sub">Email notifications</div></div>
        <div class="box">Dashboard<div class="sub">4 widget live view</div></div>
        <div class="box">Test Suite<div class="sub">27/27 passing</div></div>
      </div>
    </div>
  </div>
  <div class="footer">GlobeTrack Logistics Ltd. - TCS iON AIP-135 Industry Project - Fatema Habil Saifuddin - MSc Statistics(DS)|Vishwakarma University""" + datetime.now().strftime("%d %B %Y") + """</div>
</div>
</body>
</html>"""

    with open("docs/architecture_diagram.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  architecture_diagram.html generated")

def generate_runbook():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GlobeTrack Logistics Ltd. - Operational Runbook</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',Arial,sans-serif; background:#fff; color:#1e293b; }
  .page { max-width:900px; margin:0 auto; padding:50px; }
  h1 { color:#1e293b; font-size:24px; margin-bottom:6px; }
  .meta { color:#64748b; font-size:13px; margin-bottom:30px; padding-bottom:16px; border-bottom:2px solid #f1f5f9; }
  h2 { font-size:18px; color:#1e40af; margin:30px 0 12px; padding:8px 14px; background:#f8fafc; border-left:4px solid #3b82f6; border-radius:0 6px 6px 0; }
  h3 { font-size:14px; color:#334155; margin:18px 0 8px; }
  p  { font-size:13px; color:#475569; line-height:1.8; margin-bottom:10px; }
  code { background:#f1f5f9; color:#dc2626; padding:2px 6px; border-radius:4px; font-size:12px; font-family:monospace; }
  .cmd { background:#1e293b; color:#86efac; padding:12px 16px; border-radius:8px; font-size:12px; font-family:monospace; margin:10px 0; line-height:1.8; }
  table { width:100%; border-collapse:collapse; margin:12px 0; font-size:12px; }
  th { background:#1e40af; color:white; padding:8px 12px; text-align:left; }
  td { padding:8px 12px; border-bottom:1px solid #f1f5f9; color:#475569; }
  tr:nth-child(even) td { background:#f8fafc; }
  .alert-info  { background:#eff6ff; border-left:4px solid #3b82f6; padding:10px 14px; margin:10px 0; font-size:12px; color:#1d4ed8; border-radius:0 6px 6px 0; }
  .alert-warn  { background:#fffbeb; border-left:4px solid #f59e0b; padding:10px 14px; margin:10px 0; font-size:12px; color:#b45309; border-radius:0 6px 6px 0; }
  .footer { text-align:center; margin-top:40px; padding-top:16px; border-top:1px solid #f1f5f9; font-size:11px; color:#94a3b8; }
</style>
</head>
<body>
<div class="page">
<h1>GlobeTrack Logistics - Operational Runbook</h1>
<div class="meta">TCS iON AIP-135 | AWS ap-south-1""" + datetime.now().strftime("%d %B %Y") + """</div>

<h2>1. Environment Setup</h2>
<h3>Prerequisites</h3>
<table>
  <tr><th>Software</th><th>Version</th><th>Purpose</th></tr>
  <tr><td>Python</td><td>3.12.7</td><td>ETL and ML scripts</td></tr>
  <tr><td>Git</td><td>2.53.0</td><td>Version control</td></tr>
  <tr><td>Apache Airflow</td><td>3.1.8</td><td>Pipeline orchestration</td></tr>
  <tr><td>Java OpenJDK</td><td>21.0.7</td><td>Spark runtime</td></tr>
  <tr><td>Power BI Desktop</td><td>Latest</td><td>Dashboard visualization</td></tr>
  <tr><td>AWS CLI</td><td>Latest</td><td>Cloud access</td></tr>
</table>

<h3>Python Libraries</h3>
<div class="cmd">pip install boto3 pandas pyarrow scikit-learn xgboost lightgbm
pip install apache-airflow awscli python-dotenv fastparquet requests</div>

<h3>AWS Configuration</h3>
<div class="cmd">aws configure
# Region: ap-south-1
# Output: json
</div>

<h2>2. AWS Infrastructure</h2>
<h3>S3 Buckets</h3>
<table>
  <tr><th>Bucket</th><th>Purpose</th><th>Region</th></tr>
  <tr><td>globetrack-raw-data-lake</td><td>Raw JSON and CSV ingestion</td><td>ap-south-1</td></tr>
  <tr><td>globetrack-processed-data</td><td>Cleaned Parquet files</td><td>ap-south-1</td></tr>
  <tr><td>globetrack-analytics-zone</td><td>ML outputs and reports</td><td>ap-south-1</td></tr>
</table>

<h3>IAM Policies Required</h3>
<table>
  <tr><th>Policy</th><th>Required For</th></tr>
  <tr><td>AmazonS3FullAccess</td><td>All S3 operations</td></tr>
  <tr><td>AWSGlueConsoleFullAccess</td><td>Glue crawlers and catalog</td></tr>
  <tr><td>CloudWatchFullAccess</td><td>Metrics and alarms</td></tr>
  <tr><td>AmazonSNSFullAccess</td><td>Alert notifications</td></tr>
  <tr><td>AmazonAthenaFullAccess</td><td>SQL queries on Parquet</td></tr>
</table>

<h2>3. Pipeline Execution</h2>
<div class="alert-info">Run all commands from project root: cd globetrack-logistics</div>

<h3>Step 1 - Data Ingestion</h3>
<div class="cmd">python ingestion/iot_simulator.py
python ingestion/booking_simulator.py
python ingestion/weather_simulator.py
python ingestion/generate_large_datasets.py
python ingestion/manifest_logger.py</div>

<h3>Step 2 - ETL Processing</h3>
<div class="cmd">python processing/etl_iot_sensor.py
python processing/etl_booking_logs.py
python processing/etl_weather.py
python processing/etl_enrichment.py
python processing/etl_large_scale.py</div>

<h3>Step 3 - Analytics and ML</h3>
<div class="cmd">python analytics/ml_models.py
python analytics/ml_anomaly_detection.py
python analytics/master_analytics.py</div>

<h3>Step 4 - Deployment and Monitoring</h3>
<div class="cmd">python dags/globetrack_pipeline_dag.py
python monitoring/cloudwatch_monitoring.py
python tests/test_cases.py</div>

<h2>4. ML Model Details</h2>
<table>
  <tr><th>Model</th><th>Accuracy</th><th>AUC</th><th>Recall</th><th>Selection</th></tr>
  <tr><td>XGBoost</td><td>69.0%</td><td>73.1%</td><td>56.8%</td><td>Best-Logistics Score</td></tr>
  <tr><td>LightGBM</td><td>70.8%</td><td>72.9%</td><td>52.3%</td><td>Runner up</td></tr>
  <tr><td>Random Forest</td><td>69.4%</td><td>72.8%</td><td>55.5%</td><td>Feature importance</td></tr>
</table>
<p>Selection method: Logistics Score = 0.4 x AUC + 0.6 x Recall</p>
<p>Threshold: 0.45 | Interaction features included</p>

<h2>5. Anomaly Detection</h2>
<table>
  <tr><th>Vehicle Tier</th><th>Contamination</th><th>Anomaly Rate</th><th>Reason</th></tr>
  <tr><td>OLD (GT-001 to GT-017)</td><td>9%</td><td>9.0%</td><td>Worn engines, fuel leaks</td></tr>
  <tr><td>MID (GT-018 to GT-035)</td><td>5%</td><td>5.0%</td><td>Standard wear and tear</td></tr>
  <tr><td>NEW (GT-036 to GT-050)</td><td>2%</td><td>2.0%</td><td>Modern sensors, reliable</td></tr>
</table>

<h2>6. CloudWatch Alarms</h2>
<table>
  <tr><th>Alarm</th><th>Threshold</th><th>Action</th></tr>
  <tr><td>GlobeTrack-FleetHealth-Critical</td><td>Less than 85%</td><td>SNS Alert</td></tr>
  <tr><td>GlobeTrack-DelayRate-High</td><td>Greater than 50%</td><td>SNS Alert</td></tr>
  <tr><td>GlobeTrack-Ingestion-Failed</td><td>Less than 95%</td><td>SNS Alert</td></tr>
  <tr><td>GlobeTrack-MLModel-Degraded</td><td>Less than 60% AUC</td><td>Warning</td></tr>
  <tr><td>GlobeTrack-Anomaly-Spike</td><td>Greater than 60,000</td><td>SNS Alert</td></tr>
</table>


<div class="footer">GlobeTrack Logistics Ltd. - TCS iON AIP-135 Industry Project - Fatema Habil Saifuddin - MSc Statistics(DS)|Vishwakarma University""" + datetime.now().strftime("%d %B %Y") + """</div>
</div>
</body>
</html>"""

    with open("docs/runbook.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  runbook.html generated")

if __name__ == "__main__":
    print("=" * 55)
    print("  GlobeTrack - Generating Documentation")
    print("=" * 55)
    generate_architecture_diagram()
    generate_runbook()
    print("\n  DOCUMENTATION COMPLETE")
    print("  docs/architecture_diagram.html")
    print("  docs/runbook.html")
    print("=" * 55)