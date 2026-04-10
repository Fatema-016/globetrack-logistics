# GlobeTrack Logistics - Combined Full Report Generator
# Generates: Submission Report + Architecture Diagram + Runbook
# Step 4 - Final Documentation

from datetime import datetime
import json
import os

def load_report_data():
    ml_report      = {}
    anomaly_report = {}
    master_report  = {}

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

def generate_combined_report():
    ml_report, anomaly_report, master_report = load_report_data()

    fleet    = master_report.get("fleet_kpis",    {})
    delivery = master_report.get("delivery_kpis", {})
    best     = ml_report.get("best_metrics",      {})
    models   = ml_report.get("model_results",     {})

    now_str = datetime.now().strftime("%d %B %Y")

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TCS iON AIP 135 - End-to-End Cloud Big Data Solution for Real-Time Logistics Intelligence - Project Report.</title>
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

  .info-table { width:100%; border-collapse:collapse; margin:20px 0 40px; font-size:13px; }
  .info-table th { background:#1e40af; color:white; padding:10px 14px; text-align:left; }
  .info-table td { padding:10px 14px; border-bottom:1px solid #e2e8f0; color:#475569; }
  .info-table tr:nth-child(even) td { background:#f8fafc; }

  .toc { background:#f8fafc; border-radius:8px; padding:24px 30px; margin:30px 0 50px; }
  .toc h3 { color:#1e40af; margin-bottom:16px; font-size:16px; }
  .toc-item { display:flex; align-items:center; padding:5px 0; font-size:13px; color:#475569; border-bottom:1px dotted #e2e8f0; }
  .toc-item:last-child { border-bottom:none; }
  .toc-num { color:#1e40af; font-weight:700; margin-right:12px; min-width:24px; }

  h2 { font-size:20px; color:#1e40af; margin:40px 0 16px; padding:10px 16px; background:#f8fafc; border-left:4px solid #1e40af; border-radius:0 6px 6px 0; }
  h3 { font-size:15px; color:#334155; margin:22px 0 10px; }
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
  .warn { background:#fffbeb; border-left:4px solid #f59e0b; }
  .warn p { color:#b45309; }

  .page-break { page-break-after:always; margin:40px 0; border-top:1px dashed #e2e8f0; }
  .section-break { page-break-before:always; margin-top:0; padding-top:40px; }

  .footer { text-align:center; margin-top:60px; padding-top:20px; border-top:2px solid #e2e8f0; font-size:11px; color:#94a3b8; }

  /* Architecture Diagram Styles */
  .arch-page { max-width:1100px; margin:0 auto; padding:40px; }
  .arch-h1 { text-align:center; color:#1a365d; font-size:22px; margin-bottom:6px; }
  .arch-subtitle { text-align:center; color:#666; font-size:13px; margin-bottom:24px; }
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

  /* Runbook Styles */
  .runbook-page { max-width:900px; margin:0 auto; padding:50px; }
  .runbook-h1 { color:#1e293b; font-size:24px; margin-bottom:6px; }
  .runbook-meta { color:#64748b; font-size:13px; margin-bottom:30px; padding-bottom:16px; border-bottom:2px solid #f1f5f9; }
  .cmd { background:#1e293b; color:#86efac; padding:12px 16px; border-radius:8px; font-size:12px; font-family:monospace; margin:10px 0; line-height:1.8; }
  .alert-info  { background:#eff6ff; border-left:4px solid #3b82f6; padding:10px 14px; margin:10px 0; font-size:12px; color:#1d4ed8; border-radius:0 6px 6px 0; }
  .alert-warn  { background:#fffbeb; border-left:4px solid #f59e0b; padding:10px 14px; margin:10px 0; font-size:12px; color:#b45309; border-radius:0 6px 6px 0; }

  /* Power BI placeholder */
  .powerbi-section { max-width:900px; margin:0 auto; padding:50px; }
  .powerbi-placeholder { background:#f8fafc; border:2px dashed #cbd5e1; border-radius:12px; padding:40px; text-align:center; margin:20px 0; }
  .powerbi-placeholder p { color:#64748b; font-size:13px; margin-bottom:8px; }
  .powerbi-placeholder .ph-title { font-size:16px; font-weight:700; color:#334155; margin-bottom:10px; }

  @media print {
    body { padding:0; margin:0; }
    .page, .arch-page, .runbook-page, .powerbi-section { padding:20px 30px; max-width:100%; box-shadow:none; }
    .cover { padding:40px 0 30px; }
    .kpi-grid { grid-template-columns:repeat(3,1fr); gap:8px; }
    .kpi-box { padding:10px; }
    .kpi-val { font-size:18px; }
    h2 { font-size:15px; margin:20px 0 10px; page-break-after:avoid; }
    h3 { font-size:13px; margin:14px 0 8px; page-break-after:avoid; }
    table { page-break-inside:avoid; font-size:11px; }
    tr { page-break-inside:avoid; }
    p { font-size:12px; }
    .highlight { page-break-inside:avoid; }
    .cover-title { font-size:20px; }
    .cover-logo { font-size:26px; }
    .cover-badge { font-size:11px; padding:5px 14px; }
    .toc { page-break-inside:avoid; }
    .layer { page-break-inside:avoid; }
    .pipeline { gap:8px; }
    .cmd { font-size:10px; padding:8px 12px; }
  }
</style>
</head>
<body>

<!-- ============================================================ -->
<!--                    PART 1: SUBMISSION REPORT                 -->
<!-- ============================================================ -->

<div class="page">

<!-- COVER PAGE -->
<div class="cover">
  <div class="cover-logo">TCS iON AIP 135 End-to-End Cloud Big Data Solution for Real-Time Logistics Intelligence</div>
  <div class="cover-sub">Project Report</div>
  <div class="cover-title">
    GlobeTrack Logistics Ltd.
  </div>
  <div>
    <span class="cover-badge">TCS iON AIP-135</span>
    <span class="cover-badge">AWS ap-south-1</span>
    <span class="cover-badge">Python 3.12 | Apache Airflow</span>
    <span class="cover-badge">XGBoost + LightGBM + Random Forest</span>
  </div>
  <div class="cover-meta">
    <strong>Submitted by:</strong> Fatema Habil Saifuddin <br>
    <strong>Pursuing:</strong>MSc Statistics-Data Science 2025-27 <br>
    <strong>From:</strong>Vishwakarma University, Pune, Maharashtra, India.<br>
    <strong>Mentor:</strong>Dr. Raeesa Bashir <br>
    <strong>Project Title:</strong>TCS iON AIP 135 End-to-End Cloud Big Data Solution for Real-Time Logistics Intelligence<br>
    <strong>Company:</strong> GlobeTrack Logistics Ltd. (Simulated)<br>
    <strong>Cloud Platform:</strong> AWS Asia Pacific Mumbai ap-south-1<br>
    <strong>Date:</strong> """ + now_str + """<br>
    <strong>GitHub:</strong> github.com/Fatema-016/globetrack-logistics
  </div>
</div>

<!-- PROJECT INFO TABLE -->
<table class="info-table">
  <tr><th>Field</th><th>Details</th></tr>
  <tr><td>Industry Project Title</td><td>TCS iON AIP 135 End-to-End Cloud Big Data Solution for Real-Time Logistics Intelligence</td></tr>
  <tr><td>Name of the Company</td><td>GlobeTrack Logistics Ltd. (Simulated Enterprise)</td></tr>
  <tr><td>Project Environment</td><td>AWS Cloud — S3, Glue, Athena, CloudWatch, SNS — ap-south-1 Mumbai</td></tr>
  <tr><td>Start Date</td><td>22 March 2026</td></tr>
  <tr><td>End Date</td><td>""" + now_str + """</td></tr>
  <tr><td>Total Effort</td><td>136 hours across 4 steps</td></tr>
  <tr><td>Tools Used</td><td>Python 3.12, XGBoost, LightGBM, Scikit-learn, Apache Airflow 3.1.8, Power BI, AWS boto3, Pandas, PyArrow</td></tr>
</table>

<!-- TABLE OF CONTENTS -->
<div class="toc">
  <h3>Table of Contents</h3>
  <div class="toc-item"><span class="toc-num">1.</span> Acknowledgements</div>
  <div class="toc-item"><span class="toc-num">2.</span> Objective and Scope</div>
  <div class="toc-item"><span class="toc-num">3.</span> Problem Statement</div>
  <div class="toc-item"><span class="toc-num">4.</span> Existing Approaches</div>
  <div class="toc-item"><span class="toc-num">5.</span> Approach / Methodology - Tools and Technologies Used</div>
  <div class="toc-item"><span class="toc-num">6.</span> Workflow</div>
  <div class="toc-item"><span class="toc-num">7.</span> Assumptions</div>
  <div class="toc-item"><span class="toc-num">8.</span> Implementation - Data Collection, Processing Steps, Diagrams</div>
  <div class="toc-item"><span class="toc-num">9.</span> Solution Design</div>
  <div class="toc-item"><span class="toc-num">10.</span> Challenges and Opportunities</div>
  <div class="toc-item"><span class="toc-num">11.</span> Reflections on the Project</div>
  <div class="toc-item"><span class="toc-num">12.</span> Recommendations</div>
  <div class="toc-item"><span class="toc-num">13.</span> Outcome / Conclusion</div>
  <div class="toc-item"><span class="toc-num">14.</span> Enhancement Scope</div>
  <div class="toc-item"><span class="toc-num">15.</span> Link to Code and Executable File</div>
  <div class="toc-item"><span class="toc-num">16.</span> Research Questions and Responses</div>
  <div class="toc-item"><span class="toc-num">17.</span> References</div>
  <div class="toc-item"><span class="toc-num">A.</span> Appendix I — System Architecture Diagram</div>
  <div class="toc-item"><span class="toc-num">B.</span> Appendix II — Operational Runbook</div>
  <div class="toc-item"><span class="toc-num">C.</span> Appendix III — Power BI Dashboard Screenshots</div>
</div>

<div class="page-break"></div>

<!-- SECTION 1 -->
<h2>1. Acknowledgements</h2>
<p>
I would like to express my sincere gratitude to TCS iON for providing this
Industry Project opportunity. This project has been an invaluable learning
experience in real-world Big Data Engineering on cloud infrastructure.
I am grateful for the guidance provided through the TCS iON platform.
The project covered the complete data engineering lifecycle —
from raw data ingestion through ETL processing,
machine learning model development, pipeline orchestration and cloud monitoring.
</p>
<p>
I am thankful to Vishwakarma University for providing us this golden opportunity
of enhancing our learning journey through TCS iON. A special thanks to my mentor
Dr. Raeesa Bashir for her guidance.
</p>
<p>
Special acknowledgement to the open-source communities behind Python, Scikit-learn,
XGBoost, LightGBM, Apache Airflow and AWS for making industry-grade tools
accessible for learning and development.
</p>

<!-- SECTION 2 -->
<h2>2. Objective and Scope</h2>
<p>
The primary objective of this project is to design and implement a scalable,
End-to-End Big Data Analytics solution on AWS cloud that efficiently
handles large-scale heterogeneous datasets for real-time insights
and predictive analytics in the logistics domain.
</p>
<h3>Objectives</h3>
<table>
  <tr><th>Objective</th><th>Description</th></tr>
  <tr><td>Data Engineering</td><td>Ingest 1.8M records from 3 heterogeneous sources into AWS S3</td></tr>
  <tr><td>ETL Processing</td><td>Build 5 production-grade ETL pipelines outputting Parquet format</td></tr>
  <tr><td>Machine Learning</td><td>Train XGBoost, LightGBM and Random Forest for delay prediction</td></tr>
  <tr><td>Anomaly Detection</td><td>Tier-based IoT anomaly detection across 600K sensor readings</td></tr>
  <tr><td>Orchestration</td><td>14-task Apache Airflow DAG running daily at 6AM IST</td></tr>
  <tr><td>Monitoring</td><td>AWS CloudWatch with 12 metrics, 5 alarms and live dashboard</td></tr>
  <tr><td>Visualisation</td><td>3-page Power BI dashboard with 12 interactive charts</td></tr>
</table>

<h3>Scope</h3>
<p>
The project covers 8 cities across Maharashtra and Goa — Mumbai, Pune, Nashik,
Nagpur, Aurangabad, Kolhapur, Goa and Solapur. It simulates a fleet of 50
vehicles across 3 tiers (OLD, MID, NEW) and tracks 580,107 customer delivery
orders totalling Rs. 6.43 Billion in revenue.
</p>

<div class="kpi-grid">
  <div class="kpi-box"><div class="kpi-val">1.8M</div><div class="kpi-lbl">Records Ingested</div></div>
  <div class="kpi-box"><div class="kpi-val">69.0%</div><div class="kpi-lbl">XGBoost Accuracy</div></div>
  <div class="kpi-box"><div class="kpi-val">73.1%</div><div class="kpi-lbl">XGBoost AUC Score</div></div>
  <div class="kpi-box"><div class="kpi-val">56.8%</div><div class="kpi-lbl">XGBoost Recall</div></div>
  <div class="kpi-box"><div class="kpi-val">94.5%</div><div class="kpi-lbl">Fleet Health</div></div>
  <div class="kpi-box"><div class="kpi-val">27/27</div><div class="kpi-lbl">Tests Passing</div></div>
  <div class="kpi-box"><div class="kpi-val">32,763</div><div class="kpi-lbl">Anomalies Found</div></div>
  <div class="kpi-box"><div class="kpi-val">Rs6.43B</div><div class="kpi-lbl">Revenue Tracked</div></div>
</div>

<!-- SECTION 3 -->
<h2>3. Problem Statement</h2>
<p>
GlobeTrack Logistics Ltd. operates a fleet of 50 trucks across 8 cities in
Maharashtra and Goa, processing hundreds of thousands of delivery orders monthly.
The company faced four critical operational problems with no existing solution:
No delivery delay prediction capability, No real-time fleet health visibility,
No centralised data pipeline, No monitoring or alerting system.
</p>
<p>
The challenge was to build a unified, cloud-native Big Data platform that
ingests heterogeneous data streams, applies ML models in real-time and delivers
actionable business intelligence through automated dashboards and alerts.
</p>

<!-- SECTION 4 -->
<h2>4. Existing Approaches</h2>
<p>
Before this project, logistics companies typically used one of the following approaches:
</p>
<table>
  <tr><th>Approach</th><th>Limitation</th></tr>
  <tr><td>Manual Excel-based tracking</td><td>no real-time capability</td></tr>
  <tr><td>Traditional SQL databases</td><td>Cannot handle unstructured IoT and weather data at scale</td></tr>
  <tr><td>On-premise Hadoop clusters</td><td>complex maintenance</td></tr>
  <tr><td>Single ML model without feature engineering</td><td>AUC below 60%, high false negative rate on delay prediction</td></tr>
</table>
<p>
The GlobeTrack solution addresses all these limitations using a cloud-native,
serverless architecture on AWS with ML techniques including interaction
features, tier-aware anomaly detection and logistics-focused model selection.
</p>

<div class="page-break"></div>

<!-- SECTION 5 -->
<h2>5. Approach / Methodology - Tools and Technologies Used</h2>
<h3>Architecture Approach</h3>
<p>
The solution adopts a 9-layer Lambda architecture pattern separating batch and
streaming concerns across three S3 data zones.
</p>
<table>
  <tr><th>Category</th><th>Technology</th><th>Version</th><th>Purpose</th></tr>
  <tr><td>Cloud Platform</td><td>AWS S3, Glue, Athena, CloudWatch, SNS</td><td>Latest</td><td>Storage, catalog, monitoring</td></tr>
  <tr><td>Language</td><td>Python</td><td>3.12.7</td><td>All ETL and ML scripts</td></tr>
  <tr><td>ETL Libraries</td><td>Pandas, PyArrow, Parquet Snappy</td><td>Latest</td><td>Data transformation</td></tr>
  <tr><td>ML — Boosting</td><td>XGBoost</td><td>3.1.0</td><td>Primary delay prediction model</td></tr>
  <tr><td>ML — Boosting</td><td>LightGBM</td><td>4.6.0</td><td>Fast big data specialist model</td></tr>
  <tr><td>ML — Ensemble</td><td>Scikit-learn Random Forest</td><td>1.7.2</td><td>Feature importance model</td></tr>
  <tr><td>Anomaly Detection</td><td>Isolation Forest + Local Outlier Factor (LOF)</td><td>Scikit-learn</td><td>IoT sensor anomaly detection</td></tr>
  <tr><td>Orchestration</td><td>Apache Airflow</td><td>3.1.8</td><td>14-task daily pipeline DAG</td></tr>
  <tr><td>Monitoring</td><td>AWS CloudWatch + SNS</td><td>Latest</td><td>Metrics, alarms, alerts</td></tr>
  <tr><td>Visualisation</td><td>Power BI Desktop</td><td>Latest</td><td>3-page interactive dashboard</td></tr>
  <tr><td>Version Control</td><td>Git + GitHub</td><td>2.53.0</td><td>Source code management</td></tr>
</table>

<h3>ML Methodology</h3>
<p>
Model selection uses a Logistics Score = 0.4 x AUC + 0.6 x Recall. This
recall-weighted metric ensures the system prioritises catching delayed
deliveries over pure statistical accuracy — matching real business priorities.
Decision threshold tuned to 0.45 for better recall without
sacrificing accuracy. Weather features excluded to prevent data
leakage after initial experiments showed unrealistic AUC of 96%.
</p>

<!-- SECTION 6 -->
<h2>6. Workflow</h2>
<p>
The end-to-end pipeline runs daily at 6AM IST via Apache Airflow and consists
of 14 tasks across 9 stages:
</p>
<table>
  <tr><th>Stage</th><th>Tasks</th><th>Input</th><th>Output</th></tr>
  <tr><td>1. Ingestion</td><td>3 simulators (parallel)</td><td>Python generators</td><td>JSON/CSV to S3 raw zone</td></tr>
  <tr><td>2. Manifest</td><td>Manifest logger</td><td>S3 raw zone</td><td>Ingestion manifest CSV</td></tr>
  <tr><td>3. Large Generation</td><td>Large dataset generator</td><td>Python generators</td><td>60 CSV chunks per dataset</td></tr>
  <tr><td>4. ETL Processing</td><td>3 ETL pipelines (parallel)</td><td>JSON files + CSV chunks</td><td>Parquet Snappy to processed zone</td></tr>
  <tr><td>5. Enrichment</td><td>Enrichment pipeline</td><td>3 Parquet files</td><td>2 enriched Parquets to analytics zone</td></tr>
  <tr><td>6. Large ETL</td><td>Large scale ETL</td><td>120 CSV chunks</td><td>12 Parquet chunks to analytics zone</td></tr>
  <tr><td>7. ML Models</td><td>Delay prediction + anomaly (parallel)</td><td>580K booking records</td><td>best_model.pkl + anomaly_report.json</td></tr>
  <tr><td>8. Analytics</td><td>Master analytics</td><td>All outputs</td><td>master_report.json to S3</td></tr>
  <tr><td>9. Alert</td><td>Success notification</td><td>Pipeline completion</td><td>SNS email notification</td></tr>
</table>

<!-- SECTION 7 -->
<h2>7. Assumptions</h2>
<table>
  <tr><th>Assumption</th><th>Justification</th></tr>
  <tr><td>Synthetic data represents real patterns</td><td>8 logical delay rules injected matching real logistics scenarios</td></tr>
  <tr><td>50GB dataset architected, 1.8M demonstrated</td><td>Pipeline is architected to scale — chunked processing proves capability</td></tr>
  <tr><td>Night shift vehicles travel faster</td><td>Realistic — less traffic on Indian highways 8PM to 5AM</td></tr>
  <tr><td>Old trucks have higher fault probability (25%)</td><td>Based on industry data — vehicles over 10 years old have higher breakdown rates</td></tr>
  <tr><td>Weather features excluded from ML</td><td>Including them caused data leakage (AUC 96%) — excluded for realistic 73.1% AUC</td></tr>
  <tr><td>Threshold set at 0.45 not 0.5</td><td>Logistics recall-focused approach — better to flag more delays than miss them</td></tr>
</table>

<div class="page-break"></div>

<!-- SECTION 8 -->
<h2>8. Implementation - Data Collection, Processing Steps, Diagrams</h2>

<h3>8.1 Data Sources</h3>
<table>
  <tr><th>Dataset</th><th>Type</th><th>Records</th><th>Key Fields</th></tr>
  <tr><td>Vehicle IoT Sensors</td><td>Telemetry</td><td>600,000</td><td>GPS, fuel, engine temp, RPM, speed, 3 tiers</td></tr>
  <tr><td>Customer Booking Logs</td><td>Operational Logs</td><td>600,000</td><td>Order ID, cities, cargo type, status, freight charge</td></tr>
  <tr><td>Weather and Traffic APIs</td><td>External Feeds</td><td>600,000</td><td>City conditions, visibility, congestion, USD/INR rate</td></tr>
</table>

<h3>8.2 Vehicle Tier Design</h3>
<table>
  <tr><th>Tier</th><th>Vehicles</th><th>Fuel Efficiency</th><th>Engine Temp</th><th>Fault Probability</th></tr>
  <tr><td>OLD</td><td>GT-001 to GT-017</td><td>4 to 6.5 kmpl</td><td>95 to 108C</td><td>25%</td></tr>
  <tr><td>MID</td><td>GT-018 to GT-035</td><td>7 to 10 kmpl</td><td>82 to 94C</td><td>10%</td></tr>
  <tr><td>NEW</td><td>GT-036 to GT-050</td><td>11 to 15 kmpl</td><td>70 to 81C</td><td>3%</td></tr>
</table>

<h3>8.3 ETL Pipelines</h3>
<table>
  <tr><th>Pipeline</th><th>Input</th><th>Output Columns</th><th>Key Features Engineered</th></tr>
  <tr><td>etl_iot_sensor.py</td><td>50 JSON files</td><td>28 columns</td><td>fuel_efficiency_kmpl, engine_health_score, alert_severity</td></tr>
  <tr><td>etl_booking_logs.py</td><td>50 JSON files</td><td>28 columns</td><td>is_delayed, revenue_per_km, weather_distance_risk</td></tr>
  <tr><td>etl_weather.py</td><td>40 JSON files</td><td>25 columns</td><td>weather_severity, combined_risk_score, travel_advisory</td></tr>
  <tr><td>etl_enrichment.py</td><td>3 Parquet files</td><td>38 + 34 cols</td><td>IoT + weather join, bookings + weather join</td></tr>
  <tr><td>etl_large_scale.py</td><td>120 CSV chunks</td><td>12 Parquet chunks</td><td>1.18M records, cargo_stress_index, distance_cargo_risk</td></tr>
</table>

<h3>8.4 ML Results</h3>
<table>
  <tr><th>Model</th><th>Accuracy</th><th>AUC</th><th>Recall</th><th>Logistics Score</th></tr>
  <tr><td>XGBoost</td><td>69.0%</td><td>73.1%</td><td>56.8%</td><td>Best — 0.4xAUC + 0.6xRecall</td></tr>
  <tr><td>LightGBM</td><td>70.8%</td><td>72.9%</td><td>52.3%</td><td>Runner up</td></tr>
  <tr><td>Random Forest</td><td>69.4%</td><td>72.8%</td><td>55.5%</td><td>Feature importance</td></tr>
</table>

<h3>8.5 Anomaly Detection Results</h3>
<table>
  <tr><th>Vehicle Tier</th><th>Contamination</th><th>Anomalies</th><th>Rate</th><th>Physical Reason</th></tr>
  <tr><td>OLD (GT-001 to GT-017)</td><td>9%</td><td>18,376</td><td>9.0%</td><td>Worn engines, fuel leaks, vibration</td></tr>
  <tr><td>MID (GT-018 to GT-035)</td><td>5%</td><td>10,783</td><td>5.0%</td><td>Standard wear and tear</td></tr>
  <tr><td>NEW (GT-036 to GT-050)</td><td>2%</td><td>3,604</td><td>2.0%</td><td>Modern sensors, highly reliable</td></tr>
</table>

<h3>8.6 Test Results</h3>
<table>
  <tr><th>Test Suite</th><th>Cases</th><th>Result</th></tr>
  <tr><td>Suite 1 — S3 Infrastructure</td><td>6</td><td>6/6 PASSED</td></tr>
  <tr><td>Suite 2 — Data Ingestion</td><td>4</td><td>4/4 PASSED</td></tr>
  <tr><td>Suite 3 — ETL Processing</td><td>5</td><td>5/5 PASSED</td></tr>
  <tr><td>Suite 4 — ML Models</td><td>7</td><td>7/7 PASSED</td></tr>
  <tr><td>Suite 5 — Analytics and Reporting</td><td>5</td><td>5/5 PASSED</td></tr>
  <tr><td><strong>Total</strong></td><td><strong>27</strong></td><td><strong>27/27</strong></td></tr>
</table>

<!-- SECTION 9 -->
<h2>9. Solution Design</h2>
<p>
The solution is structured as a 9-layer cloud-native architecture deployed
entirely on AWS ap-south-1 Mumbai. Three S3 buckets form the data lakehouse:
raw, processed and analytics zones. Apache Airflow orchestrates 14 tasks daily
while CloudWatch provides real-time monitoring with 5 automated alarms.
</p>
<table>
  <tr><th>Layer</th><th>Component</th><th>Technology</th></tr>
  <tr><td>1. Sources</td><td>IoT sensors, bookings, weather</td><td>Python simulators</td></tr>
  <tr><td>2. Ingestion</td><td>5 simulators + manifest logger</td><td>boto3, AWS S3</td></tr>
  <tr><td>3. Raw Storage</td><td>globetrack-raw-data-lake</td><td>AWS S3 JSON and CSV</td></tr>
  <tr><td>4. ETL</td><td>5 ETL pipelines</td><td>Pandas, PyArrow</td></tr>
  <tr><td>5. Processed</td><td>globetrack-processed-data</td><td>Parquet Snappy</td></tr>
  <tr><td>6. ML</td><td>3 models + anomaly detection</td><td>XGBoost, LightGBM, Random Forest</td></tr>
  <tr><td>7. Analytics</td><td>globetrack-analytics-zone</td><td>Parquet + JSON reports</td></tr>
  <tr><td>8. Orchestration</td><td>14-task Airflow DAG</td><td>Apache Airflow 3.1.8</td></tr>
  <tr><td>9. Monitoring</td><td>5 alarms + dashboard</td><td>AWS CloudWatch + SNS</td></tr>
</table>

<div class="page-break"></div>

<!-- SECTION 10 -->
<h2>10. Challenges and Opportunities</h2>
<h3>Challenges Faced</h3>
<table>
  <tr><th>Challenge</th><th>How it was Resolved</th></tr>
  <tr><td>ML AUC unrealistically high at 96%</td><td>Identified data leakage from weather features — removed them, achieved realistic 73.1%</td></tr>
  <tr><td>Power BI charts showing uniform patterns</td><td>Injected realistic city demand weights, vehicle tier profiles and delay rules</td></tr>
  <tr><td>Uniform bar heights in visualisations</td><td>Added city-specific climate patterns and booking demand distributions</td></tr>
  <tr><td>Airflow RuntimeWarning on Windows</td><td>Expected Linux-native behaviour — DAG validated and code confirmed correct</td></tr>
  <tr><td>AWS IAM permissions denied</td><td>Added CloudWatchFullAccess, SNSFullAccess and AthenaFullAccess to IAM user</td></tr>
  <tr><td>S3 network connectivity errors</td><td>Internet connectivity issue — resolved by reconnecting and retrying</td></tr>
</table>

<h3>Opportunities Identified</h3>
<table>
  <tr><th>Opportunity</th><th>Business Value</th></tr>
  <tr><td>Real-time streaming with Kinesis</td><td>Sub-second delay alerts instead of batch processing</td></tr>
  <tr><td>Dynamic route optimisation ML</td><td>Reduce delay rate from 35.6% by optimising routes dynamically</td></tr>
  <tr><td>Predictive maintenance scheduling</td><td>Flag Old trucks before breakdown using anomaly trends</td></tr>
  <tr><td>Weather API integration (real)</td><td>Replace simulated weather with live IMD or OpenWeatherMap data</td></tr>
</table>

<!-- SECTION 11 -->
<h2>11. Reflections on the Project</h2>
<p>
This project provided hands-on experience with the complete Big Data Engineering
lifecycle. Several key learnings emerged through the process of building a real
system that had to work correctly:
</p>
<p>
The most important lesson was about data leakage in ML. The initial model achieved
96% AUC which appeared impressive but was completely unrealistic. Diagnosing this
required understanding that weather features were directly used to generate delay
labels — the model was reading the answer rather than learning patterns. Removing
those features and retraining produced a genuine 73.1% AUC which is both realistic
and defensible.
</p>
<p>
Building for Power BI visualisation highlighted the importance of designing data
with downstream consumers in mind. Purely random simulation produced uniform
charts with no business insight. Injecting realistic patterns — city demand
weights, delay rules, seasonal variations — transformed the dashboard from
decorative to genuinely informative.
</p>

<!-- SECTION 12 -->
<h2>12. Recommendations</h2>
<table>
  <tr><th>Recommendation</th><th>Priority</th><th>Expected Impact</th></tr>
  <tr><td>Schedule maintenance for GT-001 to GT-017 (OLD tier)</td><td>HIGH</td><td>Reduce OLD truck anomaly rate from 9% to under 5%</td></tr>
  <tr><td>Review EXPRESS delivery commitments</td><td>HIGH</td><td>EXPRESS orders show 53.94% delay - causing customer dissatisfaction</td></tr>
  <tr><td>Implement speed governance policy</td><td>HIGH</td><td>Anomalous vehicles average 82.76 km/h — safety risk requiring immediate action</td></tr>
  <tr><td>Avoid scheduling in Thunderstorm and Fog conditions</td><td>MEDIUM</td><td>These conditions cause 90% delay rate — rescheduling saves revenue</td></tr>
  <tr><td>Enhanced monitoring 8PM to 5AM night shift</td><td>MEDIUM</td><td>Night vehicles travel faster — higher accident and breakdown risk</td></tr>
  <tr><td>Upgrade OLD fleet to NEW tier vehicles</td><td>LOW</td><td>NEW trucks show 2% anomaly rate vs 9% for OLD — 78% reduction in incidents</td></tr>
</table>

<!-- SECTION 13 -->
<h2>13. Outcome / Conclusion</h2>
<p>
This project demonstrates a complete, End-to-End Cloud Big Data Solution
for Real-Time Logistics Intelligence. All 4 steps from
the TCS iON AIP-135 specification were completed within framework.
</p>

<div class="highlight success">
  <p>
    27/27 automated test cases passed. XGBoost achieves AUC 73.1%
    and Recall 56.8% with no data leakage. Tier-aware anomaly detection correctly
    identifies OLD trucks at 9% vs NEW trucks at 2%.
    Fleet health 94.5%. Total revenue tracked Rs 6.43 Billion.
  </p>
</div>

<!-- SECTION 14 -->
<h2>14. Enhancement Scope</h2>
<table>
  <tr><th>Enhancement</th><th>Technology</th><th>Business Value</th></tr>
  <tr><td>Real-time streaming ingestion</td><td>AWS Kinesis Data Streams</td><td>Sub-second IoT processing instead of batch</td></tr>
  <tr><td>Deep learning delay prediction</td><td>TensorFlow LSTM</td><td>Capture sequential booking patterns for higher AUC</td></tr>
  <tr><td>Live weather API integration</td><td>IMD or OpenWeatherMap API</td><td>Real-time delay risk instead of simulated weather</td></tr>
  <tr><td>Geospatial route analysis</td><td>AWS Location Service + Folium</td><td>Map-based route visualisation and optimisation</td></tr>
  <tr><td>Natural Language Query interface</td><td>AWS Bedrock + Claude API</td><td>Ask questions about fleet data in simple English</td></tr>
  <tr><td>Mobile alert app</td><td>AWS SNS + React Native</td><td>Push notifications to drivers and fleet managers</td></tr>
  <tr><td>Auto-scaling ETL</td><td>AWS Glue + Spark</td><td>Handle true 50GB+ datasets with elastic compute</td></tr>
</table>

<!-- SECTION 15 -->
<h2>15. Link to Code and Executable File</h2>
<table>
  <tr><th>Resource</th><th>Link</th></tr>
  <tr><td>GitHub Repository</td><td>github.com/Fatema-016/globetrack-logistics</td></tr>
  <tr><td>AWS S3 Raw Data Lake</td><td>s3://globetrack-raw-data-lake (ap-south-1)</td></tr>
  <tr><td>AWS S3 Processed Data</td><td>s3://globetrack-processed-data (ap-south-1)</td></tr>
  <tr><td>AWS S3 Analytics Zone</td><td>s3://globetrack-analytics-zone (ap-south-1)</td></tr>
  <tr><td>CloudWatch Dashboard</td><td>AWS Console — GlobeTrack-Logistics-Dashboard</td></tr>
  <tr><td>Architecture Diagram</td><td>docs/architecture_diagram.html</td></tr>
  <tr><td>Operational Runbook</td><td>docs/runbook.html</td></tr>
  <tr><td>Power BI Dashboard</td><td>dashboard/GlobeTrack_Logistics_Dashboard.pbix</td></tr>
</table>

<!-- SECTION 16 -->
<h2>16. Research Questions and Responses</h2>
<table>
  <tr><th>Research Question</th><th>Response</th></tr>
  <tr><td>Can ML predict logistics delays with meaningful accuracy on synthetic data?</td><td>Yes — XGBoost achieves AUC 73.1% and Recall 56.8% after removing data leakage and applying interaction features</td></tr>
  <tr><td>Does vehicle age (tier) significantly impact fleet health metrics?</td><td>Yes — OLD trucks show 9% anomaly rate vs 2% for NEW trucks. Fuel level averages 40% vs 74%. Engine health 72.9 vs 96.2 out of 100</td></tr>
  <tr><td>What is the primary driver of delivery delays?</td><td>Weather conditions — Thunderstorm and Fog cause 90% delay probability. Long haul routes over 500km with bad weather cause 85% delays</td></tr>
  <tr><td>Is tier-aware anomaly detection necessary?</td><td>Yes — a single contamination rate misclassified NEW trucks as anomalous (12.3%) because their superior metrics deviated from the OLD truck-dominated baseline</td></tr>
  <tr><td>Can a recall-focused ML selection metric improve logistics outcomes?</td><td>Yes — using 0.4 x AUC + 0.6 x Recall selects XGBoost which catches 56.8% of delayed orders vs LightGBM which only catches 52.3% despite higher accuracy</td></tr>
  <tr><td>Does EXPRESS priority actually mean faster delivery?</td><td>No — EXPRESS orders show 53.94% delay rate vs 46.06% for NORMAL, suggesting commitments are unrealistic given current fleet capacity</td></tr>
</table>

<!-- SECTION 17 -->
<h2>17. References</h2>
<table>
  <tr><th>Reference</th><th>Source</th></tr>
  <tr><td>XGBoost Documentation</td><td>xgboost.readthedocs.io</td></tr>
  <tr><td>LightGBM Documentation</td><td>lightgbm.readthedocs.io</td></tr>
  <tr><td>Scikit-learn User Guide</td><td>scikit-learn.org/stable/user_guide</td></tr>
  <tr><td>Apache Airflow Documentation</td><td>airflow.apache.org/docs</td></tr>
  <tr><td>AWS S3 Developer Guide</td><td>docs.aws.amazon.com/s3</td></tr>
  <tr><td>AWS CloudWatch User Guide</td><td>docs.aws.amazon.com/cloudwatch</td></tr>
  <tr><td>PyArrow Documentation</td><td>arrow.apache.org/docs/python</td></tr>
  <tr><td>Pandas Documentation</td><td>pandas.pydata.org/docs</td></tr>
  <tr><td>Power BI Documentation</td><td>learn.microsoft.com/power-bi</td></tr>
  <tr><td>TCS iON Industry Project Guidelines</td><td>Provided on TCS iON platform.</td></tr>
</table>

<div class="footer">
  Fatema Habil Saifuddin | MSc Statistics Data Science 2025-27 | Vishwakarma University,Pune. """ + now_str + """ |
  github.com/Fatema-016/globetrack-logistics
</div>

</div>

<!-- ============================================================ -->
<!--           APPENDIX I: ARCHITECTURE DIAGRAM                   -->
<!-- ============================================================ -->

<div class="page-break"></div>

<div class="arch-page">
  <h1 class="arch-h1" style="text-align:center;color:#1a365d;font-size:22px;margin-bottom:6px;">
    Appendix I — System Architecture Diagram
  </h1>
  <div class="arch-subtitle">TCS iON AIP 135 End-to-End Cloud Big Data Solution for Real-Time Logistics Intelligence | GlobeTrack Logistics Ltd.</div>

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
      <div class="layer-title">Layer 2 - Data Ingestion</div>
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
      <div class="layer-title">Layer 4 - ETL Processing</div>
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
      <div class="layer-title">Layer 6 - ML and Analytics</div>
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
    <div class="layer l-orch">
      <div class="layer-title">Layer 8 - Orchestration</div>
      <div class="boxes">
        <div class="box">Apache Airflow DAG<div class="sub">14 tasks, daily 6AM</div></div>
        <div class="box">AWS Step Functions<div class="sub">Pipeline state machine</div></div>
        <div class="box">Scheduled Retraining<div class="sub">Daily ML model update</div></div>
      </div>
    </div>
    <div class="arrow">↓</div>
    <div class="layer l-monitor">
      <div class="layer-title">Layer 9 - Monitoring and Alerting</div>
      <div class="boxes">
        <div class="box">CloudWatch<div class="sub">12 metrics, 5 alarms</div></div>
        <div class="box">SNS Alerts<div class="sub">Email notifications</div></div>
        <div class="box">Dashboard<div class="sub">4 widget live view</div></div>
        <div class="box">Test Suite<div class="sub">27/27 passing</div></div>
      </div>
    </div>
  </div>

  <div class="footer" style="margin-top:20px;">
    GlobeTrack Logistics Ltd. - TCS iON AIP-135 Industry Project - Fatema Habil Saifuddin - MSc Statistics(DS)|Vishwakarma University """ + now_str + """
  </div>
</div>

<!-- ============================================================ -->
<!--              APPENDIX II: OPERATIONAL RUNBOOK                -->
<!-- ============================================================ -->

<div class="page-break"></div>

<div class="runbook-page">
  <h1 class="runbook-h1">Appendix II — Operational Runbook</h1>
  <div class="runbook-meta">TCS iON AIP 135 End-to-End Cloud Big Data Solution for Real-Time Logistics Intelligence | GlobeTrack Logistics Ltd. """ + now_str + """</div>

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
# Output: json</div>

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

  <div class="footer">
    Fatema Habil Saifuddin - MSc Statistics(DS)|Vishwakarma University """ + now_str + """
  </div>
</div>

<!-- ============================================================ -->
<!--         APPENDIX III: POWER BI DASHBOARD SCREENSHOTS         -->
<!-- ============================================================ -->

<div class="page-break"></div>

<div class="powerbi-section">
  <h1 style="color:#1a365d;font-size:22px;margin-bottom:6px;">
    Appendix III — Power BI Dashboard Screenshots
  </h1>
  <p style="color:#64748b;font-size:13px;margin-bottom:24px;">
    GlobeTrack Logistics Ltd. | 3-Page Dashboard | """ + now_str + """
  </p>

  <h2>Page 1 — Fleet Overview</h2>
  <img src="powerbi_page1.png" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;">
    <div class="ph-title">Fleet Overview Dashboard</div>
    
    
  </div>

  <div class="page-break"></div>

  <h2>Page 2 — Delivery Analytics</h2>
  <img src="powerbi_page2.png" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;">
    <div class="ph-title">Delivery Analytics Dashboard</div>
    
    
  </div>

  <div class="page-break"></div>

  <h2>Page 3 — Route and Tier Intelligence</h2>
  <img src="powerbi_page3.png" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;">
    <div class="ph-title">Route and Tier Intelligence Dashboard</div>
    
    
  </div>

</div>

</body>
</html>"""

    output_path = "docs/submission_report.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    
    print("  GlobeTrack - Full Combined Report Generated")
    
if __name__ == "__main__":
    generate_combined_report()