🐘 CSV Generator and Uploader for AWS RDS PostgreSQL

This Python script (datagen-aws-rds-postgres.py) generates large CSV files filled with random UUID data and uploads them to a specified table in an AWS RDS PostgreSQL database. It can also create the database and table if they don't exist.

**📋 Prerequisites**

Before running the script, make sure the following are available:

Linux/macOS system (or Windows WSL / PowerShell with Python installed)

Access to an AWS RDS PostgreSQL instance

Internet connection (for installing packages)

🧩 Installation Steps

1. ✅ Install Python 3 (if not already installed)

**On RHEL/CentOS:**

sudo dnf install python3 -y

**On Ubuntu/Debian:**

sudo apt update sudo apt install python3 -y 

**On macOS (using Homebrew):**

brew install python 

**2. ✅ Install required Python packages**

Use pip to install the required library:

pip3 install psycopg2-binary 

The script uses psycopg2 to interact with PostgreSQL.

**🚀 Usage Instructions**

1. Save the script as:

datagen-aws-rds-postgres.py

2. Run the script:

python3 datagen-aws-rds-postgres.py 

3. Provide required inputs when prompted:

CSV filename prefix (e.g., 1gb)

Number of files to generate (e.g., 2)

Size of each file in bytes (e.g., 1073741824 for 1 GB)

PostgreSQL database name (e.g., testdb)

Table name (e.g., testtable)

**⚙️ What the Script Does**

Generates CSV files of the specified size with 10 columns of UUIDs.

Creates the PostgreSQL database if it doesn’t exist.

Creates the table if it doesn’t exist.

Uploads the CSV data into the specified table using COPY.

📌 Notes

The script assumes the PostgreSQL RDS credentials and host are hardcoded in the script:

PG_HOST = "db1tb.c8ldg6pg7mmb.us-west-1.rds.amazonaws.com"
PG_PORT = 5432
PG_USER = "postgres"
PG_PASSWORD = "postgres"

You can change these in the script directly to match your environment.

**🛠 Example**

$ python3 datagen-aws-rds-postgres.py
Enter CSV filename prefix (e.g., 1gb): 1gb
Enter number of files to generate and upload: 1
Enter target size for each file (in bytes): 1073741824
Enter the PostgreSQL database name to create/use: testdb
Enter the table name to insert data into: datatable 

**📦 Output**

CSV files like 1gb1.csv, 1gb2.csv will be generated.

Messages will indicate database/table creation, data insertion progress, and timings.

🧹 Optional Cleanup

To remove generated CSV files:

rm 1gb*.csv
