import csv
import uuid
import os
import math
import time
import subprocess

def convert_size(size_bytes):
    """Converts a size in bytes to a human readable string with appropriate units.
    Args:
        size_bytes: The size in bytes.
    Returns:
        A string representing the size in human readable format.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def generate_unique_data(filename, target_size_bytes, batch_size=1000):
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['column1', 'column2', 'column3', 'column4', 'column5', 'column6', 'column7', 'column8', 'column9', 'column10']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:
            writer.writeheader()
            print("Writing header to CSV file...")

        # Adjust estimated_row_size based on your actual row size
        estimated_row_size = 100  # Adjust this value as needed

        target_row_count = target_size_bytes // estimated_row_size

        batch = []
        current_size = 0
        start_time = time.time()  # Record the start time
        for _ in range(target_row_count // batch_size + 1):
            for _ in range(batch_size):
                row = {
                    'column1': str(uuid.uuid4()),
                    'column2': str(uuid.uuid4()),
                    'column3': str(uuid.uuid4()),
                    'column4': str(uuid.uuid4()),
                    'column5': str(uuid.uuid4()),
                    'column6': str(uuid.uuid4()),
                    'column7': str(uuid.uuid4()),
                    'column8': str(uuid.uuid4()),
                    'column9': str(uuid.uuid4()),
                    'column10': str(uuid.uuid4())
                }
                batch.append(row)
            writer.writerows(batch)
            batch.clear()
            current_size = os.path.getsize(filename)
            print(f"Current file size: {convert_size(current_size)}")

            # Check if the current file size is close to the target size
            if target_size_bytes - current_size < batch_size * estimated_row_size:
                # Adjust the batch size to ensure the final file size is close to the target
                batch_size = (target_size_bytes - current_size) // estimated_row_size

    # Change file ownership using subprocess
    subprocess.run(["chown", "postgres:postgres", filename])

    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time
    print(f"Script execution completed in {elapsed_time:.2f} seconds.")

def get_filename():
    filename = input("Enter the desired filename (with .csv extension): ")
    while os.path.exists(filename):
        print("File already exists. Please enter a different name.")
        filename = input("Enter the desired filename (with .csv extension): ")
    return filename

if __name__ == "__main__":
    filename = get_filename()
    target_size_bytes = int(input("Enter target file size in bytes: "))
    generate_unique_data(filename, target_size_bytes)
