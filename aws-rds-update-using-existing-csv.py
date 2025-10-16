import csv
import uuid
import os
import time
import subprocess
import psycopg2
import psycopg2.extensions
from datetime import datetime

# AWS RDS PostgreSQL connection details
PG_HOST = "db.c8ldg6pg7mmb.us-west-1.rds.amazonaws.com"
PG_PORT = 5432
PG_USER = "postgres"
PG_PASSWORD = "Password"

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
            next(f)  # skip header
            cursor.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV", f)
            conn.commit()

        cursor.close()
        conn.close()
        end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_end = time.time()
        print(f"✅ Data inserted from {csv_file}.")
        print(f"🕓 Started: {start_dt} | Ended: {end_dt}")
        print(f"⏱️  Time taken: {total_end - total_start:.2f} sec")

    except Exception as e:
        print(f"❌ Failed to insert data: {e}")

if __name__ == "__main__":
    prefix = input("Enter CSV filename prefix (e.g., 1gb1): ").strip()
    dbname = input("Enter PostgreSQL database name: ").strip()
    table_name = input("Enter table name: ").strip()

    matching_files = sorted(f for f in os.listdir('.') if f.startswith(prefix) and f.endswith('.csv'))

    if not matching_files:
        print(f"❌ No files found with prefix '{prefix}'")
    else:
        print(f"🔍 Found {len(matching_files)} matching file(s). Starting upload...\n")

        for filename in matching_files:
            print(f"\n📁 Processing: {filename}")
            create_database_and_table(dbname, table_name, filename)
            print("\n-------------------------------\n")


