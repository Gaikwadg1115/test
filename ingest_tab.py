from PySide2 import QtWidgets

from utils.config import ConfigTableView
from ingest_table import IngestTableView

yaml_data = ConfigTableView().load_yaml_data()


class IngestTabView(QtWidgets.QTabWidget):
    def __init__(self, app):
        super(IngestTabView, self).__init__()
        self.setStyleSheet(
            """
            QTabBar::tab {
                border: 1px solid black;
                padding: 10px;
                color: rgb(255, 255, 255);
                background-color: rgb(59, 62, 66);
                border-radius: 5px;
                width: 150px;
                font-size: 12px;
                font-family: 'Arial';
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: rgb(30, 31, 34);
                margin-bottom: -1px;
            }
            QTabWidget::pane {
                border-width: 3px;
                border-style: solid;
                border-color: rgb(59, 62, 66);
                border-radius: 7px;
            }
        """
        )
        self.app = app
        self.add_tab_button = QtWidgets.QPushButton("+")
        self.add_tab_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
                padding: 0px 10px;
            }
        """
        )
        self.setCornerWidget(self.add_tab_button)

    def add_tab_menu_item_clicked(self, action):
        table_name = action.text()
        headers = yaml_data["Table"][table_name]["table_head"]
        table_object = IngestTableView(
            table_head=table_name, data=None, headers=headers, app=self.app
        )
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(table_object)
        tab = QtWidgets.QWidget()
        tab.setLayout(layout)
        self.addTab(tab, table_name)
        self.menu.removeAction(action)

    def create_tab_and_table(self, ingest_data=None):
        """
        create tab if the table data is present otherwise it will be added in + menu bar.
        """
        if ingest_data:
            self.file_screen_source_path = ingest_data
            self.clear()
            self.menu = QtWidgets.QMenu(self)
            self.menu.triggered.connect(self.add_tab_menu_item_clicked)
            for key, value in ingest_data.items():
                if value["data"]:
                    table_object = IngestTableView(
                        table_head=key,
                        data=value["data"],
                        headers=value["column_head"],
                        app=self.app,
                    )
      
                    layout = QtWidgets.QVBoxLayout()
                    layout.addWidget(table_object)
                    tab = QtWidgets.QWidget()
                    tab.setLayout(layout)
                    self.addTab(tab, key)
                else:
                    action = QtWidgets.QAction(key, self)
                    self.menu.addAction(action)
                    self.add_tab_button.setMenu(self.menu)

