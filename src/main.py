"""
    main.py - Entry point for the application.
"""

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import *
from pyqtgraph.opengl import GLGraphicsItem, GLViewWidget
from pyqtgraph.Qt import QtCore, QtGui
from stl import mesh

from geography import calc_distance, get_px_in_meter, get_tile_urls
from settings import *


class MapDataThread(QThread):
    """map data download and plot thread"""

    signal_progress: pyqtSignal = pyqtSignal(int)
    signal_message: pyqtSignal = pyqtSignal(str)

    SAVE_PATH = Path("src/map_data")  # saving path

    def __init__(self, map_name: str):
        super().__init__()
        self.spec: MapSpec = None
        self.urls: list[list[str]] = [[]]
        self.X: np.ndarray = np.array([])
        self.Y: np.ndarray = np.array([])
        self.Z: np.ndarray = np.array([])
        self.color: np.ndarray = np.array([])
        self.px_w: float = 0
        self.px_h: float = 0

        self.terminate = False

        self.map_item: gl.GLSurfacePlotItem = None

        self.__select_map(map_name)

        if get_map_settings().saveTempData:
            # create the directory if it does not exist
            self.SAVE_PATH.mkdir(parents=True, exist_ok=True)

    def __select_map(self, map_name: str):
        """select the map and set its download urls"""
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

    def __get_map_data(self) -> None:
        """get the map data using the API"""

        # download the map data
        map_arr = []
        n = len(self.urls) * len(self.urls[0])
        idx = 0  # counter

        for row in self.urls:
            map_arr.append([])
            for u in row:
                if self.terminate:
                    return  # terminate the thread
                idx += 1

                # send progress status
                self.signal_progress.emit(int(idx / n * 100.0))
                self.signal_message.emit(f"Dowloading map data... {idx}/{n}\nurl: {u}")

                text = requests.get(u).text

                if get_map_settings().saveTempData:
                    z, x, y = u.removesuffix(".txt").split("/")[
                        -3:
                    ]  # get the tile index
                    data_path = self.SAVE_PATH / f"{self.spec.name}_{z}_{x}_{y}.terrain"
                    try:
                        # check if the data is already downloaded
                        with open(data_path) as f:
                            text = f.read()
                    except FileNotFoundError:
                        # if the data is not downloaded, download it
                        text = requests.get(u).text
                        with open(
                            data_path,
                            "w",
                        ) as f:
                            f.write(text)
                else:
                    text = requests.get(u).text

                try:
                    map_arr[-1].append(
                        np.loadtxt(
                            text.replace("e", "-inf").splitlines(), delimiter=","
                        )
                    )
                except:
                    # if the region is sea, the data is not available
                    # in this case, fill the array with -inf(=sea level)
                    map_arr[-1].append(np.full((256, 256), -np.inf))
                if n > 100:
                    # prevent the server from being overloaded
                    time.sleep(0.001)

        self.Z = [np.hstack(sublist) for sublist in map_arr]
        self.Z = np.vstack(self.Z)

        if self.terminate:
            return  # terminate the thread

        # self.map.Z = self.map.Z[::5, ::5] # downsample
        lat, lon = self.spec.northwest
        self.px_w, self.px_h = get_px_in_meter(lat=lat, lon=lon, zoom=self.spec.zoom)

        width = self.px_w * self.Z.shape[0]
        height = self.px_h * self.Z.shape[1]

        self.X = np.linspace(-width / 2, width / 2, self.Z.shape[0])
        self.Y = np.linspace(-height / 2, height / 2, self.Z.shape[1])

        # set the color of the map based on the elevation
        self.color = np.empty((len(self.X), len(self.Y), 4), dtype=np.float32)
        max = np.max(self.Z)
        self.color[..., 0] = 0.5
        self.color[..., 1] = np.clip(self.Z / max * 0.4 + 0.6, 0, 1)
        self.color[..., 2] = 0.5
        self.color[..., 3] = 1
        self.color[self.Z == -np.inf, :] = [0, 0, 1, 1]  # sea color
        # flatten the color array
        self.color = self.color.reshape(len(self.X) * len(self.Y), 4)
        self.Z[self.Z == -np.inf] = 0

    def run(self):
        self.terminate = False

        self.__get_map_data()  # download the map data


