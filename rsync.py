#!/usr/local/bin/python3.9
import sys
import subprocess
import os


# Function to create a destination directory if it doesn't exist
def create_destination_directory(destination_path):
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)


source_path, destination_path = sys.argv[1].split(",")

create_destination_directory(destination_path)
rsync_cmd = ["rsync", "-avz", "-e", "ssh", source_path, destination_path]
subprocess.call(rsync_cmd)

