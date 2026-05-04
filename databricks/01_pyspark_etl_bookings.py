# GlobeTrack Logistics - PySpark ETL Pipeline (Databricks)
# Booking Logs Large Scale Processing using Apache Spark
# Compute: Databricks Community Edition
# Storage: AWS S3 ap-south-1



from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, lit, round as spark_round,
    count, sum as spark_sum, avg,
    to_timestamp, hour, dayofweek,
    udf, regexp_replace
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType,
    IntegerType, BooleanType
)
from datetime import datetime
import json


# Initialize Spark Session

spark = SparkSession.builder \
    .appName("GlobeTrack-Booking-ETL") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=" * 60)
print("  GlobeTrack - PySpark Booking ETL Pipeline")
print("  Running on Databricks Community Edition")
print(f"  Spark Version: {spark.version}")
print("=" * 60)

# ─────────────────────────────────────────
# Step 1 - Load Data
# In Databricks: load from S3
# Locally: use sample data
# ─────────────────────────────────────────
print("\n[1/6] Loading booking data...")

# Define schema 
schema = StructType([
    StructField("booking_id",           StringType(),  True),
    StructField("customer_name",        StringType(),  True),
    StructField("origin_city",          StringType(),  True),
    StructField("destination_city",     StringType(),  True),
    StructField("cargo_type",           StringType(),  True),
    StructField("cargo_weight_kg",      DoubleType(),  True),
    StructField("cargo_value_inr",      DoubleType(),  True),
    StructField("assigned_vehicle_id",  StringType(),  True),
    StructField("booking_timestamp",    StringType(),  True),
    StructField("estimated_delivery",   StringType(),  True),
    StructField("delivery_status",      StringType(),  True),
    StructField("distance_km",          DoubleType(),  True),
    StructField("freight_charge_inr",   DoubleType(),  True),
    StructField("priority",             StringType(),  True),
    StructField("is_insured",           StringType(),  True),
    StructField("origin_weather",       StringType(),  True),
    StructField("origin_delay_risk",    DoubleType(),  True),
    StructField("origin_has_severe",    IntegerType(), True),
])

try:
    
    S3_PATH = "s3://globetrack-raw-data-lake/booking-logs/large-dataset/"
    df_raw = spark.read \
        .option("header", "true") \
        .schema(schema) \
        .csv(S3_PATH)
    print(f"  Loaded from S3: {S3_PATH}")
except Exception:
    
    print("  S3 not accessible - generating sample Spark DataFrame...")
    import pandas as pd
    from pyspark.sql import Row

    print("  Loading from local CSV dashboard data...")
    pandas_df = pd.read_csv("dashboard/delivery_analytics.csv")

    for col_name in ["cargo_weight_kg","cargo_value_inr",
                     "distance_km","freight_charge_inr",
                     "origin_delay_risk"]:
        if col_name in pandas_df.columns:
            pandas_df[col_name] = pd.to_numeric(
                pandas_df[col_name], errors="coerce"
            ).fillna(0.0)

    if "origin_has_severe" not in pandas_df.columns:
        pandas_df["origin_has_severe"] = 0
    if "origin_delay_risk" not in pandas_df.columns:
        pandas_df["origin_delay_risk"] = 0.0
    if "origin_weather" not in pandas_df.columns:
        pandas_df["origin_weather"] = "Clear"
    if "customer_name" not in pandas_df.columns:
        pandas_df["customer_name"] = "GlobeTrack Customer"
    if "assigned_vehicle_id" not in pandas_df.columns:
        pandas_df["assigned_vehicle_id"] = "GT-001"
    if "booking_timestamp" not in pandas_df.columns:
        pandas_df["booking_timestamp"] = "2026-04-07T06:00:00+00:00"
    if "estimated_delivery" not in pandas_df.columns:
        pandas_df["estimated_delivery"] = "2026-04-10T06:00:00+00:00"
    if "is_insured" not in pandas_df.columns:
        pandas_df["is_insured"] = "True"

    df_raw = spark.createDataFrame(pandas_df)
    print(f"  Loaded {df_raw.count():,} records from local CSV")

