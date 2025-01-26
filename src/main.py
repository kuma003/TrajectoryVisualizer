"""
    main.py - Entry point for the application.
"""

import time
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLViewWidget
import requests
from pyqtgraph.Qt import QtCore, QtGui
from PyQt6.QtCore import pyqtSignal, QThread
from geography import calc_distance, get_tile_urls, get_px_in_meter
from settings import *

from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QLabel,
    QComboBox,
    QProgressDialog,
)


@dataclass
class MapData:
    X: np.ndarray
    Y: np.ndarray
    Z: np.ndarray
    color: np.ndarray


class MapDataThread(QThread):
    signal_progress: pyqtSignal = pyqtSignal(int)
    signal_message: pyqtSignal = pyqtSignal(str)

    def __init__(self, map_viewer: GLViewWidget, map_name: str):
        super().__init__()
        self.map_viewer: GLViewWidget = map_viewer
        self.spec: MapSpec = None
        self.urls: list[list[str]] = [[]]
        self.map = MapData([], [], [], [])
        self.map_item: gl.GLSurfacePlotItem = None

        self.terminate = False

        self.__select_map(map_name)

    def __select_map(self, map_name: str):
        map_settings: MapSettings = get_map_settings()
        # find the map spec
        spec = [spec for spec in map_settings.specs if spec.name == map_name]
        if len(spec) == 0:
            return None
        self.spec = spec[0]

        self.urls = get_tile_urls(
            map_settings.tileURL,
            self.spec.northwest,
            self.spec.southeast,
            self.spec.zoom,
        )

    def __get_map_data(self):
        # map data
        map_arr = []
        n = len(self.urls) * len(self.urls[0])
        i = 0

        for row in self.urls:
            map_arr.append([])
            for u in row:
                i += 1
                self.signal_progress.emit(int(i / n * 100.0))
                self.signal_message.emit(f"Dowloading map data... {i}/{n}\nurl: {u}")
                text = requests.get(u).text
                try:
                    map_arr[-1].append(
                        np.loadtxt(
                            text.replace("e", "-0.0").splitlines(), delimiter=","
                        )
                    )
                except:
                    map_arr[-1].append(np.zeros((256, 256)))
                if n > 100:
                    # prevent the server from being overloaded
                    time.sleep(0.001)

        self.map.Z = [np.hstack(sublist) for sublist in map_arr]
        self.map.Z = np.vstack(self.map.Z)

        # self.map.Z = self.map.Z[::5, ::5] # downsample
        lat, lon = self.spec.northwest
        px_w, px_h = get_px_in_meter(lat=lat, lon=lon, zoom=self.spec.zoom)

        width = px_w * self.map.Z.shape[0]
        height = px_h * self.map.Z.shape[1]

        self.map.X = np.linspace(-width / 2, width / 2, self.map.Z.shape[0])
        self.map.Y = np.linspace(-height / 2, height / 2, self.map.Z.shape[1])

        # set the color of the map based on the elevation
        self.map.color = np.empty(
            (len(self.map.X), len(self.map.Y), 4), dtype=np.float32
        )
        max = np.max(self.map.Z)
        self.map.color[..., 0] = 0.5
        self.map.color[..., 1] = np.clip(self.map.Z / max * 0.4 + 0.6, 0, 1)
        self.map.color[..., 2] = 0.5
        self.map.color[..., 3] = 1
        self.map.color[self.map.Z == 0, :] = [0, 0, 1, 1]  # sea color
        # flatten the color array
        self.map.color = self.map.color.reshape(len(self.map.X) * len(self.map.Y), 4)

    def run(self):
        self.terminate = False

        self.__get_map_data()

        self.map_viewer.clear()  # clear the current map data

        self.map_item = gl.GLSurfacePlotItem(
            x=self.map.X,
            y=self.map.Y,
            z=self.map.Z,
            colors=self.map.color,
            shader="shaded",
            smooth=True,
        )

        self.map_viewer.addItem(self.map_item)

        self.signal_progress.emit(100)


class TrajectoryViwer(GLViewWidget):
    def __init__(self):
        super().__init__()
        self.show()
        self.setCameraPosition(distance=1500)

        self.urls: list[list[str]] = [[]]
        self.spec: MapSpec = None
        self.map = MapData([], [], [], [])
        self.map_item: gl.GLSurfacePlotItem = None

        self.vbl = QVBoxLayout()
        self.setLayout(self.vbl)
        self.pbar: QProgressDialog = None
        self.mapDataThread: MapDataThread = None

    def set_button(self, button):
        self.start_button = button

    def set_map(self, map_name: str):
        # disable the update button to prevent multiple downloads
        self.start_button.setEnabled(False)

        # start the thread to download the map data
        self.mapDataThread = MapDataThread(self, map_name)
        self.mapDataThread.signal_progress.connect(self.update_progress)
        self.mapDataThread.signal_message.connect(self.update_prog_message)
        # progress bar initialization
        self.pbar = QProgressDialog("Downloading map data...", None, 0, 100, self)
        self.vbl.addWidget(self.pbar)
        self.pbar.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.mapDataThread.start()

    def update_progress(self, value):
        self.pbar.setValue(value)
        if value == 100:
            # self.pbar.close()
            self.start_button.setEnabled(True)

    def update_prog_message(self, message):
        self.pbar.setLabelText(message)


class MainWindow(QSplitter):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Map")
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        # settings
        map_settings = get_map_settings()

        # viewer initialization
        self.trajectory_viewer = TrajectoryViwer()
        self.addWidget(self.trajectory_viewer)

        # side panel settings
        self.side_panel: QWidget = QWidget()
        self.side_panel.setMaximumWidth(200)
        self.addWidget(self.side_panel)
        layout = QVBoxLayout()
        self.side_panel.setLayout(layout)

        # self.map_select = QLabel("Select Map")
        # layout.addWidget(self.map_select)
        self.map_combo = QComboBox()
        layout.addWidget(self.map_combo)
        for spec in map_settings.specs:
            self.map_combo.addItem(spec.name)

        self.update_button = QPushButton("Update")
        layout.addWidget(self.update_button)
        self.update_button.clicked.connect(
            lambda: self.trajectory_viewer.set_map(self.map_combo.currentText())
        )
        self.trajectory_viewer.set_button(self.update_button)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    exit(app.exec())
