# GlobeTrack Logistics - AWS CloudWatch Monitoring & Alerts
# Step 4 - Deployment & Monitoring

import boto3
import json
from datetime import datetime, timezone

REGION              = "ap-south-1"
S3_BUCKET_ANALYTICS = "globetrack-analytics-zone"
SNS_TOPIC_NAME      = "globetrack-pipeline-alerts"

cloudwatch = boto3.client("cloudwatch", region_name=REGION)
sns_client = boto3.client("sns",        region_name=REGION)

def create_sns_topic():
    print("\n[1/5] Creating SNS alert topic...")
    try:
        response  = sns_client.create_topic(Name=SNS_TOPIC_NAME)
        topic_arn = response["TopicArn"]
        print(f"  SNS Topic: {topic_arn}")
        return topic_arn
    except Exception as e:
        print(f"  SNS failed: {e}")
        return None

def publish_pipeline_metrics():
    print("\n[2/5] Publishing metrics to CloudWatch...")

    now     = datetime.now(timezone.utc)
    metrics = [
        {
            "MetricName": "RecordsIngested",
            "Dimensions": [{"Name":"Pipeline","Value":"GlobeTrack-Ingestion"}],
            "Value": 1800000, "Unit": "Count", "Timestamp": now,
        },
        {
            "MetricName": "IngestionSuccessRate",
            "Dimensions": [{"Name":"Pipeline","Value":"GlobeTrack-Ingestion"}],
            "Value": 100.0, "Unit": "Percent", "Timestamp": now,
        },
        {
            "MetricName": "RecordsProcessed",
            "Dimensions": [{"Name":"Pipeline","Value":"GlobeTrack-ETL"}],
            "Value": 1180107, "Unit": "Count", "Timestamp": now,
        },
        {
            "MetricName": "ETLSuccessRate",
            "Dimensions": [{"Name":"Pipeline","Value":"GlobeTrack-ETL"}],
            "Value": 100.0, "Unit": "Percent", "Timestamp": now,
        },
        {
            "MetricName": "ModelAUCScore",
            "Dimensions": [{"Name":"Pipeline","Value":"GlobeTrack-ML"}],
            "Value": 73.13, "Unit": "Percent", "Timestamp": now,
        },
        {
            "MetricName": "ModelRecallScore",
            "Dimensions": [{"Name":"Pipeline","Value":"GlobeTrack-ML"}],
            "Value": 56.84, "Unit": "Percent", "Timestamp": now,
        },
        {
            "MetricName": "AnomaliesDetected",
            "Dimensions": [{"Name":"Pipeline","Value":"GlobeTrack-ML"}],
            "Value": 32763, "Unit": "Count", "Timestamp": now,
        },
        {
            "MetricName": "FleetHealthScore",
            "Dimensions": [{"Name":"Fleet","Value":"GlobeTrack-Fleet"}],
            "Value": 94.5, "Unit": "Percent", "Timestamp": now,
        },
        {
            "MetricName": "ActiveVehicles",
            "Dimensions": [{"Name":"Fleet","Value":"GlobeTrack-Fleet"}],
            "Value": 50, "Unit": "Count", "Timestamp": now,
        },
        {
            "MetricName": "DelayRate",
            "Dimensions": [{"Name":"Delivery","Value":"GlobeTrack-Delivery"}],
            "Value": 35.6, "Unit": "Percent", "Timestamp": now,
        },
        {
            "MetricName": "TotalOrders",
            "Dimensions": [{"Name":"Delivery","Value":"GlobeTrack-Delivery"}],
            "Value": 580107, "Unit": "Count", "Timestamp": now,
        },
        {
            "MetricName": "TotalRevenue",
            "Dimensions": [{"Name":"Delivery","Value":"GlobeTrack-Delivery"}],
            "Value": 6430823008, "Unit": "Count", "Timestamp": now,
        },
    ]

    for i in range(0, len(metrics), 10):
        cloudwatch.put_metric_data(
            Namespace  = "GlobeTrack/Pipeline",
            MetricData = metrics[i:i+10],
        )

    print(f"  Published {len(metrics)} metrics")
    print(f"  Namespace: GlobeTrack/Pipeline")
    return metrics

