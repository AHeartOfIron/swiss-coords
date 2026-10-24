"""Convert between WGS84 (GPS) and the Swiss grids LV95 and LV03.

Uses the swisstopo approximate formulas, accurate to about 1 metre in
Switzerland. That is enough for maps, field work and data cleaning. For
survey-grade work use swisstopo REFRAME instead.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Grid", "wgs84_to_lv95", "lv95_to_wgs84", "wgs84_to_lv03", "lv03_to_wgs84", "detect", "parse_dms"]
__version__ = "0.1.0"

# LV95 = LV03 + these offsets (east, north).
LV95_OFFSET = (2_000_000.0, 1_000_000.0)


@dataclass(frozen=True)
class Grid:
    east: float
    north: float
    height: float | None = None


def _aux_from_wgs(lat: float, lon: float) -> tuple[float, float]:
    """Latitude and longitude in degrees to the auxiliary values phi', lambda'."""
    phi = (lat * 3600 - 169028.66) / 10000
    lam = (lon * 3600 - 26782.5) / 10000
    return phi, lam


def wgs84_to_lv95(lat: float, lon: float, height: float | None = None) -> Grid:
    """WGS84 degrees to LV95 metres. Height is ellipsoidal in, LN02 out."""
    phi, lam = _aux_from_wgs(lat, lon)
    east = (2600072.37 + 211455.93 * lam - 10938.51 * lam * phi
            - 0.36 * lam * phi**2 - 44.54 * lam**3)
    north = (1200147.07 + 308807.95 * phi + 3745.25 * lam**2 + 76.63 * phi**2
             - 194.56 * lam**2 * phi + 119.79 * phi**3)
    h = None if height is None else height - 49.55 + 2.73 * lam + 6.94 * phi
    return Grid(east, north, h)


def lv95_to_wgs84(east: float, north: float, height: float | None = None) -> tuple[float, float, float | None]:
    """LV95 metres to WGS84 (lat, lon, height) in degrees."""
    y = (east - 2_600_000) / 1_000_000
    x = (north - 1_200_000) / 1_000_000
    lam = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x**2 - 0.0436 * y**3
    phi = (16.9023892 + 3.238272 * x - 0.270978 * y**2 - 0.002528 * x**2
           - 0.0447 * y**2 * x - 0.0140 * x**3)
    h = None if height is None else height + 49.55 - 12.60 * y - 22.64 * x
    return phi * 100 / 36, lam * 100 / 36, h


def wgs84_to_lv03(lat: float, lon: float, height: float | None = None) -> Grid:
    g = wgs84_to_lv95(lat, lon, height)
    return Grid(g.east - LV95_OFFSET[0], g.north - LV95_OFFSET[1], g.height)


def lv03_to_wgs84(east: float, north: float, height: float | None = None) -> tuple[float, float, float | None]:
    return lv95_to_wgs84(east + LV95_OFFSET[0], north + LV95_OFFSET[1], height)


def detect(a: float, b: float) -> str:
    """Guess the system of a coordinate pair: "lv95", "lv03" or "wgs84".

    Swiss grid easting is always larger than northing, so the pair may be
    given in either order. Raises ValueError for anything outside Switzerland.
    """
    east, north = max(a, b), min(a, b)
    if 2_450_000 <= east <= 2_850_000 and 1_050_000 <= north <= 1_320_000:
        return "lv95"
    if 450_000 <= east <= 850_000 and 50_000 <= north <= 320_000:
        return "lv03"
    if -90 <= a <= 90 and -180 <= b <= 180:
        return "wgs84"
    raise ValueError(f"not a WGS84, LV95 or LV03 coordinate: {a}, {b}")


def parse_dms(text: str) -> float:
    """Parse 46°2'38.87"N, 46 2 38.87, 46.0441 or 8°43'49.79"W to degrees."""
    s = text.strip().upper()
    sign = -1 if s.endswith(("S", "W")) or s.startswith("-") else 1
    for ch in "°'\"′″NSEW-":
        s = s.replace(ch, " ")
    parts = [float(p) for p in s.replace(",", ".").split()]
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"cannot read angle: {text!r}")
    deg = sum(p / 60**i for i, p in enumerate(parts))
    return sign * deg
