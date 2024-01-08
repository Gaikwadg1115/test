'''
run cmd:- 

    python3.9 main -src /brahmos/projects/TestPiped/shots/sq_002 -dst chennai
'''

#!/usr/local/bin/python3.9
import argparse
import subprocess
import os
import socket
import logging
import re
import yaml
import time
import grp

from pathlib import Path


# Parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", "--source", required=True, help="Source file or folder path")
    parser.add_argument("-dst", "--destination", required=True, help="Location name")
    parser.add_argument("-se", "--server", required=False)
    args = parser.parse_args()

    return args
config="/tools/common/cfg/deadline_transfer.yaml"

# Initialize the logger
def get_logger():
    if not os.path.exists("log"):
        os.makedirs("log")
    logging.basicConfig(
        filename="log/deadline_transfer_log.log",
        format="%(asctime)s %(message)s",
        filemode="a",
    )

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger


# # Read data from YAML file
def read_config(config_file):
    with open(config_file, "r") as f:
        return yaml.safe_load(f)


# # Get server and mount details from path
def extract_path(path):
    path_split = path.split(os.sep)
    return path_split[1], path_split[2]


# # Write job information to a file
def write_job_info_file(details):
    job_info_file = os.getcwd() + "/job_info.job"
    with open(job_info_file, "w+") as file:
         file.write(details)
    return job_info_file


# # Extract the JobID from the output
def extract_job_id(stdout_lines):
     job_id = None

#     # Extract the JobID from the output
     for line in stdout_lines:
        if "JobID" in line:
             job_id = line[6::]
     return job_id

# Extract the progress percentage and job status from job details
# def extract_progress_and_job_status(lines):
#     progress_percent = None
#     job_status = "Unknown"  # Default status if not found in the details

#     for line in lines:
#         if "Status:" in line:
#             job_status = line.split("Status:")[1].strip().lower()
#         if "Progress:" in line:
#             progress_match = re.search(r"Progress:(\d+\s*%)\s+\(\d+/\d+\)", line)
#             if progress_match:
#                 progress_percent = int(progress_match.group(1).replace("%", "").strip())

#     return progress_percent, job_status


# Write plugin information to a file
# def write_plugin_info_file(details):
#     plugin_info_file = os.getcwd() + "/plugin_info.job"
#     with open(plugin_info_file, "w+") as file:
#         file.write(details)
#     return plugin_info_file

# def show_progress_bar(percentage, length=50):
#     block = int(round(length * percentage / 100))
#     progress = "█" * block + "-" * (length - block)
#     print(f"[{progress}] {percentage:.1f}%", end="\r")

# Submit the job to Deadline