def create_cloudwatch_alarms(topic_arn):
    print("\n[3/5] Creating CloudWatch alarms...")

    alarms = [
        {
            "AlarmName":          "GlobeTrack-FleetHealth-Critical",
            "AlarmDescription":   "Fleet health below 85% — urgent inspection needed",
            "MetricName":         "FleetHealthScore",
            "Namespace":          "GlobeTrack/Pipeline",
            "Dimensions":         [{"Name":"Fleet","Value":"GlobeTrack-Fleet"}],
            "Period":             300,
            "EvaluationPeriods":  2,
            "Threshold":          85.0,
            "ComparisonOperator": "LessThanThreshold",
            "Statistic":          "Average",
            "TreatMissingData":   "notBreaching",
        },
        {
            "AlarmName":          "GlobeTrack-DelayRate-High",
            "AlarmDescription":   "Delay rate exceeded 50% — investigate routes",
            "MetricName":         "DelayRate",
            "Namespace":          "GlobeTrack/Pipeline",
            "Dimensions":         [{"Name":"Delivery","Value":"GlobeTrack-Delivery"}],
            "Period":             300,
            "EvaluationPeriods":  2,
            "Threshold":          50.0,
            "ComparisonOperator": "GreaterThanThreshold",
            "Statistic":          "Average",
            "TreatMissingData":   "notBreaching",
        },
        {
            "AlarmName":          "GlobeTrack-Ingestion-Failed",
            "AlarmDescription":   "Ingestion success below 95%",
            "MetricName":         "IngestionSuccessRate",
            "Namespace":          "GlobeTrack/Pipeline",
            "Dimensions":         [{"Name":"Pipeline","Value":"GlobeTrack-Ingestion"}],
            "Period":             300,
            "EvaluationPeriods":  1,
            "Threshold":          95.0,
            "ComparisonOperator": "LessThanThreshold",
            "Statistic":          "Average",
            "TreatMissingData":   "breaching",
        },
        {
            "AlarmName":          "GlobeTrack-MLModel-Degraded",
            "AlarmDescription":   "ML AUC below 60% — retraining required",
            "MetricName":         "ModelAUCScore",
            "Namespace":          "GlobeTrack/Pipeline",
            "Dimensions":         [{"Name":"Pipeline","Value":"GlobeTrack-ML"}],
            "Period":             3600,
            "EvaluationPeriods":  1,
            "Threshold":          60.0,
            "ComparisonOperator": "LessThanThreshold",
            "Statistic":          "Average",
            "TreatMissingData":   "notBreaching",
        },
        {
            "AlarmName":          "GlobeTrack-Anomaly-Spike",
            "AlarmDescription":   "Anomalies exceeded 10% — fleet inspection needed",
            "MetricName":         "AnomaliesDetected",
            "Namespace":          "GlobeTrack/Pipeline",
            "Dimensions":         [{"Name":"Pipeline","Value":"GlobeTrack-ML"}],
            "Period":             300,
            "EvaluationPeriods":  2,
            "Threshold":          60000,
            "ComparisonOperator": "GreaterThanThreshold",
            "Statistic":          "Sum",
            "TreatMissingData":   "notBreaching",
        },
    ]

    for alarm in alarms:
        config = dict(alarm)
        if topic_arn:
            config["AlarmActions"] = [topic_arn]
            config["OKActions"]    = [topic_arn]
        cloudwatch.put_metric_alarm(**config)
        print(f"  Alarm created: {alarm['AlarmName']}")

    print(f"  Total alarms: {len(alarms)}")
    return alarms

