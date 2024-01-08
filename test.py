import yaml
import shutil
import time
import os

config="/tools/common/cfg/deadline_transfer.yaml"

def transfer_file(source_path, destination_path, deadline_seconds):
    # Check if the source file exists
    if not os.path.exists(source_path):
        print(f"Error: Source file '{source_path}' not found.")
        return

    start_time = time.time()

    try:
        # Copy the file to the destination
        shutil.copy(source_path, destination_path)
        print(f"File transferred successfully from '{source_path}' to '{destination_path}'.")
    except Exception as e:
        print(f"Error: {e}")

    elapsed_time = time.time() - start_time

    # Check if the transfer took more time than the deadline
    if elapsed_time > deadline_seconds:
        print(f"Warning: The file transfer took longer than the specified deadline of {deadline_seconds} seconds.")

def get_file_and_folder_config(city):
    with open(config, 'r') as file:
        data = yaml.safe_load(file)

        if city in data:
            city_data = data[city]
            blades = city_data.get('blades', [])
            server = city_data.get('server', {})

            if blades:
                source_file = blades[0] if blades else None
            else:
                source_file = None

            server_folders = []
            for server_name, folders in server.items():
                server_folders.extend(folders)

            if server_folders:
                destination_folder = server_folders[0] if server_folders else None
            else:
                destination_folder = None

            return source_file, destination_folder
        else:
            print(f"Error: City '{city}' not found in the configuration.")

# Get city from the user
city = input("Enter the city (e.g., chennai, pune): ")

# Get file and folder configuration based on the city
source_file, destination_folder = get_file_and_folder_config(city)

if source_file and destination_folder:
    print(f"Source File: {source_file}")
    print(f"Destination Folder: {destination_folder}")

    # Get source file path from the user
    source_file_path = input("Enter the full path of the source file: ")

    # Get deadline from the user
    deadline_seconds = int(input("Enter the deadline for file transfer in seconds: "))

    # Perform the file transfer with the given deadline
    transfer_file(source_file_path, destination_folder, deadline_seconds)
else:
    print("Error getting file and folder configuration.")


# def get_file_and_folder_config(city):
#     with open(config, 'r') as file:
#         data = yaml.safe_load(file)

#         if city in data:
#             city_data = data[city]
#             blades = city_data.get('blades', [])
#             server = city_data.get('server', {})

#             if blades:
#                 source_file = blades[0] if blades else None
#             else:
#                 source_file = None

#             server_folders = []
#             for server_name, folders in server.items():
#                 server_folders.extend(folders)

#             if server_folders:
#                 destination_folder = server_folders[0] if server_folders else None
#             else:
#                 destination_folder = None

#             return source_file, destination_folder
#         else:
#             print(f"Error: City '{city}' not found in the configuration.")

# # Get city from the user
# city = input("Enter the city (e.g., chennai, pune): ")

# # Get file and folder configuration based on the city
# source_file, destination_folder = get_file_and_folder_config(city)

# if source_file and destination_folder:
#     print(f"Source File: {source_file}")
#     print(f"Destination Folder: {destination_folder}")
# else:
#     print("Error getting file and folder configuration.")

