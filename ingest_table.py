import os
import re

import fileseq

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore

from utils.config import ConfigTableView
from file_screen import ingest_file_screening
from file_screen import ingest_file_screening

yaml_data = ConfigTableView().load_yaml_data()
file_screen = ingest_file_screening(yaml_data)


class IngestTableView(QtWidgets.QTableWidget):
    def __init__(self, table_head, data, headers, app, parent=None):
        super(IngestTableView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().installEventFilter(self)
        self.setObjectName(table_head)
        self.horizontalHeader().sectionClicked.connect(self.enable_disable_checkbox)
        self.setColumnCount(len(headers))
        if data:
            self.setRowCount(len(data))
            self.create_table_data(data)
        self.setHorizontalHeaderLabels(headers)
        self.resizeColumnsToContents()
        self.cut_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence.Cut, self)
        self.paste_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence.Paste, self)
        self.connect_table_ui()
        self.app = app
        self.clipboard = self.app.clipboard()
        self.get_server_name()
        self.setStyleSheet("QTableWidget::item { border: 1px solid grey; }")

    def get_server_name(self):
        widgets = self.app.allWidgets()
        for widget in widgets:
            if isinstance(widget, QtWidgets.QComboBox):
                if widget.objectName()=="server_select":
                    self.server_name= widget.currentText()

    def create_table_data(self, data):
        """
        Populates the QTableWidget with data.
        Args:
            data (list): A 2D list of data to populate the table with.
        1. creating checkbox in 0 column index.
        2. if data in list datatype then creating combobox widget item.
        3. other than everything will be text item.
        """
        for row_index, row in enumerate(data):
            for column_index, column_data in enumerate(row):
                if column_index == 0:
                    chkBoxItem = QtWidgets.QTableWidgetItem()
                    chkBoxItem.setCheckState(QtGui.Qt.Checked)
                    self.setItem(row_index, column_index, chkBoxItem)
                    continue
                if isinstance(column_data, list):
                    self.combo_box = QtWidgets.QComboBox()
                    self.combo_box.currentIndexChanged.connect(self.handleItemChanged)
                    self.combo_box.addItems(column_data)
                    self.setCellWidget(row_index, column_index, self.combo_box)
                else:
                    item = QtWidgets.QTableWidgetItem(str(column_data))
                    self.setItem(row_index, column_index, item)

    def connect_table_ui(self):
        self.cut_shortcut.activated.connect(self.cut)
        self.paste_shortcut.activated.connect(self.paste)
        self.itemChanged.connect(self.handleItemChanged)

    def handleItemChanged(self, item):
        """
        every changes in table cell item will be noted and trigger to this function .
        1. First it checks the item type so that we can get item text value according to cellwidget(combobox) or text(plain text).
        2. get the current row item changed and change the preview column with the update field.
        """
        row_index = None
        if isinstance(item, int):
            sender_combo_box = self.sender()
            parent_widget = sender_combo_box.parent()
            if parent_widget is not None:
                index = self.indexAt(sender_combo_box.pos())
                row_index = index.row()
                column_index = index.column()
                combo_box = self.cellWidget(row_index, column_index)
                combo_box.setStyleSheet("QComboBox { border: 3px solid orange; }")
        else:
            row_index = item.row()
            if item.column() != 0:
                item.setData(QtCore.Qt.UserRole, QtGui.QColor("orange"))

        if row_index is not None and row_index >= 0:
            path_dict = dict()
            self.server_name=None
            self.project_name = None
            self.source_path = None
            widgets = self.app.allWidgets()
            for widget in widgets:
                if isinstance(widget, QtWidgets.QComboBox):
                    if widget.objectName()=="server_select":
                        self.server_name= widget.currentText()
                    if widget.objectName() == "show_comboBox":
                        self.project_name = widget.currentText().upper()
                if isinstance(widget, QtWidgets.QLineEdit):
                    if widget.objectName() == "ingest_source_path_line_edit":
                        self.source_path = widget.text()

            for column_index in range(self.columnCount()):
                item = self.item(row_index, column_index)
                header = self.horizontalHeaderItem(column_index)

                if item is not None:
                    path_dict[header.text()] = item.text() or "None"
                else:
                    combo_box = self.cellWidget(row_index, column_index)
                    path_dict[header.text()] = combo_box.currentText()

            path_dict["server"]=self.server_name
            path_dict["Show"] = self.project_name
            pattern = r"\d{4}x\d{4}"
            match = re.search(pattern, path_dict["Preview"])
            path_dict["Extension"] = os.path.splitext(path_dict["Preview"])[-1]
            path_dict["Res"] = None
            if match:
                path_dict["Res"] = match.group()

            path_dict["Preview"] = os.path.basename(path_dict["Preview"])
            if "Shot" in path_dict:
                shot = path_dict["Shot"]
                if shot == "common":
                    file_path = yaml_data["Table"][self.objectName()][
                        "common_path"
                    ].format(**path_dict)
                elif not shot.isalpha():
                    file_path = yaml_data["Table"][self.objectName()]["path"].format(
                        **path_dict
                    )
            else:
                file_path = yaml_data["Table"][self.objectName()]["path"].format(
                    **path_dict
                )
            print("file_path",file_path)
            item.setText(file_path)

    def cut(self):
        """
        This function is used to cut the selected row in the table and append the preview text in the clipboard .
        """
        column_count = self.columnCount()
        move_data_list = []
        remove_index = []
        for row_index in range(self.rowCount()):
            item = self.item(row_index, 0)
            if item.checkState() == QtCore.Qt.Checked:
                item_data = self.item(row_index, column_count - 1).text()
                move_data_list.append(item_data)
                remove_index.append(row_index)
        remove_index.sort()
        [self.removeRow(index) for index in reversed(remove_index)]
        self.clipboard.setText("\n".join(move_data_list))

    def paste(self):
        """
        This paste function is used to perform to actions
        1. generally paste the copyboard value in the selected items in a table .
        2. create a new row in the focused table , where we cut a row from a table in cut method .
        """
        data = self.clipboard.text()
        if self.selectedIndexes():
            for index in self.selectedIndexes():
                self.setItem(
                    index.row(), index.column(), QtWidgets.QTableWidgetItem(data)
                )
            self.clearSelection()

        elif data:
            self.itemChanged.disconnect(self.handleItemChanged)
            for file_path in data.split("\n"):
                table_name = self.objectName()
                file_name = os.path.basename(file_path)
                regex = yaml_data["Table"][table_name]["regex"]

                self.source_path = None
                widgets = self.app.allWidgets()
                for widget in widgets:
                    if isinstance(widget, QtWidgets.QLineEdit):
                        if widget.objectName() == "ingest_source_path_line_edit":
                            self.source_path = widget.text()

                for root, dirs, files in os.walk(self.source_path):
                    file_sequence = fileseq.findSequencesOnDisk(root)
                    for seq in file_sequence:
                        seq_file_name = (
                            seq.basename() + seq.frameRange() + seq.extension()
                        )
                        if seq_file_name == file_name:
                            file_path = seq
                regex = None if regex == "None" else regex
                data = file_screen.build_ingest_data(table_name,self.server_name,file_path, regex)
                if data:
                    row_index = self.rowCount()
                    self.insertRow(row_index)
                    for column_index, column_data in enumerate(data):
                        if column_index == 0:
                            chkBoxItem = QtWidgets.QTableWidgetItem()
                            chkBoxItem.setCheckState(QtGui.Qt.Checked)
                            self.setItem(row_index, column_index, chkBoxItem)
                            continue
                        if isinstance(column_data, list):
                            self.combo_box = QtWidgets.QComboBox()
                            self.combo_box.currentIndexChanged.connect(
                                self.handleItemChanged
                            )
                            self.combo_box.addItems(column_data)
                            self.setCellWidget(row_index, column_index, self.combo_box)
                        else:
                            item = QtWidgets.QTableWidgetItem(str(column_data))
                            self.setItem(row_index, column_index, item)

            self.itemChanged.connect(self.handleItemChanged)

    def enable_disable_checkbox(self, val):
        if val == 0:
            check = list()
            for i in range(self.rowCount()):
                check.append(bool(self.item(i, 0).checkState()))

            if all(check):
                for i in range(self.rowCount()):
                    self.item(i, 0).setCheckState(QtGui.Qt.Unchecked)
            else:
                for i in range(self.rowCount()):
                    self.item(i, 0).setCheckState(QtGui.Qt.Checked)
            self.clearSelection()

    def paintEvent(self, event):
        """
        PaintEvent is a customizable build in function to draw or color the widget.
        In this function its used to create a colored border for cell widget.
        """
        super().paintEvent(event)
        painter = QtGui.QPainter(self.viewport())
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item and item.data(QtCore.Qt.UserRole) is not None:
                    rect = self.visualRect(self.indexFromItem(item))
                    pen = QtGui.QPen(item.data(QtCore.Qt.UserRole), 3)
                    painter.setPen(pen)
                    painter.drawRect(rect)

