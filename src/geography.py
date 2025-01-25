"""
    geography.py - Helper functions for geographic calculations.
"""

import numpy as np
from typing import Union

Number = Union[int, float, list, np.ndarray]


def tile2latlon(x: Number, y: Number, z: float) -> tuple[Number, Number]:
    """
    Convert tile coordinates to latitude and longitude.

    Parameters
    ----------
    x : Number
        Tile x-coordinate.
    y : Number
        Tile y-coordinate.
    z : float
        Zoom level.

    Returns
    -------
    lat, lon: tuple[Number, Number]
        Latitude and longitude(degrees).

    Notes
    -----
    Mathematics Reference: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Mathematics
    """
    n = 2.0**z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * y / n)))
    lat_deg = np.degrees(lat_rad)
    return lat_deg, lon_deg


def latlon2tile(lat: Number, lon: Number, z: Number) -> tuple[Number, Number]:
    """
    Convert latitude and longitude to tile coordinates.

    Parameters
    ----------
    lat : Number
        Latitude in degrees.
    lon : float
        Longitude in degrees.
    z : float
        Zoom level.

    Returns
    -------
    x, y: tuple
        Tile x and y coordinates.

    Notes
    -----
    Mathematics Reference: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Mathematics
    """
    n = 2.0**z
    x = np.floor((lon + 180.0) / 360.0 * n)
    lat_rad = np.radians(lat)
    y = np.floor(
        (1.0 - np.log(np.tan(lat_rad) + 1.0 / np.cos(lat_rad)) / np.pi) / 2.0 * n
    )
    return x, y


def calc_distance(lat1: Number, lon1: Number, lat2: Number, lon2: Number) -> Number:
    """
    Calculate the geodetic distance between two points on the Earth's surface.

    Parameters
    ----------
    lat1 : Number
        Latitude of the first point.
    lon1 : Number
        Longitude of the first point.
    lat2 : Number
        Latitude of the second point.
    lon2 : Number
        Longitude of the second point.

    Returns
    -------
    distance: float
        Distance between the two points in meters.

    Notes
    -----
    Mathematics Reference:
        - https://qiita.com/matsuda_tkm/items/4eba5632535ca2f699b4 (Qiita)
        - https://www2.nc-toyama.ac.jp/WEB_Profile/mkawai/lecture/sailing/geodetic/geosail.html (Original)
    """

    # GRS80 constants (JGD2011: GSI(https://www.gsi.go.jp/sokuchikijun/datum-main.html))
    f = 1.0 / 298.257222101  # Earth's flattening
    A = 6378_137.0  # Earth's semi-major axis in meters
    B = A * (1 - f)  # Earth's semi-minor axis in meters

    # Reduced latitude
    phi_1 = np.arctan2(B * np.tan(np.radians(lat1)), A)
    phi_2 = np.arctan2(B * np.tan(np.radians(lat2)), A)

    # spherical distance
    X = np.arccos(
        np.sin(phi_1) * np.sin(phi_2)
        + np.cos(phi_1) * np.cos(phi_2) * np.cos(np.radians(lon2 - lon1))
    )

    # Lambert-Andoyer correction
    Delta_rho = (
        f
        * (
            (np.sin(X) - X) * ((np.sin(phi_1) + np.sin(phi_2)) / np.cos(X / 2)) ** 2
            - (np.sin(X) + X) * ((np.sin(phi_1) - np.sin(phi_2)) / np.sin(X / 2)) ** 2
        )
        / 8
    )

    # Geodetic distance
    distance = A * (X + Delta_rho)

    return distance
