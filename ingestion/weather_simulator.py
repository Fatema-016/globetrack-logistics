# GlobeTrack Logistics - Weather & Traffic Feed Simulator
# Simulates external weather + traffic + currency APIs
# Step 1 - Data Collection & Ingestion

import json
import random
import time
import boto3
from datetime import datetime, timezone

S3_BUCKET = "globetrack-raw-data-lake"
S3_FOLDER = "weather-data"
REGION    = "ap-south-1"
s3_client = boto3.client("s3", region_name=REGION)

CITIES = [
    {"name":"Mumbai",     "lat":19.0760,"lon":72.8777,
     "rain_prob":0.45,"fog_prob":0.10,"base_temp":29,"congestion":80},
    {"name":"Pune",       "lat":18.5204,"lon":73.8567,
     "rain_prob":0.35,"fog_prob":0.08,"base_temp":27,"congestion":65},
    {"name":"Nashik",     "lat":19.9975,"lon":73.7898,
     "rain_prob":0.30,"fog_prob":0.12,"base_temp":25,"congestion":45},
    {"name":"Nagpur",     "lat":21.1458,"lon":79.0882,
     "rain_prob":0.20,"fog_prob":0.05,"base_temp":33,"congestion":50},
    {"name":"Aurangabad", "lat":19.8762,"lon":75.3433,
     "rain_prob":0.25,"fog_prob":0.08,"base_temp":28,"congestion":40},
    {"name":"Kolhapur",   "lat":16.7050,"lon":74.2433,
     "rain_prob":0.40,"fog_prob":0.07,"base_temp":26,"congestion":35},
    {"name":"Goa",        "lat":15.2993,"lon":74.1240,
     "rain_prob":0.50,"fog_prob":0.06,"base_temp":30,"congestion":55},
    {"name":"Solapur",    "lat":17.6599,"lon":75.9064,
     "rain_prob":0.15,"fog_prob":0.04,"base_temp":32,"congestion":38},
]

WEATHER_CONDITIONS = [
    "Clear","Partly Cloudy","Overcast",
    "Light Rain","Heavy Rain","Fog","Thunderstorm",
]
WEATHER_RISK_MAP = {
    "Clear":5,"Partly Cloudy":15,"Overcast":25,
    "Light Rain":40,"Heavy Rain":70,"Fog":65,"Thunderstorm":85,
}

def get_weather_probs(city):
    rp = city["rain_prob"]
    fp = city["fog_prob"]
    p  = [
        max(0.05, 0.40 - rp),
        max(0.05, 0.25 - rp * 0.3),
        0.10,
        min(0.30, rp * 0.6),
        min(0.20, rp * 0.3),
        fp,
        min(0.15, rp * 0.2),
    ]
    total = sum(p)
    return [x/total for x in p]

def generate_weather_record(city):
    probs     = get_weather_probs(city)
    condition = random.choices(WEATHER_CONDITIONS, weights=probs)[0]

    temp = round(random.normalvariate(city["base_temp"], 4), 1)
    temp = max(15, min(48, temp))

    if city["name"] in ["Mumbai","Goa","Kolhapur"]:
        humidity = random.randint(65, 95)
    elif city["name"] in ["Nagpur","Solapur"]:
        humidity = random.randint(25, 55)
    else:
        humidity = random.randint(40, 75)

    if condition in ["Thunderstorm","Heavy Rain"]:
        wind     = round(random.uniform(25, 70), 1)
        rainfall = round(random.uniform(15, 100), 2)
    elif condition == "Light Rain":
        wind     = round(random.uniform(10, 30), 1)
        rainfall = round(random.uniform(2, 15), 2)
    elif condition == "Fog":
        wind     = round(random.uniform(5, 15), 1)
        rainfall = 0.0
    else:
        wind     = round(random.uniform(5, 20), 1)
        rainfall = 0.0

    vis_map = {
        "Clear":random.uniform(15,30),
        "Partly Cloudy":random.uniform(10,20),
        "Overcast":random.uniform(8,15),
        "Light Rain":random.uniform(4,10),
        "Heavy Rain":random.uniform(1,5),
        "Fog":random.uniform(0.1,2),
        "Thunderstorm":random.uniform(1,4),
    }
    visibility = round(vis_map.get(condition, 10), 1)
    delay_risk = WEATHER_RISK_MAP.get(condition, 10)

    if city["name"] in ["Mumbai","Goa"] and condition == "Fog":
        delay_risk = min(100, delay_risk + 15)

    congestion = int(random.normalvariate(city["congestion"], 12))
    congestion = max(0, min(100, congestion))

    if condition in ["Thunderstorm","Heavy Rain","Fog"]:
        congestion = min(100, congestion + 20)

    usd_inr = round(random.normalvariate(83.5, 1.2), 2)
    usd_inr = max(80.0, min(87.0, usd_inr))

    return {
        "city":               city["name"],
        "latitude":           city["lat"],
        "longitude":          city["lon"],
        "timestamp":          datetime.now(timezone.utc).isoformat(),
        "weather_condition":  condition,
        "temperature_C":      temp,
        "humidity_pct":       humidity,
        "wind_speed_kmh":     wind,
        "wind_direction":     random.choice(
                                  ["N","NE","E","SE","S","SW","W","NW"]
                              ),
        "rainfall_mm":        rainfall,
        "visibility_km":      visibility,
        "road_condition":     (
                                  "Poor" if rainfall > 30
                                  else "Moderate" if rainfall > 10
                                  else "Good"
                              ),
        "fog_alert":          condition == "Fog",
        "flood_alert":        rainfall > 50,
        "delay_risk_score":   delay_risk,
        "traffic_congestion": congestion,
        "usd_inr_rate":       usd_inr,
        "data_source":        "GlobeTrack-WeatherAPI-v2",
    }

def upload_to_s3(data):
    now    = datetime.now(timezone.utc)
    s3_key = (
        f"{S3_FOLDER}/{now.year}/{now.month:02d}/"
        f"{now.day:02d}/{data['city']}_"
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
    print("  GlobeTrack - Weather/Traffic Simulator STARTED")
    print("=" * 55)
    total = 0
    for round_num in range(1, rounds+1):
        print(f"\n--- Round {round_num}/{rounds} ---")
        for city in CITIES:
            record = generate_weather_record(city)
            upload_to_s3(record)
            total += 1
            print(
                f"  {record['city']:12} | "
                f"{record['weather_condition']:15} | "
                f"Temp: {record['temperature_C']}C | "
                f"Risk: {record['delay_risk_score']}% | "
                f"Congestion: {record['traffic_congestion']}%"
            )
        print(f"  Waiting {delay_seconds}s...")
        time.sleep(delay_seconds)
    print(f"\n{'='*55}")
    print(f"  DONE! {total} weather records uploaded")
    print("=" * 55)

if __name__ == "__main__":
    run_simulator(rounds=5, delay_seconds=2)