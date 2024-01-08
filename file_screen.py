"""
file_screen.py:

This module defines the IngestFileScreening class, which is
 responsible for screening and processing files
   during the ingest process.

Classes:
    IngestFileScreening:
        A class for organizing and processing files based on 
        specified criteria during the ingest process.

Functions:
    get_shotgrid_department_name():
        Retrieves and returns a sorted list of 
        Shotgrid department names.

Usage:
    # Example usage of the IngestFileScreening class
    ingest_screening = IngestFileScreening(yaml_data=my_yaml_data)
    result = ingest_screening.separate_the_ingest_files(
        source_path="path/to/files",
        project_name="MyProject",
        server_name="MyServer"
    )
    print(result)

    # Example usage of the get_shotgrid_department_name function
    departments = get_shotgrid_department_name()
    print(departments)

Note: Replace `my_yaml_data` with the actual YAML 
data containing information for the ingest process.
"""


import os
import re
import struct
import cv2
import fileseq

from PIL import Image
from sg_utils import read


class ingest_file_screening:
    """
    Class for screening and processing 
    files during the ingest process.

    Attributes:
        department_list (list): A list of Shotgrid department names.
        ingest_data (dict): YAML data containing information for the ingest process.
        load_table_data (dict): A dictionary to store organized data for each table during screening.
        project_name (str): The name of the project associated with the files.
    """

    def __init__(self, yaml_data=None):
        """
        Initialize the IngestFileScreening object.

        Args:
            yaml_data (dict): YAML data containing information for the ingest process.
        """
        super(ingest_file_screening, self).__init__()
        self.department_list = get_shotgrid_department_name()
        self.ingest_data = yaml_data
        self.load_table_data = dict()
        self.project_name = None

    # class ingest_file_screening:
    #     def __init__(self, yaml_data=None):
    #         super(ingest_file_screening, self).__init__()
    #         self.department_list = get_shotgrid_department_name()
    #         self.ingest_data = yaml_data
    #         self.load_table_data = dict()
    #         # self.server_name=None
    #         self.project_name = None

    def separate_the_ingest_files(self, source_path, project_name, server_name):
        """
        Separate and organize files from the given source_path based on the specified project_name and server_name.

        Args:
            source_path (str): The root directory path containing the files to be ingested.
            project_name (str): The name of the project for which the files are being ingested.
            server_name (str): The name of the server associated with the files.

        Returns:
            dict: A dictionary containing organized data for each table in the ingest process.
                The structure of the dictionary is as follows:
                {
                    'table_name_1': {
                        'data': [list_of_data_for_table_1],
                        'column_head': [list_of_column_heads_for_table_1],
                        'source_path': [list_of_source_paths_for_table_1],
                    },
                    'table_name_2': {
                        'data': [list_of_data_for_table_2],
                        'column_head': [list_of_column_heads_for_table_2],
                        'source_path': [list_of_source_paths_for_table_2],
                    },
                    ...
                    'UnMatched': {
                        'data': [list_of_data_for_unmatched_files],
                        'source_path': [list_of_source_paths_for_unmatched_files],
                    }
                }
        """
        self.server_name = server_name
        self.project_name = project_name
        for key, value in self.ingest_data["Table"].items():
            self.load_table_data[key] = {
                "data": [],
                "column_head": value["table_head"],
                "source_path": [],
            }

        # Use a dictionary to store sequences based on base name
        sequences = {}

        for root, dirs, files in os.walk(source_path):
            file_sequence = fileseq.findSequencesOnDisk(root)

            for seq in file_sequence:
                for key, value in reversed(self.ingest_data["Table"].items()):
                    filename = os.path.basename(str(seq))
                    regex = re.search(self.ingest_data["Table"][key]["regex"], filename)
                    filename_extension = (filename.split(".")[-1]).lower()
                    table_name = key

                    if len(seq) > 1:
                        # Check if it's an image sequence based on naming convention
                        if any(
                            element in filename.lower()
                            for element in self.ingest_data["Table"][table_name][
                                "filter"
                            ]
                            or []
                        ) or (
                            regex
                            and filename_extension == "exr"
                            or filename_extension == "mov"
                        ):  # Check for sequence
                            data = self.build_ingest_data(table_name,self.server_name, seq, regex)
                            self.load_table_data[table_name]["data"].append(data)
                            self.load_table_data[table_name]["source_path"].append(seq)
                            break
                    elif (
                        filename_extension
                        in self.ingest_data["Table"][table_name]["extensions"]
                    ):
                        data = self.build_ingest_data(table_name, self.server_name , seq, regex)
                        self.load_table_data[table_name]["data"].append(data)
                        self.load_table_data[table_name]["source_path"].append(seq)
                        break
                else:
                    if (
                        filename_extension
                        in self.ingest_data["Table"][table_name]["extensions"]
                    ):
                        data = self.build_ingest_data(table_name, self.server_name,seq, regex)
                        self.load_table_data[table_name]["data"].append(data)
                        self.load_table_data[table_name]["source_path"].append(seq)
                    else:
                        data = self.build_ingest_data("UnMatched",self.server_name, seq, None)
                        self.load_table_data["UnMatched"]["data"].append(data)
                        self.load_table_data["UnMatched"]["source_path"].append(seq)

        # Process accumulated sequences
        for base_name, seq_list in sequences.items():
            # Check if there are multiple files with the same base name
            if len(seq_list) > 1:
                # Process as a sequence
                table_name = table_name
                data = self.build_ingest_data(table_name,self.server_name, seq_list, None)
                self.load_table_data[table_name]["data"].append(data)
                self.load_table_data[table_name]["source_path"].extend(seq_list)
            else:
                # Treat the single file as a regular file
                seq = seq_list[0]
                data = self.build_ingest_data("UnMatched",self.server_name, seq, None)
                self.load_table_data["UnMatched"]["data"].append(data)
                self.load_table_data["UnMatched"]["source_path"].append(seq)

        return self.load_table_data

    # def separate_the_ingest_files(self, source_path, project_name, server_name):
    #     self.server_name = server_name
    #     self.project_name = project_name
    #     for key, value in self.ingest_data["Table"].items():
    #         self.load_table_data[key] = {
    #             "data": [],
    #             "column_head": value["table_head"],
    #             "source_path": [],
    #         }

    #     # Use a dictionary to store sequences based on base name
    #     sequences = {}

    #     for root, dirs, files in os.walk(source_path):
    #         file_sequence = fileseq.findSequencesOnDisk(root)

    #         for seq in file_sequence:
    #             for key, value in reversed(self.ingest_data["Table"].items()):
    #                 filename = os.path.basename(str(seq))
    #                 regex = re.search(self.ingest_data["Table"][key]["regex"], filename)
    #                 filename_extension = (filename.split(".")[-1]).lower()
    #                 table_name = key

    #                 if len(seq) > 1:
    #                     # Check if it's an image sequence based on naming convention
    #                     if any(
    #                         element in filename.lower()
    #                         for element in self.ingest_data["Table"][table_name][
    #                             "filter"
    #                         ]
    #                         or []
    #                     ) or (
    #                         regex
    #                         and filename_extension == "exr"
    #                         or filename_extension == "mov"
    #                     ):  # Check for sequence
    #                         data = self.build_ingest_data(table_name, seq, regex)
    #                         self.load_table_data[table_name]["data"].append(data)
    #                         self.load_table_data[table_name]["source_path"].append(seq)
    #                         break
    #                 elif (
    #                     filename_extension
    #                     in self.ingest_data["Table"][table_name]["extensions"]
    #                 ):
    #                     data = self.build_ingest_data(table_name, seq, regex)
    #                     self.load_table_data[table_name]["data"].append(data)
    #                     self.load_table_data[table_name]["source_path"].append(seq)
    #                     break
    #             else:
    #                 if (
    #                     filename_extension
    #                     in self.ingest_data["Table"][table_name]["extensions"]
    #                 ):
    #                     data = self.build_ingest_data(table_name, seq, regex)
    #                     self.load_table_data[table_name]["data"].append(data)
    #                     self.load_table_data[table_name]["source_path"].append(seq)
    #                 else:
    #                     data = self.build_ingest_data("UnMatched", seq, None)
    #                     self.load_table_data["UnMatched"]["data"].append(data)
    #                     self.load_table_data["UnMatched"]["source_path"].append(seq)

    #     # Process accumulated sequences
    #     for base_name, seq_list in sequences.items():
    #         # Check if there are multiple files with the same base name
    #         if len(seq_list) > 1:
    #             # Process as a sequence
    #             table_name = table_name
    #             data = self.build_ingest_data(table_name, seq_list, None)
    #             self.load_table_data[table_name]["data"].append(data)
    #             self.load_table_data[table_name]["source_path"].extend(seq_list)
    #         else:
    #             # Treat the single file as a regular file
    #             seq = seq_list[0]
    #             data = self.build_ingest_data("UnMatched", seq, None)
    #             self.load_table_data["UnMatched"]["data"].append(data)
    #             self.load_table_data["UnMatched"]["source_path"].append(seq)

    #     return self.load_table_data

    def build_ingest_data(self, table_name,server ,seq=None, regex=None):
        """
        Load ingest data from a file, extracting sequence and shot information using regular expressions.

        Args:
            table_name (str): The name of the table for which ingest data is being built.
            seq (fileseq.FileSequence): The file sequence from which to extract information.
            regex (bool): Flag indicating whether to use regular expressions for additional data extraction.

        Returns:
            list: A list of values corresponding to the table header for the specified table_name.
        """
        # Function code goes here
        # ...

        if seq:
            # Extract shot and sequence information using regular expressions
            if (os.path.splitext(str(seq))[1][1:]).lower() in self.ingest_data["Table"][
                table_name
            ]["extensions"] or table_name == "UnMatched":
                shot_regex = re.search(r"[\w\s.-]+\d{4}(?=-|_)", seq.basename())
                if shot_regex:
                    shot = shot_regex[0]
                    sequence = re.split(
                        "[_|-|.| |]\d{4}|[_|-|.| |][a-zA-Z]{1,9}\d{4}",
                        seq.basename(),
                    )[0]
                else:
                    shot = ""
                    sequence = ""

                # Build a dictionary with various data fields
                table_dict = {
                    "server": server,
                    "Show": self.project_name,
                    "Enable": None,
                    "Sequence": sequence,
                    "Shot": shot,
                    "Dept": self.department_list,
                    "Type": self.ingest_data["Table"][table_name]["Type"],
                    "Frame Range": "{}-{}".format(
                        str(seq.start()).zfill(4), str(seq.end()).zfill(4)
                    ),
                    "Version": "v###",
                    "Extension": seq.extension()[1:],
                    "Res": self.get_asset_resolution(str(seq)),
                    "Preview": seq.basename() + seq.frameRange() + seq.extension(),
                }

                # Additional data extraction using regex
                if regex:
                    scan_id = re.findall(r"[a-zA-Z]{2}[0-9]{1,4}", seq.basename())
                    if scan_id:
                        letters = re.findall(r"[a-zA-Z]+", scan_id[-1])[0]
                        numbers = str(int(re.findall(r"\d+", scan_id[-1])[0])).zfill(2)
                        table_dict["Scan ID"] = letters + numbers
                    else:
                        table_dict["Scan ID"] = None
                else:
                    table_dict["Scan ID"] = None

                # Set the Preview field using the destination path
                table_dict["Preview"] = self.set_destination_path(
                    table_name, table_dict
                )

                # Extract values based on the table header
                values = [
                    table_dict[head]
                    for head in self.ingest_data["Table"][table_name]["table_head"]
                ]

                return values

    # def build_ingest_data(self, table_name, seq=None, regex=None):
    #     """
    #     A single function to load all the ingest data from a file.
    #     1. get seq and shot name from the file using regular expression.
    #     2. arrange the destination path from the table field values in preview path.
    #     """
    #     if seq:
    #         if (os.path.splitext(str(seq))[1][1:]).lower() in self.ingest_data["Table"][
    #             table_name
    #         ]["extensions"] or table_name == "UnMatched":
    #             shot_regex = re.search(r"[\w\s.-]+\d{4}(?=-|_)", seq.basename())
    #             if shot_regex:
    #                 shot = shot_regex[0]
    #                 sequence = re.split(
    #                     "[_|-|.| |]\d{4}|[_|-|.| |][a-zA-Z]{1,9}\d{4}",
    #                     seq.basename(),
    #                 )[0]

    #             else:
    #                 shot = ""
    #                 sequence = ""

    #             table_dict = {
    #                 "server": self.server_name,
    #                 "Show": self.project_name,
    #                 "Enable": None,
    #                 "Sequence": sequence,
    #                 "Shot": shot,
    #                 "Dept": self.department_list,
    #                 "Type": self.ingest_data["Table"][table_name]["Type"],
    #                 "Frame Range": "{}-{}".format(
    #                     str(seq.start()).zfill(4), str(seq.end()).zfill(4)
    #                 ),
    #                 "Version": "v###",
    #                 "Extension": seq.extension()[1:],
    #                 "Res": self.get_asset_resolution(str(seq)),
    #                 "Preview": seq.basename() + seq.frameRange() + seq.extension(),
    #             }

    #             if regex:
    #                 scan_id = re.findall(r"[a-zA-Z]{2}[0-9]{1,4}", seq.basename())[-1]
    #                 letters = re.findall(r"[a-zA-Z]+", scan_id)[0]
    #                 numbers = str(int(re.findall(r"\d+", scan_id)[0])).zfill(2)
    #                 table_dict["Scan ID"] = letters + numbers
    #                 print ( "----------------------table_dict[Scan ID]",table_dict["Scan ID"])
    #             else:
    #                 table_dict["Scan ID"] = None

    #             table_dict["Preview"] = self.set_destination_path(
    #                 table_name, table_dict
    #             )
    #             values = [
    #                 table_dict[head]
    #                 for head in self.ingest_data["Table"][table_name]["table_head"]
    #             ]

    #             return values

    def set_destination_path(self, table_name, table_dict):
        """
        Load the destination path into the preview field.

        Args:
            table_name (str): The name of the table for which the destination path is being set.
            table_dict (dict): A dictionary containing data for the specified table.

        Returns:
            str: The formatted destination path based on the provided table_dict.
        """
        preview_dict = dict(table_dict)

        for key, value in preview_dict.items():
            if isinstance(value, list):
                preview_dict[key] = value[0]
            elif value == "":
                preview_dict[key] = None

        return self.ingest_data["Table"][table_name]["path"].format(**preview_dict)

    # def set_destination_path(self, table_name, table_dict):
    #     """
    #     load the destination path into preview field.
    #     """
    #     preview_dict = dict(table_dict)

    #     for key, value in preview_dict.items():
    #         if isinstance(value, list):
    #             preview_dict[key] = value[0]
    #         elif value == "":
    #             preview_dict[key] = None

    #     return self.ingest_data["Table"][table_name]["path"].format(**preview_dict)

    def get_asset_resolution(self, path):
        """
        Get the resolution of the file using the OpenCV method.

        Args:
            path (str): The path of the file for which the resolution needs to be determined.

        Returns:
            str: A string representing the resolution in the format "width x height".
        """
        res = "1920x1080"
        mov_file = self.ingest_data["Table"]["Movs"]["extensions"]
        plate_ext = self.ingest_data["Table"]["Plate"]["extensions"]
        annotation_ext = self.ingest_data["Table"]["Annotations"]["extensions"]
        img_seq = [*plate_ext, *annotation_ext]
        base_path = os.path.dirname(path)

        for file in os.listdir(base_path):
            img_file = os.path.join(base_path, file)
            exten = (os.path.splitext(img_file)[-1][1:]).lower()

            if exten:
                if exten in img_seq:
                    break

        if exten in mov_file:
            vid = cv2.VideoCapture(img_file)
            hgt = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
            wid = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
            res = f"{int(wid)}x{int(hgt)}"
        elif exten in img_seq:
            if exten == "dpx":
                try:
                    with open(img_file, "rb") as file:
                        # Read the magic number from the file header to determine endianness
                        magic_number = struct.unpack("I", file.read(4))[0]
                        # Set the endianness for reading the values
                        endianness = ">" if magic_number == 1481655379 else "<"
                        # Seek to x/y offset in the header (1424 bytes for x, 1428 bytes for y)
                        file.seek(1424, 0)
                        # Read x and y resolutions (4 bytes each) based on endianness
                        width = struct.unpack(endianness + "I", file.read(4))[0]
                        height = struct.unpack(endianness + "I", file.read(4))[0]
                        res = f"{width}x{height}"
                except FileNotFoundError as e:
                    print(f"Error: File not found - {e} for file: {img_file}")
                except PermissionError as e:
                    print(f"Error: Permission issue - {e} for file: {img_file}")
                except struct.error as e:
                    print(f"Error: Struct error - {e} for file: {img_file}")
                except Exception as e:
                    print(
                        f"An unexpected error occurred in 'dpx' condition: {e} for file: {img_file}"
                    )
            else:
                try:
                    img = cv2.imread(img_file)
                    height, width, channels = img.shape
                    res = f"{width}x{height}"
                except cv2.error as e:
                    print(f"OpenCV error occurred: {e} for image file: {img_file}")
                except AttributeError as e:
                    print(f"Attribute error occurred: {e} for file: {img_file}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e} for file: {img_file}")

        return res

    # def get_asset_resolution(self, path):
    #     """
    #     get resolution of the file using opencv method.
    #     """
    #     res = "1920x1080"
    #     mov_file = self.ingest_data["Table"]["Movs"]["extensions"]
    #     plate_ext = self.ingest_data["Table"]["Plate"]["extensions"]
    #     annotation_ext = self.ingest_data["Table"]["Annotations"]["extensions"]
    #     img_seq = [*plate_ext, *annotation_ext]
    #     base_path = os.path.dirname(path)
    #     for file in os.listdir(base_path):
    #         img_file = os.path.join(base_path, file)
    #         exten = (os.path.splitext(img_file)[-1][1:]).lower()
    #         if exten:
    #             if exten in img_seq:
    #                 break
    #     if exten in mov_file:
    #         vid = cv2.VideoCapture(img_file)
    #         hgt = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
    #         wid = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
    #         res = str(int(wid)) + "x" + str(int(hgt))
    #     elif exten in img_seq:
    #         if exten == "dpx":
    #             try:
    #                 with open(img_file, "rb") as file:
    #                     # Read the magic number from the file header to determine endianness
    #                     magic_number = struct.unpack("I", file.read(4))[0]
    #                     # Set the endianness for reading the values
    #                     endianness = ">" if magic_number == 1481655379 else "<"
    #                     # Seek to x/y offset in the header (1424 bytes for x, 1428 bytes for y)
    #                     file.seek(1424, 0)
    #                     # Read x and y resolutions (4 bytes each) based on endianness
    #                     width = struct.unpack(endianness + "I", file.read(4))[0]
    #                     height = struct.unpack(endianness + "I", file.read(4))[0]
    #                     res = f"{width}x{height}"
    #             except FileNotFoundError as e:
    #                 print(f"Error: File not found - {e} for file: {img_file}")
    #             except PermissionError as e:
    #                 print(f"Error: Permission issue - {e} for file: {img_file}")
    #             except struct.error as e:
    #                 print(f"Error: Struct error - {e} for file: {img_file}")
    #             except Exception as e:
    #                 print(
    #                     f"An unexpected error occurred in 'dpx' condition: {e} for file: {img_file}"
    #                 )
    #         else:
    #             try:
    #                 img = cv2.imread(img_file)
    #                 height, width, channels = img.shape
    #                 res = f"{width}x{height}"
    #             except cv2.error as e:
    #                 print(f"OpenCV error occurred: {e} for image file: {img_file}")
    #             except AttributeError as e:
    #                 print(f"Attribute error occurred: {e} for file: {img_file}")
    #             except Exception as e:
    #                 print(f"An unexpected error occurred: {e} for file: {img_file}")

    #     return res


def get_shotgrid_department_name():
    """
    Retrieves and returns a sorted list of Shotgrid department names.

    This function queries Shotgrid to obtain department details, filters out
    departments with underscores in their names, and returns the sorted list
    of department names.

    Returns:
        list: A sorted list of Shotgrid department names without underscores.
    """
    # Consider changing the name of 'read' to a more descriptive name if possible
    shotgrid_reader = read  # Replace 'read' with the actual module/class you are using
    departments = shotgrid_reader._get_details("Department", [], ["name"])
    filtered_departments = [
        dept["name"] for dept in departments if "_" not in dept["name"]
    ]
    sorted_departments = sorted(filtered_departments, key=len)
    return sorted_departments


# def get_shotgrid_department_name():
#     departments = read._get_details("Department", [], ["name"])
#     filtered_departments = [
#         dept["name"] for dept in departments if "_" not in dept["name"]
#     ]
#     sorted_departments = sorted(filtered_departments, key=lambda dept: len(dept))
#     return sorted_departments