total_records = df_raw.count()
print(f"  Total records loaded: {total_records:,}")
print(f"  Columns: {len(df_raw.columns)}")

# ─────────────────────────────────────────
# Step 2 - Data Cleaning
# ─────────────────────────────────────────
print("\n[2/6] Cleaning data with Spark transformations...")

df_clean = df_raw \
    .dropDuplicates(["booking_id"]) \
    .filter(col("distance_km") > 0) \
    .filter(col("freight_charge_inr") > 0) \
    .filter(col("cargo_weight_kg").isNotNull()) \
    .na.fill({
        "cargo_weight_kg":    0.0,
        "cargo_value_inr":    0.0,
        "distance_km":        0.0,
        "freight_charge_inr": 0.0,
        "origin_delay_risk":  0.0,
        "origin_has_severe":  0,
    }) \
    .withColumn(
        "delivery_status",
        regexp_replace(col("delivery_status"), " ", "")
    )

records_after = df_clean.count()
duplicates    = total_records - records_after
print(f"  Removed {duplicates:,} duplicates")
print(f"  Records after cleaning: {records_after:,}")

# ─────────────────────────────────────────
# Step 3 - Feature Engineering
# ─────────────────────────────────────────
print("\n[3/6] Engineering features with Spark SQL functions...")

df_features = df_clean \
    .withColumn(
        "is_delayed",
        when(col("delivery_status") == "DELAYED", 1).otherwise(0)
    ) \
    .withColumn(
        "is_express",
        when(col("priority") == "EXPRESS", 1).otherwise(0)
    ) \
    .withColumn(
        "is_long_haul",
        when(col("distance_km") > 500, 1).otherwise(0)
    ) \
    .withColumn(
        "is_heavy_cargo",
        when(col("cargo_weight_kg") > 8000, 1).otherwise(0)
    ) \
    .withColumn(
        "is_high_value",
        when(col("cargo_value_inr") > 200000, 1).otherwise(0)
    ) \
    .withColumn(
        "heavy_long_haul",
        when(
            (col("cargo_weight_kg") > 8000) &
            (col("distance_km") > 500), 1
        ).otherwise(0)
    ) \
    .withColumn(
        "revenue_per_km",
        spark_round(
            col("freight_charge_inr") / col("distance_km"), 2
        )
    ) \
    .withColumn(
        "cargo_stress_index",
        spark_round(
            col("cargo_weight_kg") * col("distance_km") / 100000, 2
        )
    ) \
    .withColumn(
        "distance_cargo_risk",
        spark_round(
            col("distance_km") * col("cargo_weight_kg") / 1000000, 4
        )
    ) \
    .withColumn(
        "express_risk_score",
        spark_round(
            col("is_express") * col("distance_km") / 100, 2
        )
    ) \
    .withColumn(
        "cargo_value_category",
        when(col("cargo_value_inr") <= 50000,  "LOW")
        .when(col("cargo_value_inr") <= 200000, "MEDIUM")
        .otherwise("HIGH")
    )

print(f"  Features added: is_delayed, is_express, is_long_haul")
print(f"  Features added: is_heavy_cargo, heavy_long_haul")
print(f"  Interaction: cargo_stress_index, distance_cargo_risk")
print(f"  Interaction: express_risk_score, revenue_per_km")
print(f"  Total columns: {len(df_features.columns)}")

# ─────────────────────────────────────────
# Step 4 - Analytics with Spark SQL
# ─────────────────────────────────────────
print("\n[4/6] Running Spark SQL analytics...")

df_features.createOrReplaceTempView("bookings")

# Delivery status breakdown
print("\n  Delivery Status Breakdown:")
status_df = spark.sql("""
    SELECT
        delivery_status,
        COUNT(*) as order_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
    FROM bookings
    GROUP BY delivery_status
    ORDER BY order_count DESC
""")
status_df.show()