def create_dashboard():
    print("\n[4/5] Creating CloudWatch dashboard...")

    body = {
        "widgets": [
            {
                "type":"metric","width":12,"height":6,
                "properties":{
                    "title":"Fleet Health & Vehicles",
                    "metrics":[
                        ["GlobeTrack/Pipeline","FleetHealthScore","Fleet","GlobeTrack-Fleet"],
                        ["GlobeTrack/Pipeline","ActiveVehicles","Fleet","GlobeTrack-Fleet"],
                    ],
                    "period":300,"view":"timeSeries","region":REGION,
                },
            },
            {
                "type":"metric","width":12,"height":6,
                "properties":{
                    "title":"Delivery Performance",
                    "metrics":[
                        ["GlobeTrack/Pipeline","TotalOrders","Delivery","GlobeTrack-Delivery"],
                        ["GlobeTrack/Pipeline","DelayRate","Delivery","GlobeTrack-Delivery"],
                    ],
                    "period":300,"view":"timeSeries","region":REGION,
                },
            },
            {
                "type":"metric","width":12,"height":6,
                "properties":{
                    "title":"Pipeline Ingestion & ETL",
                    "metrics":[
                        ["GlobeTrack/Pipeline","RecordsIngested","Pipeline","GlobeTrack-Ingestion"],
                        ["GlobeTrack/Pipeline","RecordsProcessed","Pipeline","GlobeTrack-ETL"],
                        ["GlobeTrack/Pipeline","IngestionSuccessRate","Pipeline","GlobeTrack-Ingestion"],
                    ],
                    "period":300,"view":"timeSeries","region":REGION,
                },
            },
            {
                "type":"metric","width":12,"height":6,
                "properties":{
                    "title":"ML Model Performance",
                    "metrics":[
                        ["GlobeTrack/Pipeline","ModelAUCScore","Pipeline","GlobeTrack-ML"],
                        ["GlobeTrack/Pipeline","ModelRecallScore","Pipeline","GlobeTrack-ML"],
                        ["GlobeTrack/Pipeline","AnomaliesDetected","Pipeline","GlobeTrack-ML"],
                    ],
                    "period":3600,"view":"timeSeries","region":REGION,
                },
            },
        ]
    }

    cloudwatch.put_dashboard(
        DashboardName = "GlobeTrack-Logistics-Dashboard",
        DashboardBody = json.dumps(body),
    )
    print(f"  Dashboard: GlobeTrack-Logistics-Dashboard")
    print(f"  Widgets: Fleet, Delivery, Pipeline, ML")

def save_config(metrics, alarms, topic_arn):
    print("\n[5/5] Saving monitoring config...")

    config = {
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "namespace":       "GlobeTrack/Pipeline",
        "dashboard":       "GlobeTrack-Logistics-Dashboard",
        "sns_topic_arn":   topic_arn,
        "metrics_count":   len(metrics),
        "alarms_count":    len(alarms),
        "alarms": [
            {
                "name":      a["AlarmName"],
                "metric":    a["MetricName"],
                "threshold": a["Threshold"],
                "operator":  a["ComparisonOperator"],
            }
            for a in alarms
        ],
    }

    local_path = "monitoring/cloudwatch_config.json"
    with open(local_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"  Config saved: {local_path}")
    print(f"\n  Summary:")
    print(f"    Metrics:   {len(metrics)}")
    print(f"    Alarms:    {len(alarms)}")
    print(f"    Dashboard: GlobeTrack-Logistics-Dashboard")

def run_monitoring_setup():
    print("=" * 55)
    print("  GlobeTrack - CloudWatch Monitoring Setup")
    print("=" * 55)

    topic_arn = create_sns_topic()
    metrics   = publish_pipeline_metrics()
    alarms    = create_cloudwatch_alarms(topic_arn)
    create_dashboard()
    save_config(metrics, alarms, topic_arn)

    print("\n" + "=" * 55)
    print("  MONITORING SETUP COMPLETE!")
    print("=" * 55)

if __name__ == "__main__":
    run_monitoring_setup()