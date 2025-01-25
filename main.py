import numpy as np
import requests

import pyqtgraph as pg
import pyqtgraph.opengl as gl

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
            requests.get(u).text.replace("e", "-0.0").splitlines(), delimiter=","
        )
        for u in row
    ]
    for row in urls
]


Z = [np.hstack(sublist) for sublist in map_arr]

Z = np.vstack(Z)

# Z = Z[::5, ::5]

# X, Y = np.meshgrid(
#     (np.arange(Z.shape[0]) - Z.shape[0] / 2) * 30,
#     (np.arange(Z.shape[1]) - Z.shape[1] / 2) * 30,
# )
X = (np.arange(Z.shape[0]) - Z.shape[0] / 2) * 10
Y = (np.arange(Z.shape[1]) - Z.shape[1] / 2) * 10

# Z = Z.flatten()
# Create a GLViewWidget for 3D visualization
app = pg.mkQApp("3d Map")
view = gl.GLViewWidget()
view.show()
view.setWindowTitle("3D Scatter Plot")
view.setCameraPosition(distance=1500)
color = np.empty((len(X), len(Y), 4), dtype=np.float32)
max = np.max(Z.flatten())
color[..., 0] = 0.5
color[..., 1] = np.clip(Z / max * 0.4 + 0.6, 0, 1)
color[..., 2] = 0.5
color[..., 3] = 1
color[Z == 0, :] = [0, 0, 1, 1]
# color[:, 3] = 1

map = gl.GLSurfacePlotItem(
    x=X,
    y=Y,
    z=Z,
    colors=color.reshape(len(X) * len(Y), 4),
    shader="shaded",
    smooth=True,
)
# map.shader()["colorMap"] = np.array([0.2, 2, 0.5, 0.2, 1, 1, 0.2, 0, 2])
view.addItem(map)

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
if __name__ == "__main__":
    app.exec()
