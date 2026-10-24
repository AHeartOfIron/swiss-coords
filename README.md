# swiss-coords

[![tests](https://github.com/AHeartOfIron/swiss-coords/actions/workflows/ci.yml/badge.svg)](https://github.com/AHeartOfIron/swiss-coords/actions/workflows/ci.yml)

Convert GPS coordinates (WGS84) to and from the Swiss national grids **LV95** and **LV03**.
Pure Python, no dependencies, one small file.

It uses the official swisstopo approximate formulas. Each direction is accurate to about 1 metre inside Switzerland.
That is fine for maps, field notes, emergency coordinates and data cleaning.
For survey work, use swisstopo [REFRAME](https://www.swisstopo.admin.ch/en/coordinate-conversion-reframe).

## Install

```bash
pip install git+https://github.com/AHeartOfIron/swiss-coords
```

## Command line

The input system is detected for you. Degrees, minutes and seconds work too.

```text
$ swisscoords 46.2044 6.1432
WGS84  46.204400, 6.143200
LV95   E 2500016.17  N 1117821.02
LV03   E 500016.17  N 117821.02
map    https://map.geo.admin.ch/?center=2500016,1117821&z=10

$ swisscoords 2600000 1200000
WGS84  46.951081, 7.438637
...

$ swisscoords "46°2'38.87\"N" "8°43'49.79\"E"
```

Convert a whole CSV file. New columns are added to every row:

```bash
swisscoords --csv points.csv --cols lat,lon > points_ch.csv
```

Rows that cannot be read are kept unchanged and counted on stderr.

## Python

```python
from swisscoords import wgs84_to_lv95, lv95_to_wgs84, detect

g = wgs84_to_lv95(46.2044, 6.1432)        # Grid(east=2500016.17..., north=1117821.02..., height=None)
lat, lon, h = lv95_to_wgs84(2600000, 1200000, 500)
detect(1118000, 2500000)                  # "lv95", in either order
```

Heights: pass the WGS84 ellipsoidal height and get the Swiss LN02 height back, and the other way round.
The height formula is also approximate (a few decimetres).

## Tests

```bash
pip install -e ".[test]"
pytest
```

The tests check the worked example from the swisstopo formula document, the Bern origin, and round trips in Geneva, Zurich, Lugano and Lausanne.

## Reference

swisstopo, *Approximate formulas for the transformation between Swiss projection coordinates and WGS84*.

## License

MIT, Illia Usachov.
