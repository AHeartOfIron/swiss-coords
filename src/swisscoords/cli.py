"""swisscoords: convert one coordinate pair, or a CSV column pair, from the command line.

    swisscoords 46.2044 6.1432          # WGS84 to LV95 and LV03
    swisscoords 2500000 1118000         # LV95 to WGS84 (system is detected)
    swisscoords "46°2'38.87\"" "8°43'49.79\""
    swisscoords --csv points.csv --cols lat,lon > out.csv
"""

from __future__ import annotations

import argparse
import csv
import sys

from . import detect, lv03_to_wgs84, lv95_to_wgs84, parse_dms, wgs84_to_lv03, wgs84_to_lv95


def convert(a: float, b: float) -> dict[str, float]:
    """Every representation of one point, whatever system it came in."""
    system = detect(a, b)
    if system == "wgs84":
        lat, lon = a, b
    else:
        east, north = max(a, b), min(a, b)
        lat, lon, _ = (lv95_to_wgs84 if system == "lv95" else lv03_to_wgs84)(east, north)
    lv95, lv03 = wgs84_to_lv95(lat, lon), wgs84_to_lv03(lat, lon)
    return {"lat": round(lat, 6), "lon": round(lon, 6),
            "lv95_e": round(lv95.east, 2), "lv95_n": round(lv95.north, 2),
            "lv03_e": round(lv03.east, 2), "lv03_n": round(lv03.north, 2)}


def _print_point(p: dict[str, float]) -> None:
    print(f"WGS84  {p['lat']:.6f}, {p['lon']:.6f}")
    print(f"LV95   E {p['lv95_e']:.2f}  N {p['lv95_n']:.2f}")
    print(f"LV03   E {p['lv03_e']:.2f}  N {p['lv03_n']:.2f}")
    print(f"map    https://map.geo.admin.ch/?center={p['lv95_e']:.0f},{p['lv95_n']:.0f}&z=10")


def _run_csv(path: str, cols: str) -> int:
    first, second = cols.split(",")
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        extra = ["lat", "lon", "lv95_e", "lv95_n", "lv03_e", "lv03_n"]
        out = csv.DictWriter(sys.stdout, fieldnames=fields + [c for c in extra if c not in fields])
        out.writeheader()
        bad = 0
        for row in reader:
            try:
                row.update(convert(parse_dms(row[first]), parse_dms(row[second])))
            except (ValueError, KeyError):
                bad += 1
            out.writerow(row)
    if bad:
        print(f"{bad} row(s) could not be converted and were left as they were", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="swisscoords", description="WGS84 <-> Swiss LV95 / LV03, about 1 m accuracy.")
    ap.add_argument("a", nargs="?", help="latitude, or easting/northing")
    ap.add_argument("b", nargs="?", help="longitude, or northing/easting")
    ap.add_argument("--csv", help="convert every row of this CSV file and write CSV to stdout")
    ap.add_argument("--cols", default="lat,lon", help="the two input columns of --csv (default: lat,lon)")
    args = ap.parse_args(argv)
    try:
        if args.csv:
            return _run_csv(args.csv, args.cols)
        if args.a is None or args.b is None:
            ap.error("give two numbers, or --csv FILE")
        _print_point(convert(parse_dms(args.a), parse_dms(args.b)))
    except ValueError as e:
        print(f"swisscoords: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
