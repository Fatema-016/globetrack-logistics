# GlobeTrack Logistics - Booking Log Simulator (Small Scale)
# Simulates customer orders with realistic patterns
# Step 1 - Data Collection & Ingestion

import json
import random
import time
import boto3
from datetime import datetime, timezone, timedelta

S3_BUCKET = "globetrack-raw-data-lake"
S3_FOLDER = "booking-logs"
REGION    = "ap-south-1"
s3_client = boto3.client("s3", region_name=REGION)

CITIES = ["Mumbai","Pune","Nashik","Nagpur",
          "Aurangabad","Kolhapur","Goa","Solapur"]

CITY_DEMAND = {
    "Mumbai":0.25,"Pune":0.20,"Nashik":0.12,
    "Nagpur":0.12,"Aurangabad":0.10,"Kolhapur":0.08,
    "Goa":0.07,"Solapur":0.06
}

CARGO_TYPES = [
    "Electronics","Perishables","Automobile Parts",
    "Pharmaceuticals","Textiles","Raw Materials",
    "FMCG Goods","Chemicals","Machinery",
]

CUSTOMERS = [
    "Reliance Industries","Tata Motors","Mahindra Logistics",
    "ITC Limited","Hindustan Unilever","Asian Paints",
    "Sun Pharma","Bajaj Auto","Kirloskar Industries",
    "Godrej Consumer",
]

ROUTES = {
    "Mumbai-Pune":148,"Mumbai-Nashik":167,"Mumbai-Nagpur":834,
    "Mumbai-Goa":594,"Pune-Nagpur":714,"Pune-Kolhapur":228,
    "Nashik-Nagpur":668,"Kolhapur-Mumbai":373,"Goa-Pune":453,
}

WEATHER_CONDITIONS = [
    "Clear","Partly Cloudy","Overcast",
    "Light Rain","Heavy Rain","Fog","Thunderstorm",
]
WEATHER_RISK_MAP = {
    "Clear":5,"Partly Cloudy":15,"Overcast":25,
    "Light Rain":40,"Heavy Rain":70,"Fog":65,"Thunderstorm":85,
}

def generate_booking():
    cities  = list(CITY_DEMAND.keys())
    weights = list(CITY_DEMAND.values())
    origin  = random.choices(cities, weights=weights)[0]
    dest    = random.choice([c for c in cities if c != origin])

    route_key = f"{origin}-{dest}"
    alt_key   = f"{dest}-{origin}"
    distance  = ROUTES.get(route_key, ROUTES.get(alt_key, random.randint(100,800)))

    cargo_type    = random.choices(
        CARGO_TYPES,
        weights=[10,18,12,8,14,10,18,6,4]
    )[0]
    cargo_weight  = random.randint(100, 12000)
    priority      = random.choices(
        ["NORMAL","EXPRESS"], weights=[83,17]
    )[0]
    weather       = random.choice(WEATHER_CONDITIONS)
    delay_risk    = WEATHER_RISK_MAP.get(weather, 10)
    booked_at     = datetime.now(timezone.utc) - timedelta(
                        hours=random.randint(0, 72)
                    )
    est_delivery  = booked_at + timedelta(days=random.randint(1,4))

    # Delay logic
    rand   = random.random()
    status = "DELIVERED"
    if weather in ["Thunderstorm","Fog"] and rand < 0.90:
        status = "DELAYED"
    elif weather == "Heavy Rain" and rand < 0.75:
        status = "DELAYED"
    elif distance > 500 and delay_risk >= 40 and rand < 0.85:
        status = "DELAYED"
    elif priority == "EXPRESS" and cargo_weight > 9000 and rand < 0.80:
        status = "DELAYED"
    elif distance < 200 and weather in ["Clear","Partly Cloudy"] and rand < 0.92:
        status = "DELIVERED"
    else:
        status = random.choices(
            ["DELIVERED","IN_TRANSIT","BOOKED","CANCELLED"],
            weights=[45,25,20,10]
        )[0]

    freight = int(distance * random.uniform(18,32) +
                  (5000 if priority == "EXPRESS" else 0))

    return {
        "booking_id":         f"BK{random.randint(1000000,9999999)}",
        "customer_name":      random.choice(CUSTOMERS),
        "origin_city":        origin,
        "destination_city":   dest,
        "cargo_type":         cargo_type,
        "cargo_weight_kg":    cargo_weight,
        "cargo_value_inr":    random.randint(5000, 500000),
        "assigned_vehicle_id":f"GT-{str(random.randint(1,50)).zfill(3)}",
        "booking_timestamp":  booked_at.isoformat(),
        "estimated_delivery": est_delivery.isoformat(),
        "delivery_status":    status,
        "distance_km":        distance,
        "freight_charge_inr": freight,
        "priority":           priority,
        "is_insured":         random.choice([True,False]),
        "origin_weather":     weather,
        "origin_delay_risk":  delay_risk,
        "origin_has_severe":  1 if weather in
                              ["Thunderstorm","Fog","Heavy Rain"] else 0,
    }

def upload_to_s3(data):
    now    = datetime.now(timezone.utc)
    s3_key = (
        f"{S3_FOLDER}/{now.year}/{now.month:02d}/"
        f"{now.day:02d}/{data['booking_id']}_"
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
    print("  GlobeTrack - Booking Simulator STARTED")
    print("=" * 55)
    total = 0
    for round_num in range(1, rounds+1):
        print(f"\n--- Round {round_num}/{rounds} ---")
        for _ in range(10):
            record = generate_booking()
            path   = upload_to_s3(record)
            total += 1
            print(
                f"  {record['booking_id']} | "
                f"{record['origin_city']} to {record['destination_city']} | "
                f"{record['delivery_status']} | "
                f"{record['origin_weather']}"
            )
        print(f"  Waiting {delay_seconds}s...")
        time.sleep(delay_seconds)
    print(f"\n{'='*55}")
    print(f"  DONE! {total} booking records uploaded")
    print("=" * 55)

if __name__ == "__main__":
    run_simulator(rounds=5, delay_seconds=2)