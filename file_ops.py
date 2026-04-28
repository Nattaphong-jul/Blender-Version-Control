import os
import shutil
import datetime

def copy_file(source_path, destination_folder):
    destination_folder = os.path.join(destination_folder, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(destination_folder, exist_ok=True)
    shutil.copy(source_path, destination_folder)
    print(f"Copied {os.path.basename(source_path)} to {destination_folder}")

source = os.path.join(os.path.dirname(__file__), "example_file.txt")
destination = os.path.join(os.path.dirname(__file__), "test")
copy_file(source, destination)