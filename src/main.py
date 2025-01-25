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

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QSplitter,
)


class TrajectoryViwer(GLViewWidget):
    def __init__(self):
        super().__init__()
        self.show()
        self.setCameraPosition(distance=1500)
        urls = [
            [
                "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3633/1625.txt",
                "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3634/1625.txt",
            ],
            [
                "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3633/1626.txt",
                "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3634/1626.txt",
            ],
        ]

        map_arr = [
            [
                np.loadtxt(
                    requests.get(u).text.replace("e", "-0.0").splitlines(),
                    delimiter=",",
                )
                for u in row
            ]
            for row in urls
        ]
        self.Z = [np.hstack(sublist) for sublist in map_arr]

        self.Z = np.vstack(self.Z)

        self.Z = self.Z[::5, ::5]
        self.X = (np.arange(self.Z.shape[0]) - self.Z.shape[0] / 2) * 10
        self.Y = (np.arange(self.Z.shape[1]) - self.Z.shape[1] / 2) * 10

    def set_map(self):

        self.clear()
        self.d

        color = np.empty((len(self.X), len(self.Y), 4), dtype=np.float32)
        max = np.max(self.Z.flatten())
        color[..., 0] = 0.5
        color[..., 1] = np.clip(self.Z / max * 0.4 + 0.6, 0, 1)
        color[..., 2] = 0.5
        color[..., 3] = 1
        color[self.Z == 0, :] = [0, 0, 1, 1]
        # color[:, 3] = 1
        map = gl.GLSurfacePlotItem(
            x=self.X,
            y=self.Y,
            z=self.Z,
            colors=color.reshape(len(self.X) * len(self.Y), 4),
            shader="shaded",
            smooth=True,
        )
        self.addItem(map)


class MainWindow(QSplitter):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Map")
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        self.p2 = TrajectoryViwer()
        self.addWidget(self.p2)

        side_panel: QWidget = QWidget()
        layout = QVBoxLayout()
        side_panel.setLayout(layout)
        update_button = QPushButton("Update")
        update_button.clicked.connect(lambda: self.p2.set_map())
        layout.addWidget(update_button)
        self.addWidget(side_panel)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    exit(app.exec())


# urls = [
#     [
#         "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3633/1625.txt",
#         "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3634/1625.txt",
#     ],
#     [
#         "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3633/1626.txt",
#         "http://cyberjapandata.gsi.go.jp/xyz/dem/12/3634/1626.txt",
#     ],
# ]

# map_arr = [
#     [
#         np.loadtxt(
#             requests.get(u).text.replace("e", "-0.0").splitlines(), delimiter=","
#         )
#         for u in row
#     ]
#     for row in urls
# ]


# Z = [np.hstack(sublist) for sublist in map_arr]

# Z = np.vstack(Z)

# # Z = Z[::5, ::5]

# # X, Y = np.meshgrid(
# #     (np.arange(Z.shape[0]) - Z.shape[0] / 2) * 30,
# #     (np.arange(Z.shape[1]) - Z.shape[1] / 2) * 30,
# # )
# X = (np.arange(Z.shape[0]) - Z.shape[0] / 2) * 10
# Y = (np.arange(Z.shape[1]) - Z.shape[1] / 2) * 10

# # Z = Z.flatten()
# # Create a GLViewWidget for 3D visualization
# app = pg.mkQApp("3d Map")
# view = gl.GLViewWidget()
# view.show()
# view.setWindowTitle("3D Scatter Plot")
# view.setCameraPosition(distance=1500)
# color = np.empty((len(X), len(Y), 4), dtype=np.float32)
# max = np.max(Z.flatten())
# color[..., 0] = 0.5
# color[..., 1] = np.clip(Z / max * 0.4 + 0.6, 0, 1)
# color[..., 2] = 0.5
# color[..., 3] = 1
# color[Z == 0, :] = [0, 0, 1, 1]
# # color[:, 3] = 1

# map = gl.GLSurfacePlotItem(
#     x=X,
#     y=Y,
#     z=Z,
#     colors=color.reshape(len(X) * len(Y), 4),
#     shader="shaded",
#     smooth=True,
# )
# # map.shader()["colorMap"] = np.array([0.2, 2, 0.5, 0.2, 1, 1, 0.2, 0, 2])
# view.addItem(map)

# color = np.empty((len(Z), 3), dtype=np.float32)
# max = np.max(Z)
# color[:, 0] = np.clip((1 + Z / max) / 2, 0, 1)
# color[:, 1] = np.clip((1 + Z / max) / 6, 0, 1)
# color[:, 2] = np.clip((1 + Z / max) / 6, 0, 1)
# # color[:, 3] = 1

# color[Z == 0] = [0, 0, 1]

# Create scatter plot item
# scatter = gl.GLScatterPlotItem(
#     pos=np.c_[X.flatten(), Y.flatten(), Z],
#     size=1,
#     color=(1, 1, 1),
#     pxMode=False,
# )
# # scatter.setGLOptions("translucent")
# view.addItem(scatter)
# scatter.setData(color=color)

# # for x axis
# for x, y, z in zip(X, Y, Z):
#     pts = np.column_stack([x, y, z])
#     color = np.empty((len(z), 4), dtype=np.float32)
#     color[:, 0] = 0
#     color[:, 1] = 1
#     color[:, 2] = 0
#     color[:, 3] = 1
#     color[z == 0] = [0, 0, 1, 1]
#     plt = gl.GLLinePlotItem(pos=pts, color=color, width=1, antialias=True)
#     plt.setGLOptions("translucent")

#     view.addItem(plt)

# X = X.transpose()
# Y = Y.transpose()
# Z = Z.transpose()
# # for y axis
# for x, y, z in zip(X, Y, Z):
#     pts = np.column_stack([x, y, z])
#     color = np.empty((len(z), 4), dtype=np.float32)
#     color[:, 0] = 0
#     color[:, 1] = 1
#     color[:, 2] = 0
#     color[:, 3] = 1
#     color[z == 0] = [0, 0, 1, 1]
#     plt = gl.GLLinePlotItem(pos=pts, color=color, width=1, antialias=True)
#     plt.setGLOptions("translucent")
#     view.addItem(plt)

# Start Qt event loop
# if __name__ == "__main__":
#     app.exec()