class TrajectoryViwer(GLViewWidget):
    def __init__(self):
        super().__init__()

        self.map_item: gl.GLSurfacePlotItem = None
        self.paint_item: GLGraphicsItem.GLGraphicsItem = None
        self.pbar: QProgressDialog = None
        self.mapDataThread: MapDataThread = None

        self.vbl = QVBoxLayout()
        self.setLayout(self.vbl)

        # rocket_mesh = mesh.Mesh.from_file("src/rocket_model.stl")
        # verts = np.array(rocket_mesh.vectors, dtype=np.float32)
        # faces = np.arange(verts.shape[0] * 3, dtype=np.uint32).reshape(
        #     verts.shape[0], 3
        # )
        # # self.model = gl.GLMeshItem(
        #     vertexes=verts.reshape(-1, 3),
        #     faces=faces,
        #     glOptions="opaque",
        #     shader="shaded",
        #     color=(1, 1, 1, 1),
        # )
        # self.addItem(self.model)

        self.setCameraPosition(distance=1500)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.mapDataThread is not None:
            self.painter = QPainter(self)
            self.painter.setFont(QFont("Arial", 8))
            self.painter.setPen(QColor(20, 20, 20, 128))
            attribution = f" Data Attribute: {self.mapDataThread.spec.dataAttribute} "
            af = (
                QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignRight
            )
            rect = self.painter.boundingRect(self.rect(), af, attribution)
            self.painter.fillRect(rect, QColor(255, 255, 255, 128))
            self.painter.drawText(rect, af, attribution)

            self.painter.end()

    def set_button(self, button):
        self.start_button = button

    def set_map(self, map_name: str):
        # disable the update button to prevent multiple downloads
        self.start_button.setEnabled(False)

        # start the thread to download the map data
        self.mapDataThread = MapDataThread(map_name)
        self.mapDataThread.signal_progress.connect(self.update_progress)
        self.mapDataThread.signal_message.connect(self.update_prog_message)
        self.mapDataThread.finished.connect(self.draw_map)
        # progress bar initialization
        self.pbar = QProgressDialog("Downloading map data...", "cancel", 0, 100, self)
        self.vbl.addWidget(self.pbar)
        self.pbar.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.mapDataThread.start()
        self.pbar.canceled.connect(self.draw_map_termiante)

    def update_progress(self, value):
        self.pbar.setValue(value)
        if value == 100:
            # self.pbar.close()
            self.start_button.setEnabled(True)

    def update_prog_message(self, message):
        self.pbar.setLabelText(message)

    def draw_map_termiante(self):
        self.mapDataThread.terminate = True
        self.start_button.setEnabled(True)

    def draw_map(self):
        if self.mapDataThread.terminate == True:
            # if the thread is terminated unexpectedly
            return

        if self.map_item is not None:
            self.removeItem(self.map_item)  # remove the previous map datas

        self.map_item = gl.GLSurfacePlotItem(
            x=self.mapDataThread.X,
            y=self.mapDataThread.Y,
            z=self.mapDataThread.Z,
            colors=self.mapDataThread.color,
            shader="shaded",
            smooth=True,
        )
        self.addItem(self.map_item)


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
        self.side_panel.setFixedWidth(200)
        self.addWidget(self.side_panel)
        layout = QVBoxLayout()
        self.side_panel.setLayout(layout)

        select_map_layout = QHBoxLayout()
        layout.addLayout(select_map_layout)
        self.map_select = QLabel("Select Map")
        select_map_layout.addWidget(self.map_select)
        self.map_combo = QComboBox()
        select_map_layout.addWidget(self.map_combo)
        for spec in map_settings.specs:
            self.map_combo.addItem(spec.name)

        map_button_layout = QVBoxLayout()
        layout.addLayout(map_button_layout)
        self.update_button = QPushButton("Apply Map Selection")
        self.update_button.setIcon(QtGui.QIcon("src/icons/draw.svg"))
        map_button_layout.addWidget(self.update_button)
        self.update_button.clicked.connect(
            lambda: self.trajectory_viewer.set_map(self.map_combo.currentText())
        )
        self.trajectory_viewer.set_button(
            self.update_button
        )  # asocciate the button with the viewer

        self.reload_conf_button = QPushButton("Reload Settings File")
        self.reload_conf_button.setIcon(QtGui.QIcon("src/icons/refresh.svg"))
        self.reload_conf_button.clicked.connect(load_settings)
        map_button_layout.addWidget(self.reload_conf_button)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    exit(app.exec())
