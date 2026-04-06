# GlobeTrack Logistics - Large Dataset Generator


import boto3
import pandas as pd
import numpy as np
import random
import time
from datetime import datetime, timezone, timedelta
import warnings
warnings.filterwarnings("ignore")

# AWS Configuration
S3_BUCKET = "globetrack-raw-data-lake"
REGION    = "ap-south-1"
s3_client = boto3.client("s3", region_name=REGION)

# ─────────────────────────────────────────
# Reference Data
# ─────────────────────────────────────────

# 50 vehicles split into 3 tiers by age
# OLD trucks (GT-001 to GT-017)  : poor efficiency, high engine temp
# MID trucks (GT-018 to GT-035)  : average performance
# NEW trucks (GT-036 to GT-050)  : best efficiency, low temp
VEHICLE_PROFILES = {}
for i in range(1, 51):
    vid = f"GT-{str(i).zfill(3)}"
    if i <= 17:   # Old trucks
        VEHICLE_PROFILES[vid] = {
            "tier":          "OLD",
            "base_fuel_eff": np.random.uniform(4.0, 6.5),
            "base_eng_temp": np.random.uniform(95, 108),
            "base_rpm":      np.random.randint(2800, 3800),
            "fault_prob":    0.25,
        }
    elif i <= 35:  # Mid trucks
        VEHICLE_PROFILES[vid] = {
            "tier":          "MID",
            "base_fuel_eff": np.random.uniform(7.0, 10.0),
            "base_eng_temp": np.random.uniform(82, 94),
            "base_rpm":      np.random.randint(2000, 2800),
            "fault_prob":    0.10,
        }
    else:          # New trucks
        VEHICLE_PROFILES[vid] = {
            "tier":          "NEW",
            "base_fuel_eff": np.random.uniform(11.0, 15.0),
            "base_eng_temp": np.random.uniform(70, 81),
            "base_rpm":      np.random.randint(1200, 2000),
            "fault_prob":    0.03,
        }

VEHICLES = list(VEHICLE_PROFILES.keys())


DRIVERS = [
    "Rajesh Kumar",   "Suresh Yadav",   "Amit Singh",
    "Vikram Sharma",  "Ravi Patel",     "Manoj Gupta",
    "Arjun Verma",    "Deepak Tiwari",  "Sanjay Mishra",
    "Rohit Chauhan",  "Anil Dubey",     "Pradeep Nair",
    "Ganesh Rao",     "Santosh Joshi",  "Ramesh Pandey",
    "Dinesh Shukla",  "Mahesh Iyer",    "Naresh Bhatia",
    "Umesh Kapoor",   "Lokesh Verma",   "Harish Tomar",
    "Girish Patil",   "Bharat Sharma",  "Prakash Nair",
    "Vinod Yadav",    "Mukesh Singh",   "Rakesh Gupta",
    "Satish Kumar",   "Navin Joshi",    "Prem Chauhan",
]


ROUTES = {
    "Mumbai-Pune":        148,
    "Mumbai-Nashik":      167,
    "Mumbai-Aurangabad":  335,
    "Mumbai-Nagpur":      834,
    "Mumbai-Goa":         594,
    "Mumbai-Solapur":     455,
    "Pune-Nashik":        211,
    "Pune-Aurangabad":    233,
    "Pune-Nagpur":        714,
    "Pune-Kolhapur":      228,
    "Pune-Solapur":       248,
    "Nashik-Nagpur":      668,
    "Nashik-Aurangabad":  183,
    "Nagpur-Aurangabad":  503,
    "Kolhapur-Mumbai":    373,
    "Goa-Pune":           453,
    "Solapur-Nagpur":     494,
    "Aurangabad-Kolhapur":393,
}
ROUTE_NAMES    = list(ROUTES.keys())
ROUTE_DISTANCES= list(ROUTES.values())

# Cities with demand weights
# Mumbai/Pune = high commercial demand
# Goa/Kolhapur = lower demand
CITIES = ["Mumbai","Pune","Nashik","Nagpur",
          "Aurangabad","Kolhapur","Goa","Solapur"]
CITY_DEMAND_WEIGHTS = [0.25, 0.20, 0.12, 0.12,
                       0.10, 0.08, 0.07, 0.06]

