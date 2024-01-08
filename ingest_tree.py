import os

from PySide2 import QtWidgets
from PySide2 import QtGui

from utils.config import ConfigTableView

yaml_data = ConfigTableView().load_yaml_data()


class IngestTreeView(QtWidgets.QTreeView):
    def __init__(self, app, parent=None):
        super(IngestTreeView, self).__init__()
        self.app = app
        self.setObjectName("IngestTreeView")
        self.setContextMenuPolicy(QtGui.Qt.CustomContextMenu)
        self.setColumnWidth(0, 175)
        image_path = os.path.dirname(__file__)
        self.setStyleSheet(
            """
            QTreeView{{
            background-color: rgb(30, 31, 34);
            color: rgb(217, 219, 223);
            }}
            QHeaderView::section{{
            background-color: rgb(59, 62, 66);
            color:white;
            }}
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {{
                    border-image: none;
                    image: url({});
                    color: white;
                background-position: center;
            }}
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings  {{
                    border-image: none;
                    image: url({});
                    color: white;
                background-position: center;
            }}
            """.format(
                os.path.join(image_path, "images", "icons", "close.png"),
                os.path.join(image_path, "images", "icons", "open.png"),
            )
        )
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def set_context_data(self, source_path):
        file_model = QtWidgets.QFileSystemModel()
        file_model.setRootPath(source_path)
        self.setModel(file_model)
        self.setRootIndex(file_model.index(source_path))
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)

