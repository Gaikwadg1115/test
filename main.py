import os
import re
import sys
import time  # Added import

from PySide2 import QtWidgets, QtGui, QtCore
import ui.ingest_ui as _ui
import fileseq

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

# Import your other modules as needed
# from jobsetup import __shots as shots
from jobsetup import new_shots as shots
from sg_utils import create, read
from utils.config import ConfigTableView
from ingest_tab import IngestTabView
from ingest_tree import IngestTreeView
from file_screen import ingest_file_screening
from utils.logger import get_logger
from file_utils.file_op import copy_file_seq, copy_file
from deadline_integrate import deadline_ingest

yaml_data = ConfigTableView().load_yaml_data()


class IngestApp(_ui.Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self):
        """
        Initialize the IngestApp.

        This constructor sets up the IngestApp, initializes UI components, and connects UI elements.

        - Sets up the user interface using 'setupUi'.
        - Creates an 'IngestTreeView' and 'IngestTabView' instance.
        - Initializes file screening with the provided YAML data.
        - Sets 'project_name' to None initially.
        - Retrieves the initial value for 'server_name' from the 'server_comboBox'.
        - Calls 'InitializeUI' to perform additional UI setup.
        - Connects UI elements using 'connect_ui'.

        Example:
        ```python
        my_app = IngestApp()
        my_app.show()
        ```
        """
        super(IngestApp, self).__init__()
        self.setupUi(self)
        self.IngestTreeView = IngestTreeView(app)
        self.IngestTabView = IngestTabView(app)
        self.file_screen = ingest_file_screening(yaml_data)
        self.project_name = None
        self.server_name = self.server_comboBox.currentText()
        self.InitializeUI()
        self.connect_ui()

    def connect_ui(self):
        """
        Connect UI elements to their corresponding functions.

        This method connects various buttons in the UI to their respective functions.

        - The 'Browse' button is connected to the 'PopUpFileDialog' function.
        - The 'Cancel' button is connected to the 'ClearAllTableData' function.
        - The 'Validate' button is connected to the 'ValidateTableData' function.
        - The 'Publish' button is connected to the 'PublishIngestFiles' function.

        Note:
        Ensure that the 'ingest_browse_button' is initially disabled.

        Example:
        ```python
        my_object = MyClass()
        my_object.connect_ui()
        ```
        """
        self.ingest_browse_button.setEnabled(False)
        self.ingest_browse_button.clicked.connect(self.PopUpFileDialog)
        self.ingest_cancel_button.clicked.connect(self.ClearAllTableData)
        self.ingest_validate_button.clicked.connect(self.ValidateTableData)
        self.ingest_publish_button.clicked.connect(self.PublishIngestFiles)

    def PopUpFileDialog(self):
        """
        Open a file dialog to browse and select ingest files, screen them using the file screening process,
        and display the ingested data in the table view setup.

        This function performs the following steps:
        1. Opens a file dialog to select a folder.
        2. Sets the source path based on the selected folder.
        3. Updates the UI to reflect the selected source path.
        4. Sets the context data for the 'IngestTreeView'.
        5. Screens the ingest files using the file screening process.
        6. Creates tabs and tables in the 'IngestTabView' based on the screened ingest data.
        """
        file_dialog = QtWidgets.QFileDialog(self)
        source_url = file_dialog.getExistingDirectoryUrl(
            parent=self,
            caption="Open a folder",
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        self.source_path = source_url.toLocalFile()
        if self.source_path:
            self.ingest_source_path_line_edit.setText(self.source_path)
            self.IngestTreeView.set_context_data(self.source_path)
            self.ingest_data = self.file_screen.separate_the_ingest_files(
                self.source_path, self.project_name, self.server_name
            )

            self.IngestTabView.create_tab_and_table(self.ingest_data)

    def InitializeUI(self):
        """
        Initialize the user interface for the IngestApp.

        This method performs the following UI initialization steps:

        1. Sets up a horizontal QSplitter to display the 'IngestTreeView' and 'IngestTabView' side by side.
        2. Configures and adds the QSplitter to the 'ingest_context_layout'.
        3. Configures the 'show_comboBox':
        - Makes it editable.
        - Populates the dropdown with project names retrieved from 'read.Projects().projects'.
        - Connects the 'currentTextChanged' signal to the 'validate_show_comboBox' method.

        4. Configures the 'server_comboBox':
        - Makes it editable.
        - Populates the dropdown with server names.
        - Connects the 'currentTextChanged' signal to the 'validate_server_comboBox' method.

        5. Sets the window title to "Ingest Package Tool".
        """
        ingest_view_splitter = QtWidgets.QSplitter(QtGui.Qt.Horizontal)
        ingest_view_splitter.addWidget(self.IngestTreeView)
        ingest_view_splitter.addWidget(self.IngestTabView)
        ingest_view_splitter.setSizes([100, 500])
        self.ingest_context_layout.addWidget(ingest_view_splitter)

        # Configure show_comboBox
        self.show_comboBox.setEditable(True)
        self.show_list = [project["name"] for project in read.Projects().projects]
        self.show_list.insert(0, "")
        self.show_comboBox.addItems(self.show_list)
        self.show_comboBox.currentTextChanged.connect(self.validate_show_comboBox)

        # Configure server_comboBox
        self.server_comboBox.setEditable(True)
        server = self.server_list = ["brahmos", "bolt","live"]
        self.server_list.insert(0, "")
        self.server_comboBox.addItems(self.server_list)
        self.server_comboBox.currentTextChanged.connect(self.validate_server_comboBox)

        # Set window title
        self.setWindowTitle("Ingest Package Tool")

    def validate_show_comboBox(self, index):
        """
        Validate the selected item in the 'show_comboBox'.

        This method checks if the selected project name is valid. If valid:
        - Enables the 'ingest_browse_button'.
        - Sets the 'project_name' attribute to the uppercase version of the selected project name.
        - Updates the style of 'show_comboBox' with a green border.
        If not valid:
        - Disables the 'ingest_browse_button'.
        - Updates the style of 'show_comboBox' with a red border.

        Args:
        - index (int): The index of the currently selected item in the 'show_comboBox'.
        """
        project_name = self.show_comboBox.currentText()

        if project_name and project_name in self.show_list:
            # Valid project name
            self.ingest_browse_button.setEnabled(True)
            self.project_name = project_name.upper()
            self.show_comboBox.setStyleSheet("QComboBox { border: 3px solid green; }")
        else:
            # Invalid or empty project name
            self.ingest_browse_button.setEnabled(False)
            self.show_comboBox.setStyleSheet("QComboBox { border: 3px solid red; }")

    def validate_server_comboBox(self, index):
        """
        Validate the selected item in the 'server_comboBox'.

        This method checks if the selected server name is valid. If valid:
        - Enables the 'ingest_browse_button'.
        - Sets the 'server_name' attribute to the selected server name.
        - Updates the style of 'server_comboBox' with a green border.
        If not valid:
        - Disables the 'ingest_browse_button'.
        - Updates the style of 'server_comboBox' with a red border.

        Args:
        - index (int): The index of the currently selected item in the 'server_comboBox'.
        """
        server_name = self.server_comboBox.currentText()

        if server_name and server_name in self.server_list:
            # Valid server name
            self.ingest_browse_button.setEnabled(True)
            self.server_name = server_name
            self.server_comboBox.setStyleSheet("QComboBox { border: 3px solid green; }")
        else:
            # Invalid or empty server name
            self.ingest_browse_button.setEnabled(False)
            self.server_comboBox.setStyleSheet("QComboBox { border: 3px solid red; }")

    def ClearAllTableData(self):
        """
        Clear all data in QTableViews within the application.

        This method iterates over all widgets in the application. If a widget is a QTableView:
        - Sets the row count to 0.
        - Sets the column count to 0.

        Additionally, it resets the data in the 'IngestTreeView'.
        """
        widgets = app.allWidgets()
        for widget in widgets:
            if isinstance(widget, QtWidgets.QTableView):
                widget.setRowCount(0)
                widget.setColumnCount(0)

        self.IngestTreeView.reset()

    def ValidateTableData(self):
        """
        Validate show/project name.
        Validate table cell data; if missing, indicate an error in a dialogue box and mark the cell border as red.
        After validating table cell values, check the preview path in Shotgun published data,
        retrieve the latest version, and fill it in the version column.

        - Checks if a project and server are selected. Displays a warning if not.
        - Creates a validation progress dialog to show progress during validation.
        - Iterates over QTableViews in the application.
        - For each table, iterates over rows and columns to validate data and fill the version column.
        - Updates the UI and triggers validation progress.

        Returns:
        - validate_dict (dict): A dictionary containing information about missing data in table cells.
        """
        project_name = self.show_comboBox.currentText()
        server_name = self.server_comboBox.currentText()
        if not project_name:
            self.DialogBox("Warning", "Please select a project")
            return

        if not server_name:
            self.DialogBox("Warning", "Please select the server")
            return

        validate_dict = {}
        published_files = read.PublishedFiles(
            prj_name=self.project_name
        ).published_files
        widgets = app.allWidgets()

        # Create a validation progress dialog
        progress_dialog = QtWidgets.QProgressDialog(self)
        progress_dialog.setWindowTitle("Validation Progress")
        progress_dialog.setLabelText("Validating Table Data...")
        progress_dialog.setModal(True)
        progress_dialog.setAutoClose(True)
        progress_dialog.setAutoReset(True)
        progress_dialog.setMinimumDuration(0)

        # Set the maximum value based on your task
        progress_dialog.setMaximum(len(widgets))
        progress_dialog.setValue(0)

        for idx, widget in enumerate(widgets):
            if isinstance(widget, QtWidgets.QTableView):
                table_name = widget.objectName()
                for row_index in range(widget.rowCount()):
                    row_data = []
                    item = widget.item(row_index, 0)
                    if item.checkState():
                        path_dict = dict()
                        flag = True
                        version_index = widget.columnCount() - 2
                        for column_index in range(1, widget.columnCount()):
                            item = widget.item(row_index, column_index)
                            header = widget.horizontalHeaderItem(column_index)
                            path_dict["server"] = self.server_comboBox.currentText()
                            path_dict["Show"] = self.show_comboBox.currentText().upper()

                            if item is not None:
                                if item.text() == "":
                                    widget.itemChanged.disconnect(
                                        widget.handleItemChanged
                                    )
                                    if table_name in validate_dict:
                                        validate_dict[table_name].append(
                                            "Row {} {} column".format(
                                                row_index + 1, header.text()
                                            )
                                        )

                                    else:
                                        validate_dict[table_name] = [
                                            "Row {} {} column".format(
                                                row_index + 1,
                                                header.text(),
                                            )
                                        ]

                                    item.setData(
                                        QtCore.Qt.UserRole, QtGui.QColor("red")
                                        
                                    )
                                    print('project name and sequence not present')

                                    flag = False
                                    widget.itemChanged.connect(widget.handleItemChanged)
                                    continue
                                row_data.append(item.text())
                                path_dict[header.text()] = item.text()

                            else:
                                combo_box = widget.cellWidget(row_index, column_index)
                                row_data.append(combo_box.currentText())
                                path_dict[header.text()] = combo_box.currentText()

                        if flag:
                            path_dict["Extension"] = os.path.splitext(
                                path_dict["Preview"]
                            )[-1]

                            file_path = (
                                yaml_data["Table"][table_name]["path"]
                                .split("{Version}")[0]
                                .format(**path_dict)
                            )

                            pattern = r"[\\/]v(\d+)"
                            filtered_list = [
                                int(match.group(1))
                                for match in (
                                    re.search(pattern, d["sg_filepath"])
                                    for d in published_files
                                    if d["sg_filepath"]
                                    and file_path in d["sg_filepath"]
                                )
                                if match
                            ] or [0]

                            version = "v" + str(max(filtered_list) + 1).zfill(3)
                            widget.setItem(
                                row_index,
                                version_index,
                                QtWidgets.QTableWidgetItem(version),
                            )
                progress_dialog.setValue(idx + 1)
                QtWidgets.QApplication.processEvents()

                # Simulating work for the current table (remove this in your actual code)
                # time.sleep(1)
        progress_dialog.close()

        if validate_dict:
            self.DialogBox(
                "Warning",
                "Please fill the below data's \n"
                + self.format_missing_data(validate_dict),
            )
            return validate_dict

    def format_missing_data(self, input_dict):
        """
        Format missing data in a dictionary for display in a warning message.

        Args:
        - input_dict (dict): A dictionary containing information about missing data.

        Returns:
        - str: Formatted string representing missing data.
        """
        data = ""
        for key, value in input_dict.items():
            data += f"\n{key}:\n"
            if isinstance(value, list):
                data += "\n".join([f"    - {elem}" for elem in value])
            else:
                data += f"    {value}"
        data += "\n"
        return data

    def PublishIngestFiles(self):
        """
        Generate a log for published files.
        Validate the published file once again and publish the files in Shotgun as well as copy to the file server.

        - Retrieves project details and initializes lists for published and unpublished files.
        - Creates a progress dialog to show progress during the publish process.
        - Iterates over QTableViews in the application.
        - For each table, iterates over rows and columns to validate data and publish files.
        - Updates the UI and triggers publish progress.
        - Logs information about published and unpublished files.
        - Displays a success message in a dialog box.
        """
        logger = get_logger(self.project_name, self.server_name)
        project_id = read._get_details_one(
            "Project", [["name", "is", self.show_comboBox.currentText()]], ["id"]
        )["id"]
        widgets = app.allWidgets()
        PublishedFiles = []
        UnPublishedFiles = []

        # Create a publish progress dialog
        progress_dialog = QtWidgets.QProgressDialog(self)
        progress_dialog.setWindowTitle("Publish Progress")
        progress_dialog.setLabelText("Publish Table Data...")
        progress_dialog.setModal(True)
        progress_dialog.setAutoClose(True)
        progress_dialog.setAutoReset(True)
        progress_dialog.setMinimumDuration(0)

        # Set the maximum value based on your task
        progress_dialog.setMaximum(len(widgets))
        progress_dialog.setValue(0)

        for idx, widget in enumerate(widgets):
            if isinstance(widget, QtWidgets.QTableView):
                for row_index in range(widget.rowCount()):
                    item = widget.item(row_index, 0)
                    if item.checkState():
                        flag = True
                        make_shot_name = None
                        make_sequence_name = None
                        for column_index in range(1, widget.columnCount()):
                            item = widget.item(row_index, column_index)
                            header = widget.horizontalHeaderItem(column_index)
                            if item is not None:
                                if header.text() == "Shot":
                                    make_shot_name = item.text()
                                if header.text() == "Sequence":
                                    make_sequence_name = item.text()
                                if item.text() == "" or "None" in item.text():
                                    flag = False
                                    break

                        if flag:
                            widget.itemChanged.disconnect(widget.handleItemChanged)

                            file_path = widget.item(row_index, column_index).text()
                            file_name = os.path.basename(file_path)
                            dst_path = os.path.dirname(file_path)

                            for root, dirs, files in os.walk(self.source_path):
                                file_sequence = fileseq.findSequencesOnDisk(root)
                                for seq in file_sequence:
                                    seq_file_name = (
                                        seq.basename()
                                        + seq.frameRange()
                                        + seq.extension()
                                    )
                                    published = None
                                    if seq_file_name == file_name:
                                        src_path = seq

                                        publish_data = {
                                            "project": {
                                                "type": "Project",
                                                "id": project_id,
                                            },
                                            "code": str(file_name),
                                            "sg_filepath": str(file_path),
                                            "sg_source_path": str(src_path),
                                        }
                                        if (
                                            
                                            self.project_name
                                            and self.server_name
                                            and make_sequence_name
                                            and make_shot_name
                                        ):
                                            shots.create(
                                                self.server_name,
                                                self.project_name,
                                                make_sequence_name,
                                                make_shot_name,
                                                None,
                                                None,
                                            )

                                        if len(seq) > 1:
                                            try:
                                                copy_file_seq(src_path, dst_path)
                                                published = create._create_entry(
                                                    "PublishedFile", publish_data
                                                )
                                                deadline_ingest(publish_data,self.server_name)
                                                item.setData(
                                                    QtCore.Qt.UserRole,
                                                    QtGui.QColor("green"),
                                                )
                                            except FileExistsError:
                                                print(
                                                    "File Already exists and cannot be replaced {}".format(
                                                        file_path
                                                    )
                                                )
                                                item.setData(
                                                    QtCore.Qt.UserRole,
                                                    QtGui.QColor("red"),
                                                )
                                            except Exception as e:
                                                print(e)
                                                item.setData(
                                                    QtCore.Qt.UserRole,
                                                    QtGui.QColor("red"),
                                                )
                                        else:
                                            try:
                                                copy_file(
                                                    os.path.join(
                                                        os.path.dirname(str(src_path)),
                                                        seq.basename()
                                                        + seq.frameRange()
                                                        + seq.extension(),
                                                    ),
                                                    dst_path,
                                                )
                                                published = create._create_entry(
                                                    "PublishedFile", publish_data
                                                )
                                                # src_for_deadline = publish_data['sg_filepath']
                                                # print ("***************src_for_deadline",src_for_deadline)
                                                
                                                deadline_ingest(publish_data,self.server_name)
                                                item.setData(
                                                    QtCore.Qt.UserRole,
                                                    QtGui.QColor("green"),
                                                )
                                            
                                            except FileExistsError:
                                                print(
                                                    "File Already exists and cannot be replaced {}".format(
                                                        dst_path
                                                    )
                                                )
                                                item.setData(
                                                    QtCore.Qt.UserRole,
                                                    QtGui.QColor("red"),
                                                )
                                            except Exception as e:
                                                print(e)
                                                item.setData(
                                                    QtCore.Qt.UserRole,
                                                    QtGui.QColor("red"),
                                                )

                                        if published:
                                            PublishedFiles.append(str(file_path) + "\n")
                                        else:
                                            UnPublishedFiles.append(
                                                str(file_path) + "\n"
                                            )

                            widget.itemChanged.connect(widget.handleItemChanged)

                        else:
                            widget.itemChanged.disconnect(widget.handleItemChanged)
                            item.setData(QtCore.Qt.UserRole, QtGui.QColor("red"))
                            widget.itemChanged.connect(widget.handleItemChanged)
                progress_dialog.setValue(idx + 1)
                QtWidgets.QApplication.processEvents()

                # Simulating work for the current table (remove this in your actual code)
                # time.sleep(1)

        # Close progress dialog
        progress_dialog.close()

        # Log information about published and unpublished files
        logger.info(
            "Published Files :\n" + ("\n".join(PublishedFiles) or "No published files")
        )
        if UnPublishedFiles:
            logger.info("Unpublished Files :\n" + "\n".join(UnPublishedFiles))

        # Display a success message in a dialog box
        self.DialogBox("Success", "Ingestion Completed")

    def DialogBox(self, window_title, message):
        """
        Display a simple message dialog box.

        Args:
        - window_title (str): The title of the dialog box.
        - message (str): The message to be displayed in the dialog box.
        """
        dialog_object = QtWidgets.QMessageBox(self)
        dialog_object.setWindowTitle(window_title)
        dialog_object.setText(message)
        dialog_object.exec_()

    def split_details_for_deadline(publish_details):
        src_for_deadline = publish_details['sg_filepath']
        # Printing the values)
        print(f"SG Filepath: {src_for_deadline}")
        return src_for_deadline



if __name__ == "__main__":
    app = QtWidgets.QApplication()
    ingest_app = IngestApp()
    ingest_app.show()
    sys.exit(app.exec_())

