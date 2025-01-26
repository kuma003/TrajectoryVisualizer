import pytest
import numpy as np
from src.geography import tile2latlon, latlon2tile, calc_distance, get_tile_urls


@pytest.mark.parametrize(
    "x, y, z, expected",
    [(1, 1, 1, (0.0, 0.0)), (233080, 102845, 18, (36.104665, 140.087099))],
)
def test_tile2latlon(x, y, z, expected):
    assert np.allclose(tile2latlon(x, y, z), expected, atol=1e-3)


@pytest.mark.parametrize(
    "lat, lon, z, expected",
    [
        (36.104665, 140.087099, 14, (14567, 6427)),
    ],
)
def test_latlon2tile(lat, lon, z, expected):
    assert np.allclose(np.floor(latlon2tile(lat, lon, z)), expected, atol=1e-4)


# Expected values are calculated by using GSI's distance calculator
# (https://vldb.gsi.go.jp/sokuchi/surveycalc/surveycalc/bl2stf.html).
@pytest.mark.parametrize(
    "lat1, lon1, lat2, lon2, expected",
    [
        (36.1037748, 140.087855, 35.6550285, 139.74475, 58643.824),
        (38.2685833, 140.872028, 38.2680833, 140.8695, 228.066),
    ],
)
def test_calc_distance(lat1, lon1, lat2, lon2, expected):
    print(calc_distance(lat1, lon1, lat2, lon2))
    assert np.isclose(
        calc_distance(lat1, lon1, lat2, lon2=lon2), expected, atol=2e-2
    )  # error must be less than 1 m


@pytest.mark.parametrize(
    "url, northwest, southeast, zoom, expected",
    [
        (
            "https://cyberjapandata.gsi.go.jp/xyz/dem/{z}/{x}/{y}.txt",
            (34.808917, 139.331932),
            (34.672182, 139.472122),
            12,
            [
                [
                    "https://cyberjapandata.gsi.go.jp/xyz/dem/12/3633/1625.txt",
                    "https://cyberjapandata.gsi.go.jp/xyz/dem/12/3634/1625.txt",
                ],
                [
                    "https://cyberjapandata.gsi.go.jp/xyz/dem/12/3633/1626.txt",
                    "https://cyberjapandata.gsi.go.jp/xyz/dem/12/3634/1626.txt",
                ],
            ],
        )
    ],
)
def test_get_tile_urls(url, northwest, southeast, zoom, expected):
    assert get_tile_urls(url, northwest, southeast, zoom) == expected


if __name__ == "__main__":
    pytest.main()
