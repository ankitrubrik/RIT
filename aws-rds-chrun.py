import psycopg2
import csv
import os
import random
import time
import tempfile

# ---- PostgreSQL connection details (hardcoded for AWS RDS) ----
HOST = "db1000.c8ldg6pg7mmb.us-west-1.rds.amazonaws.com"
PORT = 5432
USER = "postgres"
PASSWORD = "SantaClara97!"

# ---------------------------------------------------------------

def connect_db(dbname):
    try:
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            dbname=dbname
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        exit(1)

def get_table_stats(conn, table_name):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT reltuples::BIGINT AS estimate FROM pg_class WHERE relname = %s;", (table_name,))
        est_rows = cur.fetchone()[0] or -1

        cur.execute(f"SELECT pg_total_relation_size(%s);", (table_name,))
        table_size = cur.fetchone()[0]

        cur.execute("SELECT pg_database_size(current_database());")
        db_size = cur.fetchone()[0]

        return est_rows, table_size, db_size
    except Exception as e:
        print(f"❌ Could not retrieve stats: {e}")
        return -1, -1, -1
    finally:
        cur.close()

def get_column_list(conn, table_name):
    cur = conn.cursor()
    try:
        schema, table = (table_name.split('.', 1) + ['public'])[:2][::-1]
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """, (schema, table))
        cols = [r[0] for r in cur.fetchall()]
        return cols
    except Exception as e:
        print(f"❌ Failed to fetch column list: {e}")
        exit(1)
    finally:
        cur.close()

def format_size(size_bytes):
    if size_bytes <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:3.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def load_csv_to_temp(conn, csv_file, table_name):
    cur = conn.cursor()
    temp_table = f"churn_temp_{random.randint(1000000000,9999999999)}"
    cur.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table_name} INCLUDING ALL);")
    conn.commit()

    total_lines = sum(1 for _ in open(csv_file, encoding='utf-8'))
    with open(csv_file, 'r', encoding='utf-8') as f:
        next(f)  # skip header
        reader = csv.reader(f)
        inserted = 0
        start = time.time()

        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tempf:
            writer = csv.writer(tempf)
            for row in reader:
                writer.writerow(row)
                inserted += 1
                if inserted % (total_lines // 20 or 1) == 0:
                    print(f"CSV load: {int(inserted/total_lines*100)}%")
            tempf.flush()

        with open(tempf.name, 'r', encoding='utf-8') as tf:
            cur.copy_expert(f"COPY {temp_table} FROM STDIN WITH CSV", tf)

    conn.commit()
    print(f"✅ CSV loaded into {temp_table} in {time.time()-start:.2f} sec.")
    cur.close()
    return temp_table

def update_table(conn, target_table, temp_table, churn_percentage, est_rows):
    cur = conn.cursor()
    start = time.time()

    # 🔹 Fetch actual column names dynamically
    cols = get_column_list(conn, target_table)
    set_clause = ", ".join([f"{c}=t.{c}" for c in cols])

    if churn_percentage == 100:
        print("⚙️  Updating 100% of rows...")
        cur.execute(f"""
            WITH selected AS (
                SELECT ctid, row_number() OVER () AS rn FROM {target_table}
            ),
            updates AS (
                SELECT *, row_number() OVER () AS rn FROM {temp_table}
            )
            UPDATE {target_table} AS orig
            SET {set_clause}
            FROM updates t
            JOIN selected s ON t.rn = s.rn
            WHERE orig.ctid = s.ctid;
        """)
    else:
        limit_rows = int(est_rows * churn_percentage / 100)
        print(f"⚙️  Updating approximately {limit_rows:,} rows...")
        cur.execute(f"""
            WITH selected AS (
                SELECT ctid, row_number() OVER () AS rn
                FROM {target_table}
                TABLESAMPLE SYSTEM (1)
                LIMIT {limit_rows}
            ),
            updates AS (
                SELECT *, row_number() OVER () AS rn FROM {temp_table}
                LIMIT {limit_rows}
            )
            UPDATE {target_table} AS orig
            SET {set_clause}
            FROM updates t
            JOIN selected s
            ON t.rn = s.rn
            WHERE orig.ctid = s.ctid;
        """)

    conn.commit()
    print(f"✅ Churn completed in {time.time()-start:.2f} sec.")
    cur.close()

# ------------------- MAIN LOGIC -------------------

dbname = input("Enter the PostgreSQL database name: ").strip()
table_name = input("Enter the table name to churn (schema.table or table): ").strip()
conn = connect_db(dbname)

est_rows, table_size, db_size = get_table_stats(conn, table_name)
print(f"\n📊 Estimated rows in table '{table_name}': {est_rows:,}")
print(f"📦 Table size (including toast/indexes): {format_size(table_size)}")
print(f"🗄️ Database size: {format_size(db_size)}")

churn_percentage = float(input("Enter churn percentage (e.g., 5 for 5%, 100 for 100%): ").strip())
churn_rows = int(est_rows * churn_percentage / 100)
approx_churn_size = table_size * (churn_percentage / 100)
print(f"\n➡️ Rows that will be updated (estimate): {churn_rows:,}")
print(f"➡️ Approx data size to update (based on table size): {format_size(approx_churn_size)}")

csv_file = input("Enter churn CSV file name (with .csv): ").strip()
if not os.path.exists(csv_file):
    print(f"❌ CSV file not found: {csv_file}")
    exit(1)

file_size = os.path.getsize(csv_file)
print(f"\n📁 Found existing file: {csv_file} ({format_size(file_size)})")
if abs(file_size - approx_churn_size) / approx_churn_size > 0.3:
    print(f"⚠️ WARNING: File size ({format_size(file_size)}) does not match expected (~{format_size(approx_churn_size)}).")
    proceed = input("Proceed with existing file? (yes/no): ").strip().lower()
    if proceed != "yes":
        print("❌ Aborted by user.")
        exit(0)

print(f"\n⏳ Starting update: will update ≈ {churn_rows:,} rows (~{format_size(file_size)}).")
print("Please wait — starting now...\n")

temp_table = load_csv_to_temp(conn, csv_file, table_name)
update_table(conn, table_name, temp_table, churn_percentage, est_rows)
conn.close()

print(f"\n✅ Churn process completed successfully for table '{table_name}'.")