# City climate profiles for realistic weather
CITY_CLIMATE = {
    "Mumbai":     {"rain_prob":0.45, "fog_prob":0.10, "base_temp":29},
    "Pune":       {"rain_prob":0.35, "fog_prob":0.08, "base_temp":27},
    "Nashik":     {"rain_prob":0.30, "fog_prob":0.12, "base_temp":25},
    "Nagpur":     {"rain_prob":0.20, "fog_prob":0.05, "base_temp":33},
    "Aurangabad": {"rain_prob":0.25, "fog_prob":0.08, "base_temp":28},
    "Kolhapur":   {"rain_prob":0.40, "fog_prob":0.07, "base_temp":26},
    "Goa":        {"rain_prob":0.50, "fog_prob":0.06, "base_temp":30},
    "Solapur":    {"rain_prob":0.15, "fog_prob":0.04, "base_temp":32},
}

CARGO_TYPES = [
    "Electronics","Perishables","Automobile Parts",
    "Pharmaceuticals","Textiles","Raw Materials",
    "FMCG Goods","Chemicals","Machinery",
]
# Cargo demand weights — FMCG/Perishables more common
CARGO_WEIGHTS = [0.10,0.18,0.12,0.08,0.14,0.10,0.18,0.06,0.04]

CUSTOMERS = [
    "Reliance Industries","Tata Motors","Mahindra Logistics",
    "ITC Limited","Hindustan Unilever","Asian Paints",
    "Sun Pharma","Bajaj Auto","Kirloskar Industries",
    "Godrej Consumer","Wipro Enterprises","HCL Logistics",
    "L&T Construction","Ultratech Cement","Marico Limited",
]

WEATHER_CONDITIONS = [
    "Clear","Partly Cloudy","Overcast",
    "Light Rain","Heavy Rain","Fog","Thunderstorm",
]

WEATHER_RISK_MAP = {
    "Clear":        5,
    "Partly Cloudy":15,
    "Overcast":     25,
    "Light Rain":   40,
    "Heavy Rain":   70,
    "Fog":          65,
    "Thunderstorm": 85,
}


# DATASET 1 — IoT Sensor Data 

