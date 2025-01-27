"""thrust.py - Thrust with particle simulation."""

import sys

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLScatterPlotItem
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication


class Thrust(GLScatterPlotItem):
    """Thrust with particle simulation."""

    def __init__(
        self,
        n_particles,
        origin: tuple[float, float, float],
        direction: tuple[float, float, float],
        nozle_radius: float = 0.02,
    ):
        direction = np.array(direction) / np.linalg.norm(
            direction
        )  # normalize direction
        # Calculate two vectors perpendicular to the direction vector
        if direction[0] == 0 and direction[1] == 0:
            perp1 = np.array([1, 0, 0])
        else:
            perp1 = np.array([-direction[1], direction[0], 0])
            perp1 /= np.linalg.norm(perp1)

        perp2 = np.cross(direction, perp1)
        perp2 /= np.linalg.norm(perp2)

        # Create a set of points
        phi = np.random.uniform(0, 2 * np.pi, n_particles)
        r = np.random.uniform(0, nozle_radius, n_particles)
        self.pos = (
            perp1.reshape(1, 3) * (r * np.cos(phi))[:, None]
            + perp2.reshape(1, 3) * (r * np.sin(phi))[:, None]
            + np.array(origin).reshape(1, 3)
        )

        super().__init__(pos=self.pos, color=(1, 1, 1, 1), size=0.001, pxMode=False)
        self.n_particles = n_particles

    def update(self):
        """Update the position of the particles."""
        print("got here")
        # self.pos += np.random.random(size=(1000, 3)) * 0.1
        # self.setData(pos=self.pos, color=self.color, size=self.size)

    def init_particles(self, point, radius):
        """Initialize the particles in the simulation."""
        self.pos = np.random.random(size=(self.n_particles, 3)) * 20
        self.setData(pos=self.pos, color=(1, 1, 1, 1), size=0.1)

    def set_velocity(self, n_particles):
        """Create a set of velocitys based on Maxwell-Boltzmann distribution."""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = gl.GLViewWidget()
    w.show()
    w.setWindowTitle("3D Plot Example")
    w.setCameraPosition(distance=1)

    g = gl.GLGridItem()
    g.scale(0.1, 0.1, 0.1)
    w.addItem(g)

    # Create a set of points
    # pos = np.random.random(size=(1000, 3)) * 20
    # scatter = gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 1), size=0.1)
    scatter = Thrust(100000, (0, 0, 0), direction=(0, 0, 1))
    w.addItem(scatter)

    app.exec()