def submit_to_deadline(file_source,destination_server):
    LOGGER = get_logger()
    # Define the path to the Deadline Command executable
    deadline_cmd = "/opt/Thinkbox/Deadline10/bin/deadlinecommand"
    # print ("****submit_to_deadline file_source",file_source)
    # print ("****submit_to_deadline destination_server",destination_server)
    # Write job and plugin information to temporary files
    job_file = write_job_info_file(str(destination_server).strip())
    plugin_file = write_plugin_info_file(str(file_source).strip())
    print ("****submit_to_deadline file_source",file_source)
    print ("****submit_to_deadline destination_server",destination_server)
    # Define the path to the script to be executed by Deadline
    py_file = os.getcwd() + "/rsync"

    # Create a list containing the command to execute the Deadline job
    command = [deadline_cmd, job_file, plugin_file, py_file]

    # Execute the command to submit the job to Deadline
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Extract the 'Allowlist' information from job details
    allowlist_match = re.search(r"Allowlist=(.*)", destination_server)
    allowlist = allowlist_match.group(1).strip() if allowlist_match else "N/A"

    # Capture the standard output (stdout) and standard error (stderr) of the process
    stdout, stderr = process.communicate()
    # Log job submission status
    if stdout:
        LOGGER.info(
            f"Source path: {file_source}, Machine Name: {socket.gethostname()}, User Name: {os.getlogin()}, Render blade: {allowlist}, Submitted successfully"
        )
    
    # Log error if job submission fails
    if stderr:
        stderr_message = stderr.decode("utf-8")
        LOGGER.error(
            f"ERROR - Source path: {file_source}, Machine Name: {socket.gethostname()}, User Name: {os.getlogin()}, Render blade: {allowlist}, Submitted Failed, \nError: {stderr_message}"
        )

    stdout_lines = stdout.decode("utf-8").split("\n")
    job_id = extract_job_id(stdout_lines)

    

    # Continuously query the job's progress until it's complete
    while True:
        try:
            # Define the command to get job details using the JobID
            cmd = [deadline_cmd, "-GetJobDetails", job_id]

            # Execute the command to get job details
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            lines = stdout.split("\n")
            progress_percent, job_status = extract_progress_and_job_status(lines)
      
            # Display the progress using a progress bar
            if progress_percent is not None:
                show_progress_bar(progress_percent, length=50)

            # If the job status is "Failed," break the loop
            if job_status == "failed":
                print("\n")
                print("Failed to transfer to the destination path.")
                print("JOBID => ",job_id)
                print("Please contact pipeline team to check this issue")
                break
            elif job_status=='suspended':
                print("\n")
                print("job is suspended")
                print("JOBID => ", job_id)
                print("Please contact pipeline team to check this issue")
                break
            

            # If progress reaches 100%, the job is successfully completed
            if progress_percent is not None and progress_percent >= 100:
                print("\n")
                print("Successfully transferred to the destination path.")
                break

            # Wait for a second before checking progress again
            time.sleep(1)
        except Exception as e:
            # Handle and log errors that occur during progress checking
            LOGGER.error(f"Error while checking job progress: {str(e)}")


# def get_location_long_name(shortname):
#     loc_detail = {"chn": "chennai", "pne": "pune", "hyd": "hyderabad"}
#     return loc_detail.get(shortname, None)


# def get_source_config():
#     LOGGER = get_logger()
#     machine_name = socket.gethostname()
#     source_location = get_location_long_name(machine_name[:3])
#     if source_location in config:
#         source_config = config[source_location]
#         return source_location, source_config
#     else:
#         LOGGER.error(
#             f"Unable to find the source location of the machine {machine_name}"
#         )
#         raise ValueError(
#             f"Unable to find the source location of the machine {machine_name}"
#         )


# def validate_user_access(file_source,server):
#     file_path = file_source
#     LOGGER = get_logger()
#     # this will get the all user group name and file name
#     getfacl_output = subprocess.check_output(["getfacl", "-p", file_path])
#     file_group_names = []
#     for line in getfacl_output.decode("utf-8").split("\n"):
#         if line.startswith("group:"):
#             file_group_names.extend(line.split(":")[1].strip().split(","))

#     username = os.getlogin()
#     user_group = [grp.getgrgid(g).gr_name for g in os.getgroups()]
#     print("---user_group",user_group)

#     for user_groups in user_group:
#         if user_groups in file_group_names:
#             LOGGER.info(f"The user group{user_group} has access to the file.")
#             return True
#         else:
#             LOGGER.error("You don't have access to the file. Permission denied.")
#             raise ValueError("You don't have access to the file. Permission denied.")


# def validate_source_path(source_config,file_source):
#     LOGGER = get_logger()
#     source_path = file_source
#     print ("----source_path",source_path)
#     # source_mount = source_path.split(os.sep)[1]
#     # print ("----source_mount",source_mount)

#     if not os.path.exists(source_path):
#         LOGGER.error("Source path not exists")
#         raise ValueError(f"Source path not exists {source_path}")

#     # for mount_prefix in source_config["server"].values():
#     #     for mount in mount_prefix:
#     #         if source_mount in mount:
#     #             return True

#         # LOGGER.error("Invalid source path")
#         # raise ValueError("Invalid source path", source_path)


def get_source_and_destination(file_source,server):
    destination_location = server.lower()
    source_path = file_source
    source_location=file_source
    source_config = "/tools/common/cfg/deadline_transfer.yaml"
    # validate_source_path(source_config,file_source)
#     # validate_user_access(file_source,server)


