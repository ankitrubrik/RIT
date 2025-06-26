import csv
import uuid
import os
import time
import subprocess
import psycopg2
import psycopg2.extensions
from datetime import datetime

# AWS RDS PostgreSQL connection details
PG_HOST = "pg500db1-partition.c8ldg6pg7mmb.us-west-1.rds.amazonaws.com"
PG_PORT = 5432
PG_USER = "postgres"
PG_PASSWORD = "postgres"

def generate_unique_csv(filename, target_size_bytes):
    num_columns = 10
    row_count = 0

    print(f"\n⏳ Generating file: {filename}")
    start_time = time.time()

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        header = [f"Column_{i+1}" for i in range(num_columns)]
        writer.writerow(header)

        while True:
            row = [str(uuid.uuid4()) for _ in range(num_columns)]
            writer.writerow(row)
            row_count += 1

            if os.path.getsize(filename) >= target_size_bytes:
                break

    end_time = time.time()
    duration = end_time - start_time

    try:
        size_output = subprocess.check_output(['du', '-sh', filename])
        human_size = size_output.decode().split()[0]
    except Exception:
        human_size = f"{os.path.getsize(filename)} bytes"

    print(f"✅ CSV generation complete: {filename}")
    print(f"📊 Rows written: {row_count}")
    print(f"⏱️ Time taken: {duration:.2f} seconds")
    print(f"💾 File size: {human_size}")

def create_database_and_table(dbname, table_name, csv_file):
    total_start = time.time()
    start_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname="postgres"
        )
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = %s;", (dbname,))
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {dbname};")
            print(f"✅ Database '{dbname}' created.")
        else:
            print(f"ℹ️ Database '{dbname}' already exists.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return

    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=dbname
        )
        cursor = conn.cursor()

        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            );
        """, (table_name,))
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                columns = ', '.join(f"{col} TEXT" for col in header)
                cursor.execute(f"CREATE TABLE {table_name} ({columns});")
                conn.commit()
                print(f"✅ Table '{table_name}' created in database '{dbname}'.")
        else:
            print(f"🔄 Table '{table_name}' already exists. Appending data...")

        with open(csv_file, 'r', encoding='utf-8') as f:
            next(f)
            cursor.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV", f)
            conn.commit()

        cursor.close()
        conn.close()
        end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_end = time.time()
        print(f"✅ Data inserted into table '{table_name}' from {csv_file}.")
        print(f"🕓 Started: {start_dt} | Ended: {end_dt}")
        print(f"⏱️  DB operation time: {total_end - total_start:.2f} seconds")

    except Exception as e:
        print(f"❌ Failed to insert data: {e}")

if __name__ == "__main__":
    prefix = input("Enter CSV filename prefix (e.g., 1gb): ").strip()
    total_files = int(input("Enter number of files to generate and upload: "))
    target_size = int(input("Enter target size for each file (in bytes): "))
    dbname = input("Enter the PostgreSQL database name to create/use: ").strip()
    table_name = input("Enter the table name to insert data into: ").strip()

    for i in range(1, total_files + 1):
        filename = f"{prefix}{i}.csv"
        if os.path.exists(filename):
            print(f"📁 File '{filename}' already exists. Reusing it.")
        else:
            generate_unique_csv(filename, target_size)

        print("\n🔗 Connecting to PostgreSQL...")
        create_database_and_table(dbname, table_name, filename)
        print("\n-------------------------------\n")

