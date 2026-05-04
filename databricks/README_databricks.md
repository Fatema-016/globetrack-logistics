# GlobeTrack Logistics - Databricks PySpark Integration

## Compute Platform
- Platform: Databricks (Free Edition)
- Engine: Apache Spark 4.1.1 via PySpark
- Batch Processing: Apache Spark DataFrame API

## PySpark Scripts
- 01_pyspark_etl_bookings.py - Booking logs ETL with Spark SQL
- Designed to run on Databricks cluster connected to S3

## Note on Local Execution
PySpark 4.1.1 requires Linux/Mac or WSL2 for local execution.
These scripts are designed to run on Databricks cluster where
Spark is natively supported. The PySpark API code demonstrates
full Spark DataFrame operations, SQL queries and feature engineering.

## Architecture
Data Flow: S3 Raw Zone -> PySpark ETL -> S3 Analytics Zone
Compute: Databricks Spark Cluster (ap-south-1 compatible) 