def generate_iot_chunk(chunk_size):
    n           = chunk_size
    vehicle_ids = np.random.choice(VEHICLES, n)
    route_idx   = np.random.choice(len(ROUTE_NAMES), n)
    route_names = np.array(ROUTE_NAMES)[route_idx]
    distances   = np.array(ROUTE_DISTANCES)[route_idx]

    # Assign drivers based on vehicle
    driver_names = np.random.choice(DRIVERS, n)

    # Generate timestamps — spread over last 30 days
    timestamps = [
        (datetime.now(timezone.utc) -
         timedelta(seconds=random.randint(0, 86400*30))
        ).replace(microsecond=0)
        for _ in range(n)
    ]
    hours = np.array([t.hour for t in timestamps])

    # Night hours (20:00-05:00) = higher speed
    is_night = (hours >= 20) | (hours <= 5)

    # Build arrays using vehicle profiles
    speed_kmh       = np.zeros(n)
    fuel_level_pct  = np.zeros(n)
    fuel_consumed_L = np.zeros(n)
    engine_temp_C   = np.zeros(n)
    engine_rpm      = np.zeros(n)
    battery_voltage = np.zeros(n)
    alert_flag      = np.zeros(n, dtype=bool)

    for idx, vid in enumerate(vehicle_ids):
        profile = VEHICLE_PROFILES[vid]

        # Speed: night = faster, day = slower
        if is_night[idx]:
            base_speed = np.random.uniform(70, 120)
        else:
            base_speed = np.random.uniform(30, 85)
        speed_kmh[idx] = round(base_speed, 2)

        # Fuel level: old trucks consume more
        if profile["tier"] == "OLD":
            fuel_level_pct[idx]  = round(np.random.uniform(15, 65), 2)
            fuel_consumed_L[idx] = round(np.random.uniform(3.0, 6.5), 3)
        elif profile["tier"] == "MID":
            fuel_level_pct[idx]  = round(np.random.uniform(30, 80), 2)
            fuel_consumed_L[idx] = round(np.random.uniform(1.5, 3.5), 3)
        else:  # NEW
            fuel_level_pct[idx]  = round(np.random.uniform(50, 98), 2)
            fuel_consumed_L[idx] = round(np.random.uniform(0.5, 2.0), 3)

        # Engine temp: old trucks run hotter
        engine_temp_C[idx] = round(
            np.random.normal(profile["base_eng_temp"], 4), 1
        )

        # RPM: old trucks rev higher
        engine_rpm[idx] = int(
            np.random.normal(profile["base_rpm"], 200)
        )

        # Battery voltage
        battery_voltage[idx] = round(np.random.uniform(11.5, 14.8), 2)

        # Alert: old trucks more likely to fault
        alert_flag[idx] = np.random.random() < profile["fault_prob"]

    # GPS coordinates within Maharashtra/Goa region
    gps_lat = np.round(np.random.uniform(15.0, 21.5, n), 6)
    gps_lon = np.round(np.random.uniform(72.5, 80.5, n), 6)

    # Odometer: old trucks have higher mileage
    odometer_km = np.array([
        np.random.randint(
            150000 if VEHICLE_PROFILES[v]["tier"]=="OLD" else
            80000  if VEHICLE_PROFILES[v]["tier"]=="MID" else 20000,
            300000 if VEHICLE_PROFILES[v]["tier"]=="OLD" else
            150000 if VEHICLE_PROFILES[v]["tier"]=="MID" else 80000
        )
        for v in vehicle_ids
    ])

    vehicle_tiers = np.array([
        VEHICLE_PROFILES[v]["tier"] for v in vehicle_ids
    ])

    brake_status    = np.random.choice(
        ["OK","OK","OK","OK","WARN"], n,
        p=[0.45,0.25,0.15,0.10,0.05]
    )
    tyre_pressure   = np.round(np.random.uniform(28, 38, n), 1)
    cargo_weight_kg = np.random.randint(500, 10000, n)
    ignition_status = np.random.choice(
        ["ON","ON","ON","OFF"], n, p=[0.5,0.3,0.15,0.05]
    )

    return pd.DataFrame({
        "vehicle_id":        vehicle_ids,
        "vehicle_tier":      vehicle_tiers,
        "driver_name":       driver_names,
        "route":             route_names,
        "route_distance_km": distances,
        "timestamp":         [t.isoformat() for t in timestamps],
        "hour_of_day":       hours,
        "is_night_shift":    is_night.astype(int),
        "gps_latitude":      gps_lat,
        "gps_longitude":     gps_lon,
        "speed_kmh":         speed_kmh,
        "fuel_level_pct":    fuel_level_pct,
        "fuel_consumed_L":   fuel_consumed_L,
        "engine_temp_C":     np.clip(engine_temp_C, 60, 130),
        "engine_rpm":        np.clip(engine_rpm, 500, 5000).astype(int),
        "odometer_km":       odometer_km,
        "battery_voltage":   battery_voltage,
        "brake_status":      brake_status,
        "tyre_pressure_psi": tyre_pressure,
        "cargo_weight_kg":   cargo_weight_kg,
        "ignition_status":   ignition_status,
        "alert_flag":        alert_flag,
    })


# DATASET 2 — Operational Booking Logs

