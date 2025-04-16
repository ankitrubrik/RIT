import csv
import uuid
import os
import time
import subprocess

def generate_unique_csv(filename, target_size_bytes):
    num_columns = 10
    row_count = 0

    print("\nPlease wait... File generation in progress.\n")
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

    # Get human-readable file size using du (works on Unix systems)
    try:
        size_output = subprocess.check_output(['du', '-sh', filename])
        human_size = size_output.decode().split()[0]
    except Exception as e:
        human_size = f"{os.path.getsize(filename)} bytes (du not available)"

    print("\nCSV generation complete.")
    print(f"File: {filename}")
    print(f"Rows written: {row_count}")
    print(f"Generation time: {duration:.2f} seconds")
    print(f"Final file size: {human_size}")

if __name__ == "__main__":
    filename = input("Enter the file name (with .csv extension): ").strip()
    if not filename.endswith('.csv'):
        filename += '.csv'
    target_size = int(input("Enter target file size in bytes: "))
    generate_unique_csv(filename, target_size)

