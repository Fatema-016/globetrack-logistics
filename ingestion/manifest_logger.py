# GlobeTrack Logistics - Ingestion Manifest Logger
# Tracks every file uploaded to S3 with metadata
# Step 1 - Data Collection & Ingestion

import boto3
import pandas as pd
from datetime import datetime, timezone
from io import StringIO

S3_BUCKET = "globetrack-raw-data-lake"
REGION    = "ap-south-1"
s3_client = boto3.client("s3", region_name=REGION)

def build_manifest():
    folders = ["iot-sensor-data", "booking-logs", "weather-data"]
    records = []

    print("=" * 55)
    print("  GlobeTrack - Building Ingestion Manifest")
    print("=" * 55)

    for folder in folders:
        print(f"\n  Scanning {folder}...")

        paginator = s3_client.get_paginator("list_objects_v2")
        pages     = paginator.paginate(
                        Bucket = S3_BUCKET,
                        Prefix = f"{folder}/"
                    )

        count = 0
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                records.append({
                    "file_name":           key.split("/")[-1],
                    "s3_path":             f"s3://{S3_BUCKET}/{key}",
                    "data_source":         folder,
                    "file_size_bytes":     obj["Size"],
                    "last_modified":       obj["LastModified"].isoformat(),
                    "ingestion_timestamp": datetime.now(
                                               timezone.utc
                                           ).isoformat(),
                    "status":              "SUCCESS",
                    "bucket":              S3_BUCKET,
                    "region":              REGION,
                })
                count += 1

        print(f"  Found {count} files in {folder}")

    df = pd.DataFrame(records)
    print(f"\n  Total files tracked: {len(df)}")

    # Save manifest to S3
    csv_buffer   = StringIO()
    df.to_csv(csv_buffer, index=False)
    manifest_key = (
        f"ingestion_manifest/"
        f"manifest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    s3_client.put_object(
        Bucket      = S3_BUCKET,
        Key         = manifest_key,
        Body        = csv_buffer.getvalue(),
        ContentType = "text/csv",
    )

    # Save locally
    local_path = "docs/ingestion_manifest.csv"
    df.to_csv(local_path, index=False)

    print(f"  Manifest saved to S3: {manifest_key}")
    print(f"  Manifest saved locally: {local_path}")
    print("\n" + "=" * 55)
    print("  MANIFEST COMPLETE!")
    print("=" * 55)

    return df

if __name__ == "__main__":
    build_manifest()