def generate_booking_chunk(chunk_size):
    n = chunk_size

    # Origin cities — Mumbai/Pune dominate
    origins = np.random.choice(
        CITIES, n, p=CITY_DEMAND_WEIGHTS
    )
    # Destination — different from origin
    destinations = np.array([
        np.random.choice(
            [c for c in CITIES if c != o]
        )
        for o in origins
    ])

    # Route distance based on origin-destination
    def get_distance(orig, dest):
        key1 = f"{orig}-{dest}"
        key2 = f"{dest}-{orig}"
        if key1 in ROUTES:
            return ROUTES[key1]
        elif key2 in ROUTES:
            return ROUTES[key2]
        else:
            return random.randint(100, 800)

    distances     = np.array([
        get_distance(o, d)
        for o, d in zip(origins, destinations)
    ])
    cargo_types   = np.random.choice(
        CARGO_TYPES, n, p=CARGO_WEIGHTS
    )
    cargo_weights = np.random.randint(100, 12000, n)
    priorities    = np.random.choice(
        ["NORMAL","NORMAL","EXPRESS"], n,
        p=[0.50, 0.33, 0.17]
    )

    # Weather at origin
    weathers = np.array([
        np.random.choice(
            WEATHER_CONDITIONS,
            p=_get_weather_probs(o)
        )
        for o in origins
    ])
    delay_risks = np.array([
        WEATHER_RISK_MAP.get(w, 10) for w in weathers
    ])

    # Booking timestamps — spread over 90 days
    # Monday and Friday have higher booking volumes
    booking_times = []
    for _ in range(n):
        days_ago = random.randint(0, 90)
        hour     = random.choices(
            range(24),
            weights=[2,1,1,1,2,4,8,10,10,9,8,7,
                     8,9,9,8,7,6,5,4,3,3,2,2]
        )[0]
        bt = (datetime.now(timezone.utc) -
              timedelta(days=days_ago,
                        hours=random.randint(0,23))
             ).replace(hour=hour, microsecond=0)
        booking_times.append(bt)

    booking_times    = np.array(booking_times)
    estimated_delivery = np.array([
        bt + timedelta(days=random.randint(1, 4))
        for bt in booking_times
    ])

    # ── STRONG LOGICAL DELAY RULES ──
    rand     = np.random.random(n)
    statuses = np.full(n, "DELIVERED", dtype=object)

    # Rule 1: Thunderstorm/Fog 90% delayed
    rule1 = np.isin(weathers, ["Thunderstorm", "Fog"])
    statuses[rule1 & (rand < 0.90)] = "DELAYED"

    # Rule 2: Heavy Rain  75% delayed
    rule2 = weathers == "Heavy Rain"
    statuses[rule2 & (rand < 0.75)] = "DELAYED"

    # Rule 3: Long haul (>500km) + bad weather  85% delayed
    rule3 = (distances > 500) & (delay_risks >= 40)
    statuses[rule3 & (rand < 0.85)] = "DELAYED"

    # Rule 4: Express + very heavy cargo  80% delayed
    rule4 = (priorities == "EXPRESS") & (cargo_weights > 9000)
    statuses[rule4 & (rand < 0.80)] = "DELAYED"

    # Rule 5: Perishables + long haul  70% delayed
    rule5 = (cargo_types == "Perishables") & (distances > 400)
    statuses[rule5 & (rand < 0.70)] = "DELAYED"

    # Rule 6: Short haul (<200km) + clear weather  92% delivered
    rule6 = (distances < 200) & np.isin(
        weathers, ["Clear", "Partly Cloudy"]
    )
    statuses[rule6 & (rand < 0.92)] = "DELIVERED"

    # Rule 7: Pharmaceuticals = high priority  lower delay
    rule7 = cargo_types == "Pharmaceuticals"
    statuses[rule7 & (rand < 0.75)] = "DELIVERED"

    # Rule 8: Normal conditions  realistic mix
    is_rule_applied = rule1|rule2|rule3|rule4|rule5|rule6|rule7
    base_statuses   = np.random.choice(
        ["DELIVERED","IN_TRANSIT","BOOKED","CANCELLED"],
        n, p=[0.45, 0.25, 0.20, 0.10]
    )
    statuses[~is_rule_applied] = base_statuses[~is_rule_applied]

    # Freight charge — longer routes cost more
    freight_charge = np.array([
        int(d * random.uniform(18, 32) +
            (5000 if p == "EXPRESS" else 0))
        for d, p in zip(distances, priorities)
    ])

    # Cargo value — electronics/pharma = high value
    cargo_value_map = {
        "Electronics":      (50000,  500000),
        "Pharmaceuticals":  (80000,  800000),
        "Machinery":        (100000, 1000000),
        "Automobile Parts": (30000,  300000),
        "Chemicals":        (20000,  200000),
        "FMCG Goods":       (10000,  100000),
        "Perishables":      (5000,   80000),
        "Textiles":         (15000,  150000),
        "Raw Materials":    (8000,   80000),
    }
    cargo_values = np.array([
        random.randint(*cargo_value_map.get(ct, (10000, 100000)))
        for ct in cargo_types
    ])

    return pd.DataFrame({
        "booking_id":         [f"BK{random.randint(1000000,9999999)}"
                               for _ in range(n)],
        "customer_name":      np.random.choice(CUSTOMERS, n),
        "origin_city":        origins,
        "destination_city":   destinations,
        "cargo_type":         cargo_types,
        "cargo_weight_kg":    cargo_weights,
        "cargo_value_inr":    cargo_values,
        "assigned_vehicle_id":np.random.choice(VEHICLES, n),
        "booking_timestamp":  [t.isoformat() for t in booking_times],
        "estimated_delivery": [t.isoformat() for t in estimated_delivery],
        "delivery_status":    statuses,
        "distance_km":        distances,
        "freight_charge_inr": freight_charge,
        "priority":           priorities,
        "is_insured":         np.random.choice(
                                  [True, False], n, p=[0.6, 0.4]
                              ),
        "origin_weather":     weathers,
        "origin_delay_risk":  delay_risks,
        "origin_has_severe":  np.isin(
                                  weathers,
                                  ["Thunderstorm","Fog","Heavy Rain"]
                              ).astype(int),
    })