# Revenue by city
print("  Revenue by Origin City (Top 5):")
city_df = spark.sql("""
    SELECT
        origin_city,
        COUNT(*) as total_orders,
        ROUND(SUM(freight_charge_inr), 0) as total_revenue,
        ROUND(AVG(distance_km), 1) as avg_distance_km,
        ROUND(SUM(is_delayed) * 100.0 / COUNT(*), 1) as delay_rate_pct
    FROM bookings
    GROUP BY origin_city
    ORDER BY total_revenue DESC
    LIMIT 5
""")
city_df.show()

# Delay analysis
print("  Delay Analysis by Priority:")
priority_df = spark.sql("""
    SELECT
        priority,
        COUNT(*) as total_orders,
        SUM(is_delayed) as delayed_orders,
        ROUND(SUM(is_delayed) * 100.0 / COUNT(*), 1) as delay_rate_pct,
        ROUND(AVG(freight_charge_inr), 0) as avg_freight_inr
    FROM bookings
    GROUP BY priority
    ORDER BY delay_rate_pct DESC
""")
priority_df.show()

# Cargo type analysis
print("  Delays by Cargo Type:")
cargo_df = spark.sql("""
    SELECT
        cargo_type,
        COUNT(*) as total_orders,
        SUM(is_delayed) as delayed_orders,
        ROUND(SUM(is_delayed) * 100.0 / COUNT(*), 1) as delay_rate_pct
    FROM bookings
    GROUP BY cargo_type
    ORDER BY delay_rate_pct DESC
""")
cargo_df.show()

# ─────────────────────────────────────────
# Step 5 - Aggregate KPIs
# ─────────────────────────────────────────
print("\n[5/6] Computing KPIs...")

kpis = df_features.agg(
    count("booking_id").alias("total_orders"),
    spark_sum("is_delayed").alias("total_delayed"),
    spark_sum("freight_charge_inr").alias("total_revenue"),
    avg("distance_km").alias("avg_distance"),
    avg("freight_charge_inr").alias("avg_freight"),
    spark_sum("is_express").alias("express_orders"),
).collect()[0]

delay_rate = round(kpis["total_delayed"] / kpis["total_orders"] * 100, 1)
express_pct = round(kpis["express_orders"] / kpis["total_orders"] * 100, 1)

print(f"\n  Total orders:      {kpis['total_orders']:,}")
print(f"  Total delayed:     {kpis['total_delayed']:,} ({delay_rate}%)")
print(f"  Total revenue:     Rs {kpis['total_revenue']:,.0f}")
print(f"  Avg distance:      {kpis['avg_distance']:.1f} km")
print(f"  Avg freight:       Rs {kpis['avg_freight']:,.0f}")
print(f"  Express orders:    {kpis['express_orders']:,} ({express_pct}%)")

# ─────────────────────────────────────────
# Step 6 - Save Results
# ─────────────────────────────────────────
print("\n[6/6] Saving processed data...")

try:
    # Save to S3 as Parquet (when on Databricks)
    OUTPUT_PATH = "s3://globetrack-analytics-zone/spark-bookings/"
    df_features.write \
        .mode("overwrite") \
        .parquet(OUTPUT_PATH)
    print(f"  Saved to S3: {OUTPUT_PATH}")
except Exception:
    
    output_path = "spark_bookings_output"
    df_features.write \
        .mode("overwrite") \
        .parquet(output_path)
    print(f"  Saved locally: {output_path}/")


print("  PYSPARK BOOKING ETL COMPLETE!")
print(f"  Records processed: {records_after:,}")
print(f"  Features created:  {len(df_features.columns)}")
print(f"  Delay rate:        {delay_rate}%")
print(f"  Total revenue:     Rs {kpis['total_revenue']:,.0f}")


spark.stop()