#     if destination_location in config:
#         LOGGER = get_logger()
#         destination_config = config[destination_location]
#         allowlist = ",".join(destination_config.get("blades", []))
#         if destination_location:
#             server_name =destination_location
#         else:
#             # Get the first key of the server dictionary as the default server name
#             server_name = list(destination_config["server"].keys())[0]

#         # Check if the specified server_name exists in the server dictionary
#         if server_name not in destination_config["server"]:
#             LOGGER.error(
#                 f"ERROR - Invalid server name. Available options for '{destination_location}' are {', '.join(destination_config['server'].keys())}, but given server name is {server_name}"
#             )
#             raise ValueError(
#                 f"Invalid server name. Available options are {', '.join(destination_config['server'].keys())}"
#             )

#         server_prefix = destination_config["server"][server_name]

#         # Check if the source path starts with any of the server_prefix
#         matched_key = next(
#             (key for key in server_prefix if source_path.startswith(key)), None
#         )

#         if matched_key:
#             destination_path = source_path  # Use the same path as source
#         else:
#             destination_path = server_prefix[0]

#             # Extract the next-level directory from source and destination paths
#             source_server, source_mount = extract_path(source_path)
#             destination_server, destination_mount = extract_path(destination_path)
#             if source_server == destination_server:
#                 LOGGER.error(
#                     f"Source-{source_server} and destination-{destination_server} servers are same."
#                 )
#                 raise ValueError(
#                     f"Source-{source_server} and destination-{destination_server} servers are same."
#                 )

#             if source_mount != destination_mount:
#                 LOGGER.error(
#                     f"Source-{source_mount} and destination-{destination_mount} mounts are different"
#                 )
#                 raise ValueError(
#                     f"Source-{source_mount} and destination-{destination_mount} mounts are different"
#                 )

#             source_server_prefix = source_config["server"].get(source_server, None)[0]
#             print("-----source_server_prefix",source_server_prefix)
#             destination_path = (
#                 destination_path + source_path.split(source_server_prefix)[1]
#             )

#         if source_location != destination_location:
#             source_path = f"{source_config['blades'][0]}:{source_path}"
#         rsync_arguments = f"{source_path},{destination_path}"

#         return allowlist, rsync_arguments

#     else:
#         LOGGER.error(
#             f"ERROR - Invalid destination. Available options are {', '.join(config.keys())}, but given destination is {destination_location}"
#         )
#         raise ValueError(
#             f"Invalid destination. Available options are {', '.join(config.keys())}"
#         )



# get information and transfer files
def get_info_txt():
    machinename = socket.gethostname()
    allowlist, rsync_arguments = get_source_and_destination(file_source,server)
    print ("machinename=========",machinename)
    print ("allowlist=========",allowlist)
    print ("rsync_arguments=========",rsync_arguments)
    src = f"""
    Arguments= {rsync_arguments}
    SingleFramesOnly=False
    Version=3.7
    """

    dest = f"""
    Plugin=Python
    Name=Transfer
    Comment=None
    Allowlist={allowlist}
    Pool=pip_pool
    Group=pip
    Priority=50
    TaskTimeoutMinutes=0
    ConcurrentTasks=1
    Frames=1
    UserName={os.getlogin()}
    MachineName={machinename}
    """
    print ("dest=========",dest)
    print ("src=========",src)
    return src, dest


def deadline_ingest(publish_data,server):
    file_source = publish_data['sg_filepath']
    # dst=server
    # args = parse_args()
    print("=====file_source=========",file_source)
    print("============ server",server)
    file_source, server = get_info_txt(file_source,server)
    # shots.create(args.project, args.sequence, args.shot, args.dept, args.config)
    if server =='brahmos':
        destination_server="chennai"
        submit_to_deadline(file_source,destination_server)

if __name__ == "__main__":
    os.chdir(
        Path(__file__).resolve().parent
    )  # Change directory from symlink directory to project directory
    LOGGER = get_logger()
    args = parse_args()
    config = read_config("/tools/common/cfg/deadline_transfer.yaml")
    src, dest = get_info_txt()
    print ("****get_info_txt src",src)
    print ("****get_info_txt dest",dest)
    submit_to_deadline(src, dest)
    

