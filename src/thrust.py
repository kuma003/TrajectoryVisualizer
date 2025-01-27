"""thrust.py - Thrust with particle simulation."""

import sys

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLVolumeItem
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication

from scipy.stats import norm


def calc_spread_coeff(
    T: float, M: float, velocity: tuple[float, float, float], dx: float, dt: float
) -> np.ndarray:
    """Calculate the spread coefficient for the particle simulation based on Maxwell-Boltzmann distribution.

    Parameters
    ----------
    T : float
        Temperature of the gas.
    M : float
        Molar mass of the gas.
    velocity : tuple[float, float, float]
        Resolution of the volume mesh.
    dt : float
        Time step of the particle simulation.

    Returns
    -------
    np.array (3, 3, 3):
        Spread coefficient for the particle simulation.
    """
    k_B = 1.38064852e-23  # Boltzmann constant
    sigma = np.sqrt(k_B * T / M)  # standard deviation

    spread_threshold = dx / dt  # spreading threshold

    prob_x_neg = norm.cdf(-spread_threshold - velocity[0], loc=0, scale=sigma)
    prob_x_pos = 1 - norm.cdf(spread_threshold - velocity[0], loc=0, scale=sigma)
    prob_y_neg = norm.cdf(-spread_threshold - velocity[1], loc=0, scale=sigma)
    prob_y_pos = 1 - norm.cdf(spread_threshold - velocity[1], loc=0, scale=sigma)
    prob_z_neg = norm.cdf(-spread_threshold - velocity[2], loc=0, scale=sigma)
    prob_z_pos = 1 - norm.cdf(spread_threshold - velocity[2], loc=0, scale=sigma)

    if prob_x_neg + prob_x_pos + prob_y_neg + prob_y_pos + prob_z_neg + prob_z_pos > 1:
        sum = (
            prob_x_neg + prob_x_pos + prob_y_neg + prob_y_pos + prob_z_neg + prob_z_pos
        )
        prob_x_neg /= sum  # normalize
        prob_x_pos /= sum
        prob_y_neg /= sum
        prob_y_pos /= sum
        prob_z_neg /= sum
        prob_z_pos /= sum

    prob_stag = (
        1 - prob_x_neg - prob_x_pos - prob_y_neg - prob_y_pos - prob_z_neg - prob_z_pos
    )

    return np.array(
        [
            [[0, 0, 0], [0, prob_y_pos, 0], [0, 0, 0]],
            [
                [0, prob_y_neg, 0],
                [prob_x_pos, prob_stag, prob_x_neg],
                [0, prob_y_pos, 0],
            ],
            [[0, 0, 0], [0, prob_z_neg, 0], [0, 0, 0]],
        ]
    )


class Thrust(GLVolumeItem):
    """Thrust with particle simulation."""

    def __init__(
        self,
        width: int,
        height: int,
        dx: float,
        origin: tuple[float, float, float],
        direction: tuple[float, float, float],
        nozle_radius: float = 0.02,
    ):
        """Thrust with volume mesh.

        Parameters
        ----------
        width : int
            Width of the volume mesh.
            Actual width is width * dx.
        height : int
            Height of the volume mesh.
            Actual height is height * dx.
        dx : float
            Resolution of the volume mesh.
        origin : tuple[float, float, float]
            Origin of the volume mesh.
        direction : tuple[float, float, float]
            Direction of the thrust.
        nozle_radius : float, optional
            Radius of the nozle, by default 0.02.
        """
        self.mesh = np.zeros((width, width, height))  # volume data
        self.mesh[...] = 0
        self.color = np.zeros((width, width, height, 4), dtype=np.ubyte)  # color data
        self.color[..., :3] = self.mesh[..., None]
        self.color[..., 3] = 255
        super().__init__(self.color)

        self.scale(dx, dx, dx)
        self.translate(*origin)  # move to origin
        self.translate(-width // 2 * dx, -width // 2 * dx, 0)  # move to center
        # Calculate the angle and axis for rotation
        direction = np.array(direction) / np.linalg.norm(direction)  # normalize
        angle = np.arccos(np.dot(direction, [0, 0, 1]))
        axis = np.cross([0, 0, 1], direction)
        if np.linalg.norm(axis) == 0:
            axis = [1, 0, 0]
        axis = axis / np.linalg.norm(axis)  # normalize

        self.dt = 0.01  # time step(s)

        # Apply the rotation
        self.rotate(np.degrees(angle), *axis)

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.time_step)
        self.timer.start(self.dt * 1000)

    def time_step(self):
        """Time step for the simulation."""
        self.mesh = np.roll(self.mesh, 1, axis=2)
        self.color[..., 0] = np.random.uniform(100, 255, size=self.mesh.shape)
        self.color[..., 3] = np.random.uniform(0, 20, size=self.mesh.shape)

        self.setData(self.color)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = gl.GLViewWidget()
    w.show()
    w.setWindowTitle("3D Plot Example")
    w.setCameraPosition(distance=1)

    g = gl.GLGridItem()
    w.addItem(g)

    # Create a set of points
    # pos = np.random.random(size=(1000, 3)) * 20
    # scatter = gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 1), size=0.1)
    thrust = Thrust(100, 200, 0.001, (0, 0, 0), (0, 0, -1), 0.02)
    w.addItem(thrust)

    app.exec()
