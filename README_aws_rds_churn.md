🐘 AWS RDS PostgreSQL Churn Script
📄 Overview
The AWS RDS PostgreSQL Churn Script is designed to simulate data churn (updates) on large PostgreSQL tables hosted on AWS RDS.
It allows you to update a configurable percentage of rows (e.g., 5%, 10%, 100%) using data from a CSV file — ideal for performance testing, I/O benchmarking, and scale validation.

This script efficiently handles large datasets (up to TB scale) with batch updates, optimized CSV loading, and minimal transaction overhead.

⚙️ Features
✅ Supports any churn percentage (5%, 10%, 100%)
✅ Dynamically estimates row count and table size
✅ Supports schema.table or just table name
✅ Uses UNLOGGED temp tables for faster CSV load (no WAL logging)
✅ Performs batch updates for large tables (configurable batch size)
✅ Dynamically adapts to table schema (auto-discovers columns)
✅ Prints real-time progress updates
✅ Safe and resumable (can re-run with existing CSV)
✅ Works with AWS RDS PostgreSQL or any self-managed PostgreSQL

🧱 Requirements
Python 3.7+

PostgreSQL (local or AWS RDS)

Python packages:



pip install psycopg2-binary
Database user must have:

SELECT, UPDATE, CREATE TABLE, and DROP TABLE privileges.

🧩 Script Configuration
At the top of the script (aws_rds_churn.py):



PG_HOST = "your-db-endpoint.amazonaws.com"
PG_PORT = 5432
PG_USER = "your-username"
PG_PASSWORD = "your-password"
BATCH_SIZE = 5_000_000   # Batch commit size (default: 5M rows)
🧠 Tip: For huge tables (>500 GB), you can increase BATCH_SIZE to 10M–20M rows.
For smaller tables (<100 GB), you can reduce it to 1M–2M rows.

🧮 How It Works
Connects to PostgreSQL using provided credentials.

Estimates row count and table size using PostgreSQL system catalogs.

Prompts user for:

Churn percentage (e.g., 5, 100)

CSV file to use (existing or new)

If CSV doesn’t exist, generates it with random text data.

Creates an UNLOGGED temp table (faster, no WAL).

Loads CSV file into temp table.

Performs batched updates on the main table:

Updates data from temp table in chunks.

Commits after each batch.

Cleans up temp table and reports summary statistics.

🚀 Usage
Run the script from a terminal:



python3 aws_rds_churn.py
Example session:



Enter the PostgreSQL database name: db50
Enter the table name to churn (schema.table or table): public.db50
📊 Estimated rows in table 'db50': 134,659,248
📦 Table size (including toast/indexes): 54.51 GB
🗄️ Database size: 54.51 GB
Enter churn percentage (e.g., 5 for 5%, 100 for 100%): 5
➡️ Rows that will be updated (estimate): 6,732,962
➡️ Approx data size to update (based on table size): 2.73 GB
Enter churn CSV file name (with .csv): test_data.csv
📁 Found existing file: test_data.csv (954 MB)
⚠️ WARNING: File size does not match expected (~2.73 GB).
Proceed with existing file? (yes/no): yes
⏳ Starting update: will update ≈ 6,732,962 rows (~954 MB)...
CSV load: 5%
CSV load: 10%
...
✅ CSV loaded into churn_temp_1757920859 in 29.0 sec.
⚙️ Applying updates in batches of 5,000,000 rows...
✅ Churn completed in 270.28 sec.
📊 Output Summary
Metric

Description

Estimated rows

Approximate total rows in table

Churn %

Percentage of rows to update

Churn rows

Number of rows targeted for update

CSV load time

Time taken to import churn data

Update time

Total time to apply updates

Total elapsed

End-to-end churn time

⚡ Performance Tuning Tips
Parameter

Recommendation

Parameter

Recommendation

BATCH_SIZE

Increase for large DBs (10M–20M rows), reduce for small

maintenance_work_mem

Increase to at least 512MB for faster updates

synchronous_commit

Set to off for churn tests (non-production only)

work_mem

256MB or higher for large joins

temp_buffers

Increase to 256MB for better temp table performance

RDS Instance Type

Use at least db.m6i.4xlarge for TB-scale testing

Storage

Prefer GP3 or IO2 volumes for better IOPS

🧹 Cleanup
After the churn process completes, the script automatically drops the temporary table (churn_temp_<random_id>).
No permanent schema changes are made.

🧠 FAQs
Q: Does this script delete data?
No. It only performs UPDATE operations.

Q: Can I stop and restart?
Yes, if the CSV file already exists, the script will reuse it.

Q: Can I use it on non-AWS PostgreSQL?
Yes. It works on any PostgreSQL environment with proper access.

Q: What if I want to update 100% rows?
Simply enter 100 when asked for the churn percentage.
