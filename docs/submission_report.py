# GlobeTrack Logistics - TCS iON Submission Report Generator
# Generates the final project report as HTML 
# Step 4 - Final Documentation

from datetime import datetime
import json
import os

def load_report_data():
    ml_report     = {}
    anomaly_report= {}
    master_report = {}

    if os.path.exists("analytics/ml_report.json"):
        with open("analytics/ml_report.json") as f:
            ml_report = json.load(f)

    if os.path.exists("analytics/anomaly_report.json"):
        with open("analytics/anomaly_report.json") as f:
            anomaly_report = json.load(f)

    if os.path.exists("analytics/master_report.json"):
        with open("analytics/master_report.json") as f:
            master_report = json.load(f)

    return ml_report, anomaly_report, master_report

def generate_report():
    ml_report, anomaly_report, master_report = load_report_data()

    fleet    = master_report.get("fleet_kpis",    {})
    delivery = master_report.get("delivery_kpis", {})
    best     = ml_report.get("best_metrics",      {})
    models   = ml_report.get("model_results",     {})

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GlobeTrack Logistics Ltd. - TCS iON 135 - End-to-End Cloud Big Data Solution for Logistics Intelligence.</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',Arial,sans-serif; background:#fff; color:#1e293b; }
  .page { max-width:900px; margin:0 auto; padding:60px 50px; }
  .cover { text-align:center; padding:80px 0 60px; border-bottom:3px solid #1e40af; margin-bottom:50px; }
  .cover-logo  { font-size:32px; font-weight:700; color:#1e40af; margin-bottom:8px; }
  .cover-sub   { font-size:16px; color:#64748b; margin-bottom:40px; }
  .cover-title { font-size:26px; font-weight:700; color:#1e293b; margin-bottom:16px; line-height:1.4; }
  .cover-badge { display:inline-block; background:#1e40af; color:white; padding:8px 24px; border-radius:20px; font-size:13px; margin:4px; }
  .cover-meta  { margin-top:40px; font-size:13px; color:#64748b; line-height:2.2; }
  h2 { font-size:20px; color:#1e40af; margin:40px 0 16px; padding-bottom:8px; border-bottom:2px solid #e2e8f0; }
  h3 { font-size:15px; color:#334155; margin:24px 0 10px; }
  p  { font-size:13px; color:#475569; line-height:1.8; margin-bottom:12px; }
  table { width:100%; border-collapse:collapse; margin:16px 0; font-size:12px; }
  th { background:#1e40af; color:white; padding:10px 12px; text-align:left; }
  td { padding:9px 12px; border-bottom:1px solid #f1f5f9; color:#475569; }
  tr:nth-child(even) td { background:#f8fafc; }
  .kpi-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:20px 0; }
  .kpi-box  { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:16px; text-align:center; }
  .kpi-val  { font-size:22px; font-weight:700; color:#1e40af; }
  .kpi-lbl  { font-size:11px; color:#64748b; margin-top:4px; }
  .highlight { background:#eff6ff; border-left:4px solid #1e40af; padding:14px 18px; margin:16px 0; border-radius:0 8px 8px 0; }
  .highlight p { margin:0; color:#1e40af; font-size:13px; }
  .success { background:#f0fdf4; border-left:4px solid #16a34a; }
  .success p { color:#15803d; }
  code { background:#f1f5f9; color:#dc2626; padding:2px 6px; border-radius:4px; font-size:12px; font-family:monospace; }
  .page-break { page-break-after:always; margin:40px 0; border-top:1px dashed #e2e8f0; }
  @media print {
    body { padding:0; margin:0; }
    .page { padding:20px 30px; max-width:100%; box-shadow:none; }
    .cover { padding:40px 0 30px; }
    .kpi-grid { grid-template-columns:repeat(3,1fr); gap:8px; }
    .kpi-box { padding:10px; }
    .kpi-val { font-size:18px; }
    h2 { font-size:16px; margin:20px 0 10px; page-break-after:avoid; }
    h3 { font-size:13px; margin:14px 0 8px; page-break-after:avoid; }
    table { page-break-inside:avoid; font-size:11px; }
    tr { page-break-inside:avoid; }
    p { font-size:12px; }
    .highlight { page-break-inside:avoid; }
    .cover-title { font-size:20px; }
    .cover-logo { font-size:26px; }
    .cover-badge { font-size:11px; padding:5px 14px; }
  }
  .footer { text-align:center; margin-top:60px; padding-top:20px; border-top:2px solid #e2e8f0; font-size:11px; color:#94a3b8; }
</style>
</head>
<body>
<div class="page">

<div class="cover">
  <div class="cover-logo">GlobeTrack Logistics Ltd.</div>
  <div class="cover-sub">Big Data Engineering Project</div>
  <div class="cover-title">
    End-to-End Cloud Big Data Solution<br>
    for Real-Time Logistics Intelligence
  </div>
  <div>
    <span class="cover-badge">TCS iON AIP-135</span>
    <span class="cover-badge">AWS ap-south-1</span>
    <span class="cover-badge">Python 3.12</span>
    <span class="cover-badge">XGBoost + LightGBM + Random Forest</span>
  </div>
  <div class="cover-meta">
    <strong>Submitted by:</strong> Fatema Habil Saifuddin <br>
    <strong>MSc Statistics(Data Science) 2025-27 | Vishwakarma University.<br>
    <strong>Cloud Platform:</strong> AWS Asia Pacific Mumbai ap-south-1<br>
    <strong>Date:</strong> """ + datetime.now().strftime("%d %B %Y") + """<br>
    <strong>GitHub:</strong> github.com/Fatema-016/globetrack-logistics
  </div>
</div>

<h2>1. Executive Summary</h2>
<p>
This project implements an End-to-End Big Data Analytics pipeline
for GlobeTrack Logistics Ltd. — a logistics company operating across 8 major cities
in Maharashtra and Goa, India. The system collects, processes and analyses simulated data from
three heterogeneous real-time sources: vehicle IoT sensors, customer booking logs and
external weather and traffic APIs. 
</p>
<p>
The solution is built entirely on AWS cloud infrastructure in the ap-south-1 Mumbai
region.
</p>

<div class="kpi-grid">
  <div class="kpi-box"><div class="kpi-val">1.8M</div><div class="kpi-lbl">Raw records ingested</div></div>
  <div class="kpi-box"><div class="kpi-val">1.18M</div><div class="kpi-lbl">Records processed</div></div>
  <div class="kpi-box"><div class="kpi-box"><div class="kpi-val">3</div><div class="kpi-lbl">S3 data zones</div></div></div>
  <div class="kpi-box"><div class="kpi-val">94.5%</div><div class="kpi-lbl">Fleet health</div></div>
  <div class="kpi-box"><div class="kpi-val">27/27</div><div class="kpi-lbl">Tests passing</div></div>
</div>

<h2>2. Project Objective</h2>
<p>
The primary objective is to design and implement a scalable Big Data Analytics
solution on AWS cloud that efficiently handles large-scale heterogeneous datasets
for real-time insights and predictive analytics in logistics.
</p>
<table>
  <tr><th>Business Problem</th><th>Solution</th><th>Outcome</th></tr>
  <tr><td>Cannot predict delivery delays</td><td>XGBoost delay prediction</td><td>AUC 73.1%, Recall 56.8%</td></tr>
  <tr><td>No fleet health visibility</td><td>Tier-aware anomaly detection</td><td>32,763 anomalies, 94.5% healthy</td></tr>
  <tr><td>No real-time data pipeline</td><td>End-to-end AWS pipeline</td><td>1.8M records, Airflow orchestrated</td></tr>
  <tr><td>No monitoring or alerting</td><td>CloudWatch + SNS</td><td>5 alarms, live dashboard</td></tr>
</table>

<h2>3. System Architecture</h2>
<p>
The solution follows a 9-layer Lambda architecture pattern, separating batch and
streaming concerns across three S3 data zones with Apache Airflow orchestration.
</p>
<table>
  <tr><th>Layer</th><th>Component</th><th>Technology</th></tr>
  <tr><td>1. Data Sources</td><td>IoT sensors, bookings, weather</td><td>Python simulators</td></tr>
  <tr><td>2. Ingestion</td><td>5 simulators + manifest logger</td><td>boto3, AWS S3</td></tr>
  <tr><td>3. Raw Storage</td><td>globetrack-raw-data-lake</td><td>AWS S3 JSON and CSV</td></tr>
  <tr><td>4. ETL Processing</td><td>5 ETL pipelines</td><td>Pandas, PyArrow</td></tr>
  <tr><td>5. Processed Storage</td><td>globetrack-processed-data</td><td>AWS S3 Parquet Snappy</td></tr>
  <tr><td>6. ML and Analytics</td><td>3 ML models + anomaly detection</td><td>Scikit-learn, XGBoost, LightGBM,Random Forest</td></tr>
  <tr><td>7. Analytics Zone</td><td>globetrack-analytics-zone</td><td>AWS S3 Parquet</td></tr>
  <tr><td>8. Orchestration</td><td>14-task Airflow DAG</td><td>Apache Airflow 3.1.8</td></tr>
  <tr><td>9. Monitoring</td><td>5 alarms + dashboard</td><td>AWS CloudWatch + SNS</td></tr>
</table>

<div class="page-break"></div>

<h2>4. Data Sources and Ingestion</h2>
<p>
Three datasets ,each of which is architected to scale to 50GB+ in production environments.
The current 1.8M record synthetic dataset demonstrates the full pipeline capability.
</p>
<table>
  <tr><th>Dataset</th><th>Type</th><th>Records</th><th>Key Features</th></tr>
  <tr><td>Vehicle IoT Sensors</td><td>Telemetry</td><td>600,000</td><td>GPS, fuel, engine, speed, 3 vehicle tiers</td></tr>
  <tr><td>Customer Bookings</td><td>Operational Logs</td><td>600,000</td><td>Orders, cities, cargo, 8 delay rules</td></tr>
  <tr><td>Weather and Traffic</td><td>External Feeds</td><td>600,000</td><td>8 cities, climate patterns, congestion, currency</td></tr>
</table>

<h3>Vehicle Tier Design</h3>
<table>
  <tr><th>Tier</th><th>Vehicles</th><th>Fuel Efficiency</th><th>Engine Temp</th><th>Fault Probability</th></tr>
  <tr><td>OLD</td><td>GT-001 to GT-017</td><td>4 to 6.5 kmpl</td><td>95 to 108C</td><td>25%</td></tr>
  <tr><td>MID</td><td>GT-018 to GT-035</td><td>7 to 10 kmpl</td><td>82 to 94C</td><td>10%</td></tr>
  <tr><td>NEW</td><td>GT-036 to GT-050</td><td>11 to 15 kmpl</td><td>70 to 81C</td><td>3%</td></tr>
</table>

<h3>Delay Rules Injected</h3>
<table>
  <tr><th>Rule</th><th>Condition</th><th>Delay Probability</th></tr>
  <tr><td>1</td><td>Thunderstorm or Fog weather</td><td>90%</td></tr>
  <tr><td>2</td><td>Heavy Rain</td><td>75%</td></tr>
  <tr><td>3</td><td>Long haul over 500km + bad weather</td><td>85%</td></tr>
  <tr><td>4</td><td>Express + very heavy cargo over 9000kg</td><td>80%</td></tr>
  <tr><td>5</td><td>Perishables + long haul over 400km</td><td>70%</td></tr>
  <tr><td>6</td><td>Short haul under 200km + clear weather</td><td>92% delivered</td></tr>
  <tr><td>7</td><td>Pharmaceuticals priority</td><td>75% delivered</td></tr>
  <tr><td>8</td><td>Base distribution</td><td>45% delivered, 25% transit</td></tr>
</table>

<h2>5. ETL Processing Pipeline</h2>
<table>
  <tr><th>Pipeline</th><th>Input</th><th>Output</th><th>Key Features Engineered</th></tr>
  <tr><td>etl_iot_sensor.py</td><td>50 JSON files</td><td>Parquet 28 cols</td><td>fuel_efficiency_kmpl, engine_health_score, alert_severity</td></tr>
  <tr><td>etl_booking_logs.py</td><td>50 JSON files</td><td>Parquet 28 cols</td><td>is_delayed, revenue_per_km, weather_distance_risk</td></tr>
  <tr><td>etl_weather.py</td><td>40 JSON files</td><td>Parquet 25 cols</td><td>weather_severity, combined_risk_score, travel_advisory</td></tr>
  <tr><td>etl_enrichment.py</td><td>3 Parquet files</td><td>2 enriched Parquets</td><td>IoT + weather join, bookings + weather join</td></tr>
  <tr><td>etl_large_scale.py</td><td>120 CSV chunks</td><td>12 Parquet chunks</td><td>1.18M records, 6 chunks per dataset</td></tr>
</table>

<div class="page-break"></div>

<h2>6. Machine Learning Models</h2>

<h3>6.1 Delivery Delay Prediction</h3>
<p>
Three algorithms trained on 580,107 booking records.
</p>
<table>
  <tr><th>Model</th><th>Accuracy</th><th>AUC</th><th>Recall</th><th>Logistics Score</th></tr>
  <tr><td>XGBoost</td><td>69.0%</td><td>73.1%</td><td>56.8%</td><td>Best (0.4xAUC + 0.6xRecall)</td></tr>
  <tr><td>LightGBM</td><td>70.8%</td><td>72.9%</td><td>52.3%</td><td>Runner up</td></tr>
  <tr><td>Random Forest</td><td>69.4%</td><td>72.8%</td><td>55.5%</td><td>Feature importance</td></tr>
</table>

<h3>Key ML Engineering Decisions</h3>
<table>
  <tr><th>Decision</th><th>Implementation</th><th>Impact</th></tr>
  <tr><td>Model selection metric</td><td>0.4 x AUC + 0.6 x Recall</td><td>Logistics-focused, catches more delays</td></tr>
  <tr><td>No data leakage</td><td>Split before balance, no weather features</td><td>AUC 73% </td></tr>
  <tr><td>Decision threshold</td><td>0.45 instead of default 0.5</td><td>Better recall </td></tr>
  <tr><td>Class imbalance</td><td>scale_pos_weight, is_unbalance, balanced_subsample</td><td>Each model handles imbalance correctly</td></tr>
  <tr><td>Early stopping</td><td>10 rounds on XGBoost and LightGBM</td><td>Prevents overfitting on 580K rows</td></tr>
  <tr><td>Interaction features</td><td>cargo_stress_index, distance_cargo_risk, express_risk_score</td><td>Captures dependencies</td></tr>
</table>

<h3>6.2 IoT Anomaly Detection</h3>
<table>
  <tr><th>Tier</th><th>Model</th><th>Contamination</th><th>Anomalies</th><th>Rate</th></tr>
  <tr><td>OLD trucks</td><td>Isolation Forest + LOF</td><td>9%</td><td>18,376</td><td>9.0%</td></tr>
  <tr><td>MID trucks</td><td>Isolation Forest + LOF</td><td>5%</td><td>10,783</td><td>5.0%</td></tr>
  <tr><td>NEW trucks</td><td>Isolation Forest + LOF</td><td>2%</td><td>3,604</td><td>2.0%</td></tr>
</table>
<p>
Key finding: Anomalous vehicles average 82.76 km/h vs 72.58 km/h normal —
overspeeding is the primary anomaly pattern. Tier-aware detection prevents
NEW trucks from being misclassified due to their different performance profile.
</p>

<h2>7. Deployment and Orchestration</h2>

<h3>7.1 Apache Airflow DAG</h3>
<p>
14-task DAG scheduled daily at 6AM IST orchestrates the complete pipeline
from ingestion through ML to alerting.
</p>
<table>
  <tr><th>Stage</th><th>Tasks</th><th>Dependency</th></tr>
  <tr><td>Stage 1 Ingestion</td><td>3 simulators parallel</td><td>After start</td></tr>
  <tr><td>Stage 2 Manifest</td><td>1 manifest logger</td><td>After ingestion</td></tr>
  <tr><td>Stage 3 Large Gen</td><td>1 large dataset generator</td><td>After manifest</td></tr>
  <tr><td>Stage 4 ETL</td><td>3 ETL pipelines parallel</td><td>After large gen</td></tr>
  <tr><td>Stage 5 Enrichment</td><td>1 enrichment pipeline</td><td>After ETL</td></tr>
  <tr><td>Stage 6 Large ETL</td><td>1 large scale ETL</td><td>After enrichment</td></tr>
  <tr><td>Stage 7 ML</td><td>2 ML models parallel</td><td>After large ETL</td></tr>
  <tr><td>Stage 8 Analytics</td><td>1 analytics</td><td>After ML</td></tr>
  <tr><td>Stage 9 Alert</td><td>1 success notification</td><td>After analytics</td></tr>
</table>

<h2>8. Testing and Quality Assurance</h2>
<table>
  <tr><th>Test Suite</th><th>Cases</th><th>Result</th></tr>
  <tr><td>Suite 1 S3 Infrastructure</td><td>6</td><td>6/6 PASSED</td></tr>
  <tr><td>Suite 2 Data Ingestion</td><td>4</td><td>4/4 PASSED</td></tr>
  <tr><td>Suite 3 ETL Processing</td><td>5</td><td>5/5 PASSED</td></tr>
  <tr><td>Suite 4 ML Models</td><td>7</td><td>7/7 PASSED</td></tr>
  <tr><td>Suite 5 Analytics and Reporting</td><td>5</td><td>5/5 PASSED</td></tr>
  <tr><td><strong>Total</strong></td><td><strong>27</strong></td><td><strong>27/27 </strong></td></tr>
</table>

<h2>9. Key Business Insights</h2>
<table>
  <tr><th>Insight</th><th>Finding</th><th>Business Action</th></tr>
  <tr><td>Fleet health</td><td>94.5% healthy, OLD trucks 9% anomaly rate</td><td>Schedule maintenance for GT-001 to GT-017</td></tr>
  <tr><td>Delay drivers</td><td>Thunderstorm and Fog cause 90% delays</td><td>Avoid scheduling in severe weather</td></tr>
  <tr><td>Express risk</td><td>EXPRESS orders 53.94% delayed</td><td>Review Express commitments</td></tr>
  <tr><td>Revenue</td><td>Rs 6.43 Billion across 580,107 orders</td><td>Mumbai and Pune highest revenue cities</td></tr>
  <tr><td>Overspeeding</td><td>Anomalous vehicles avg 82.76 km/h</td><td>Implement speed policy</td></tr>
  <tr><td>Night shift</td><td>Night vehicles avg higher speed</td><td>Enhanced monitoring 8PM to 5AM</td></tr>
</table>

<h2>10. Conclusion</h2>
<p>
This project demonstrates a complete End-to-End Cloud
Big Data Solution for Real-Time Logistics Intelligence. The system ingests 1.8 million
records from three heterogeneous data sources, processes them through 5 ETL pipelines,
trains 3 machine learning models and delivers actionable insights through a Power BI
dashboard — all orchestrated via Apache Airflow and monitored through AWS CloudWatch.
</p>


<h2>11. Tech Stack</h2>
<table>
  <tr><th>Category</th><th>Technology</th><th>Version</th></tr>
  <tr><td>Cloud</td><td>AWS S3, Glue, Athena, CloudWatch, SNS</td><td>Latest</td></tr>
  <tr><td>Language</td><td>Python</td><td>3.12.7</td></tr>
  <tr><td>ETL</td><td>Pandas, PyArrow, Parquet Snappy</td><td>Latest</td></tr>
  <tr><td>ML</td><td>Scikit-learn, XGBoost, LightGBM</td><td>Latest</td></tr>
  <tr><td>Orchestration</td><td>Apache Airflow</td><td>3.1.8</td></tr>
  <tr><td>Monitoring</td><td>AWS CloudWatch + SNS</td><td>Latest</td></tr>
  <tr><td>Visualisation</td><td>Power BI Desktop</td><td>Latest</td></tr>
  <tr><td>Version Control</td><td>Git + GitHub</td><td>2.53.0</td></tr>
</table>

<div class="footer">
  GlobeTrack Logistics Ltd. | TCS iON AIP-135 | """ + datetime.now().strftime("%d %B %Y") + """ |
  github.com/Fatema-016/globetrack-logistics
</div>

</div>
</body>
</html>"""

    output_path = "docs/submission_report.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("=" * 55)
    print("  Submission Report Generated")
    print("=" * 55)
    print(f"  Saved: {output_path}")
    

if __name__ == "__main__":
    generate_report()