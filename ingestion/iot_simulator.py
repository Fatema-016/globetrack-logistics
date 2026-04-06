# GlobeTrack Logistics - IoT Sensor Simulator (Small Scale)
# Simulates real-time vehicle telemetry — Step 1 demonstration
# Large scale data generated via generate_large_datasets.py

import json
import random
import time
import boto3
from datetime import datetime, timezone
import numpy as np

S3_BUCKET = "globetrack-raw-data-lake"
S3_FOLDER = "iot-sensor-data"
REGION    = "ap-south-1"
s3_client = boto3.client("s3", region_name=REGION)

VEHICLES = {
    "GT-001": {"tier":"OLD",  "driver":"Rajesh Kumar",  "route":"Mumbai-Nagpur"},
    "GT-002": {"tier":"OLD",  "driver":"Suresh Yadav",  "route":"Mumbai-Goa"},
    "GT-003": {"tier":"OLD",  "driver":"Amit Singh",    "route":"Pune-Nagpur"},
    "GT-004": {"tier":"MID",  "driver":"Vikram Sharma", "route":"Mumbai-Pune"},
    "GT-005": {"tier":"MID",  "driver":"Ravi Patel",    "route":"Nashik-Nagpur"},
    "GT-006": {"tier":"MID",  "driver":"Manoj Gupta",   "route":"Mumbai-Aurangabad"},
    "GT-007": {"tier":"NEW",  "driver":"Arjun Verma",   "route":"Pune-Kolhapur"},
    "GT-008": {"tier":"NEW",  "driver":"Deepak Tiwari", "route":"Mumbai-Nashik"},
    "GT-009": {"tier":"NEW",  "driver":"Sanjay Mishra", "route":"Goa-Pune"},
    "GT-010": {"tier":"NEW",  "driver":"Rohit Chauhan", "route":"Kolhapur-Mumbai"},
}

TIER_PARAMS = {
    "OLD": {"fuel_range":(15,65),  "temp_range":(92,110), "rpm_range":(2800,3800), "fault_prob":0.25},
    "MID": {"fuel_range":(30,80),  "temp_range":(82,94),  "rpm_range":(2000,2800), "fault_prob":0.10},
    "NEW": {"fuel_range":(50,98),  "temp_range":(70,81),  "rpm_range":(1200,2000), "fault_prob":0.03},
}

def generate_iot_record(vehicle_id, info):
    params = TIER_PARAMS[info["tier"]]
    hour   = datetime.now().hour
    # Night = higher speed
    speed  = (
        round(random.uniform(70, 115), 2)
        if (hour >= 20 or hour <= 5)
        else round(random.uniform(30, 85), 2)
    )
    return {
        "vehicle_id":        vehicle_id,
        "vehicle_tier":      info["tier"],
        "driver_name":       info["driver"],
        "route":             info["route"],
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "hour_of_day":       hour,
        "is_night_shift":    1 if (hour>=20 or hour<=5) else 0,
        "gps_latitude":      round(random.uniform(15.0, 21.5), 6),
        "gps_longitude":     round(random.uniform(72.5, 80.5), 6),
        "speed_kmh":         speed,
        "fuel_level_pct":    round(random.uniform(*params["fuel_range"]), 2),
        "fuel_consumed_L":   round(random.uniform(0.5, 6.0), 3),
        "engine_temp_C":     round(random.uniform(*params["temp_range"]), 1),
        "engine_rpm":        random.randint(*params["rpm_range"]),
        "odometer_km":       random.randint(20000, 300000),
        "battery_voltage":   round(random.uniform(11.5, 14.8), 2),
        "brake_status":      random.choice(["OK","OK","OK","WARN"]),
        "tyre_pressure_psi": round(random.uniform(28, 38), 1),
        "cargo_weight_kg":   random.randint(500, 10000),
        "ignition_status":   random.choice(["ON","ON","ON","OFF"]),
        "alert_flag":        random.random() < params["fault_prob"],
    }

def upload_to_s3(data, vehicle_id):
    now      = datetime.now(timezone.utc)
    s3_key   = (
        f"{S3_FOLDER}/{now.year}/{now.month:02d}/"
        f"{now.day:02d}/{vehicle_id}_"
        f"{now.strftime('%H%M%S%f')}.json"
    )
    s3_client.put_object(
        Bucket      = S3_BUCKET,
        Key         = s3_key,
        Body        = json.dumps(data, indent=2),
        ContentType = "application/json",
    )
    return s3_key

def run_simulator(rounds=5, delay_seconds=2):
    print("=" * 55)
    print("  GlobeTrack - IoT Simulator STARTED")
    print("=" * 55)
    total = 0
    for round_num in range(1, rounds+1):
        print(f"\n--- Round {round_num}/{rounds} ---")
        for vid, info in VEHICLES.items():
            record = generate_iot_record(vid, info)
            path   = upload_to_s3(record, vid)
            total += 1
            print(
                f"  {vid} [{info['tier']}] | "
                f"Speed: {record['speed_kmh']} km/h | "
                f"Fuel: {record['fuel_level_pct']}% | "
                f"Temp: {record['engine_temp_C']}°C"
            )
        print(f"  Waiting {delay_seconds}s...")
        time.sleep(delay_seconds)
    print(f"\n{'='*55}")
    print(f"  DONE! {total} records uploaded")
    print("=" * 55)

if __name__ == "__main__":
    run_simulator(rounds=5, delay_seconds=2)