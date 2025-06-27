import csv
import uuid
import os
import time
import pwd
import grp
from datetime import datetime
import mysql.connector
from mysql.connector import errorcode

# MySQL connection details
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "C0mpL@b123"

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

    size_output = os.popen(f"du -sh {filename}").read().split()[0]
    print(f"✅ CSV file '{filename}' generated: {row_count} rows, {size_output}, in {duration:.2f} seconds")

def change_file_ownership(filename):
    try:
        uid = pwd.getpwnam("mysql").pw_uid
        gid = grp.getgrnam("mysql").gr_gid
        os.chown(filename, uid, gid)
        print(f"🔐 Ownership set to mysql:mysql for '{filename}'")
    except Exception as e:
        print(f"⚠️ Warning: Could not change ownership: {e}")

def create_database_if_not_exists(dbname):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            autocommit=True
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE %s;", (dbname,))
        if cursor.fetchone():
            print(f"📂 Database '{dbname}' already exists.")
        else:
            cursor.execute(f"CREATE DATABASE `{dbname}`;")
            print(f"✅ Database '{dbname}' created.")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ DB Error: {err}")

def connect_to_database(dbname):
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=dbname,
        allow_local_infile=True
    )

def create_table_if_not_exists(cursor, table_name, csv_file):
    cursor.execute(f"SHOW TABLES LIKE %s;", (table_name,))
    if cursor.fetchone():
        print(f"🔄 Table '{table_name}' exists. Appending data...")
        return

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        columns = ', '.join(f"`{col}` TEXT" for col in header)
        cursor.execute(f"CREATE TABLE `{table_name}` ({columns});")
        print(f"✅ Table '{table_name}' created.")

def load_csv_into_table(conn, cursor, table_name, csv_file):
    abs_path = os.path.abspath(csv_file).replace("\\", "/")
    load_sql = f"""
    LOAD DATA LOCAL INFILE '{abs_path}'
    INTO TABLE `{table_name}`
    FIELDS TERMINATED BY ','
    ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS;
    """
    cursor.execute(load_sql)
    conn.commit()

def process_mysql_load(dbname, table_name, csv_file):
    total_start = time.time()
    start_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    create_database_if_not_exists(dbname)

    try:
        conn = connect_to_database(dbname)
        cursor = conn.cursor()

        create_table_if_not_exists(cursor, table_name, csv_file)
        load_csv_into_table(conn, cursor, table_name, csv_file)

        end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_end = time.time()

        print(f"\n✅ Loaded '{csv_file}' into '{table_name}' in DB '{dbname}'")
        print(f"🕓 Started: {start_dt}, Ended: {end_dt}, Duration: {total_end - total_start:.2f}s")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ MySQL error: {err}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 MySQL CSV Generator & Loader")

    prefix = input("📄 Enter CSV file prefix (e.g., '1gb'): ").strip()
    file_count = int(input("🔁 How many files to work with?: "))
    dbname = input("💽 MySQL DB name to use/create: ").strip()
    table_name = input("📊 Table name to insert into: ").strip()

    missing_files = []
    for i in range(1, file_count + 1):
        filename = f"{prefix}{i}.csv"
        if not os.path.exists(filename):
            missing_files.append(filename)

    if missing_files:
        target_size = int(input("💾 Target file size in bytes (e.g., 1073741824 for 1GB): "))
        for filename in missing_files:
            generate_unique_csv(filename, target_size)
            change_file_ownership(filename)
    else:
        print("📁 All files already exist. Skipping CSV generation.")

    for i in range(1, file_count + 1):
        filename = f"{prefix}{i}.csv"
        process_mysql_load(dbname, table_name, filename)

    print("\n✅ All files processed.")