def _get_weather_probs(city):
    """Returns weather probabilities based on city climate."""
    climate = CITY_CLIMATE.get(city, {
        "rain_prob":0.25,"fog_prob":0.07,"base_temp":28
    })
    rp  = climate["rain_prob"]
    fp  = climate["fog_prob"]
    # [Clear, PartlyCloudy, Overcast, LightRain,
    #  HeavyRain, Fog, Thunderstorm]
    p   = [
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


# DATASET 3 — External Weather/Traffic Feeds

def generate_weather_chunk(chunk_size):
    n      = chunk_size
    cities = np.random.choice(CITIES, n, p=CITY_DEMAND_WEIGHTS)

    conditions      = []
    temperatures    = []
    humidity_pcts   = []
    wind_speeds     = []
    rainfall_mms    = []
    visibility_kms  = []
    delay_risks_out = []
    fog_alerts      = []
    flood_alerts    = []

    for city in cities:
        climate   = CITY_CLIMATE[city]
        probs     = _get_weather_probs(city)
        condition = np.random.choice(WEATHER_CONDITIONS, p=probs)

        # Temperature varies by city
        base_temp = climate["base_temp"]
        temp      = round(np.random.normal(base_temp, 4), 1)
        temp      = np.clip(temp, 15, 48)

        # Humidity: coastal cities (Mumbai/Goa) = higher
        if city in ["Mumbai", "Goa", "Kolhapur"]:
            humidity = random.randint(65, 95)
        elif city in ["Nagpur", "Solapur"]:
            humidity = random.randint(25, 55)
        else:
            humidity = random.randint(40, 75)

        # Wind speed: higher during storms
        if condition in ["Thunderstorm", "Heavy Rain"]:
            wind = round(random.uniform(25, 70), 1)
        elif condition in ["Light Rain", "Fog"]:
            wind = round(random.uniform(10, 30), 1)
        else:
            wind = round(random.uniform(5, 20), 1)

        # Rainfall
        if condition == "Thunderstorm":
            rainfall = round(random.uniform(30, 100), 2)
        elif condition == "Heavy Rain":
            rainfall = round(random.uniform(15, 60), 2)
        elif condition == "Light Rain":
            rainfall = round(random.uniform(2, 15), 2)
        else:
            rainfall = 0.0

        # Visibility
        vis_map = {
            "Clear": random.uniform(15, 30),
            "Partly Cloudy": random.uniform(10, 20),
            "Overcast": random.uniform(8, 15),
            "Light Rain": random.uniform(4, 10),
            "Heavy Rain": random.uniform(1, 5),
            "Fog": random.uniform(0.1, 2),
            "Thunderstorm": random.uniform(1, 4),
        }
        visibility = round(vis_map.get(condition, 10), 1)

        delay_risk = WEATHER_RISK_MAP.get(condition, 10)
        # City modifier — Mumbai fog is worse than Nagpur fog
        if city in ["Mumbai", "Goa"] and condition == "Fog":
            delay_risk = min(100, delay_risk + 15)

        conditions.append(condition)
        temperatures.append(temp)
        humidity_pcts.append(humidity)
        wind_speeds.append(wind)
        rainfall_mms.append(rainfall)
        visibility_kms.append(visibility)
        delay_risks_out.append(delay_risk)
        fog_alerts.append(condition == "Fog")
        flood_alerts.append(rainfall > 50)

    # Timestamps spread over last 30 days
    timestamps = [
        (datetime.now(timezone.utc) -
         timedelta(minutes=random.randint(0, 43200))
        ).replace(microsecond=0).isoformat()
        for _ in range(n)
    ]

    # Currency exchange rate (INR/USD) — fluctuates realistically
    usd_inr = np.round(
        np.random.normal(83.5, 1.2, n).clip(80, 87), 2
    )

    # Traffic congestion index (0-100)
    # Higher in Mumbai/Pune, lower in smaller cities
    congestion_map = {
        "Mumbai":80,"Pune":65,"Nashik":45,"Nagpur":50,
        "Aurangabad":40,"Kolhapur":35,"Goa":55,"Solapur":38
    }
    congestion = np.array([
        int(np.random.normal(congestion_map.get(c, 45), 12))
        for c in cities
    ]).clip(0, 100)

    city_lats = {
        "Mumbai":19.0760,"Pune":18.5204,"Nashik":19.9975,
        "Nagpur":21.1458,"Aurangabad":19.8762,
        "Kolhapur":16.7050,"Goa":15.2993,"Solapur":17.6599
    }
    city_lons = {
        "Mumbai":72.8777,"Pune":73.8567,"Nashik":73.7898,
        "Nagpur":79.0882,"Aurangabad":75.3433,
        "Kolhapur":74.2433,"Goa":74.1240,"Solapur":75.9064
    }

    return pd.DataFrame({
        "city":                cities,
        "latitude":            [city_lats[c] for c in cities],
        "longitude":           [city_lons[c] for c in cities],
        "timestamp":           timestamps,
        "weather_condition":   conditions,
        "temperature_C":       temperatures,
        "humidity_pct":        humidity_pcts,
        "wind_speed_kmh":      wind_speeds,
        "wind_direction":      np.random.choice(
                                   ["N","NE","E","SE","S","SW","W","NW"],n
                               ),
        "rainfall_mm":         rainfall_mms,
        "visibility_km":       visibility_kms,
        "road_condition":      np.where(
                                   np.array(rainfall_mms) > 30, "Poor",
                                   np.where(
                                       np.array(rainfall_mms) > 10,
                                       "Moderate", "Good"
                                   )
                               ),
        "fog_alert":           fog_alerts,
        "flood_alert":         flood_alerts,
        "delay_risk_score":    delay_risks_out,
        "traffic_congestion":  congestion,
        "usd_inr_rate":        usd_inr,
        "data_source":         "GlobeTrack-WeatherAPI-v2",
    })

# ─────────────────────────────────────────
# Upload to S3
# ─────────────────────────────────────────
def upload_chunk_to_s3(df, folder, chunk_num):
    csv_data = df.to_csv(index=False)
    s3_key   = (
        f"{folder}/large-dataset/"
        f"chunk_{chunk_num:04d}.csv"
    )
    s3_client.put_object(
        Bucket      = S3_BUCKET,
        Key         = s3_key,
        Body        = csv_data.encode("utf-8"),
        ContentType = "text/csv",
    )
    return s3_key

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def generate_all_datasets():
    print("=" * 60)
    print("  GlobeTrack v2 - Improved Dataset Generator")
    print("  Heterogeneous data with realistic patterns")
    print("  Target: ~50 GB per dataset")
    print("=" * 60)

    CHUNK_SIZE = 10000
    NUM_CHUNKS = 60
    TOTAL_ROWS = CHUNK_SIZE * NUM_CHUNKS

    datasets = [
        ("iot-sensor-data",  generate_iot_chunk,
         "IoT Sensor (vehicle tiers + night shift)"),
        ("booking-logs",     generate_booking_chunk,
         "Booking Logs (city demand + delay rules)"),
        ("weather-data",     generate_weather_chunk,
         "Weather/Traffic Feeds (city climate patterns)"),
    ]

    for folder, generator, name in datasets:
        print(f"\n{'─'*60}")
        print(f"  {name}")
        print(f"  {NUM_CHUNKS} chunks × {CHUNK_SIZE:,} rows = "
              f"{TOTAL_ROWS:,} total rows")
        print(f"{'─'*60}")

        start        = time.time()
        total_upload = 0

        for chunk_num in range(1, NUM_CHUNKS + 1):
            df     = generator(CHUNK_SIZE)
            upload_chunk_to_s3(df, folder, chunk_num)
            total_upload += len(df)

            if chunk_num % 10 == 0:
                elapsed = time.time() - start
                pct     = chunk_num / NUM_CHUNKS * 100
                print(
                    f"  [{pct:5.1f}%] Chunk {chunk_num:3}/{NUM_CHUNKS}"
                    f" | Rows: {total_upload:>8,}"
                    f" | Time: {elapsed:.1f}s"
                )

        elapsed = time.time() - start
        print(f"\n   {name.split('(')[0].strip()} COMPLETE!")
        print(f"    Rows: {total_upload:,} | Time: {elapsed:.1f}s")

    print("\n" + "=" * 60)
    print("  ALL 3 DATASETS GENERATED!")
    print(f"  Total rows: {TOTAL_ROWS * 3:,}")
    print("=" * 60)

if __name__ == "__main__":
    generate_all_datasets()