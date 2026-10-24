import pytest

from swisscoords import detect, lv03_to_wgs84, lv95_to_wgs84, parse_dms, wgs84_to_lv03, wgs84_to_lv95
from swisscoords.cli import convert, main

# Worked example from the swisstopo document "Approximate formulas for the
# transformation between Swiss projection coordinates and WGS84".
EX_LAT = 46 + 2 / 60 + 38.87 / 3600
EX_LON = 8 + 43 / 60 + 49.79 / 3600


def test_swisstopo_example_to_lv95():
    g = wgs84_to_lv95(EX_LAT, EX_LON, 650.60)
    assert g.east == pytest.approx(2_699_999.76, abs=0.05)
    assert g.north == pytest.approx(1_099_999.97, abs=0.05)
    assert g.height == pytest.approx(600.05, abs=0.05)


def test_swisstopo_example_back_to_wgs84():
    lat, lon, h = lv95_to_wgs84(2_700_000, 1_100_000, 600)
    assert lat == pytest.approx(EX_LAT, abs=1e-5)
    assert lon == pytest.approx(EX_LON, abs=1e-5)
    assert h == pytest.approx(650.60, abs=0.5)


def test_bern_origin():
    g = wgs84_to_lv95(46.951082877, 7.438632495)
    assert g.east == pytest.approx(2_600_000, abs=1)
    assert g.north == pytest.approx(1_200_000, abs=1)


@pytest.mark.parametrize("lat,lon", [(46.2044, 6.1432), (47.3769, 8.5417), (46.0037, 8.9511), (46.5197, 6.6323)])
def test_round_trip_within_a_few_metres(lat, lon):
    g = wgs84_to_lv95(lat, lon)
    back_lat, back_lon, _ = lv95_to_wgs84(g.east, g.north)
    # Each direction is good to about 1 m, so a round trip may drift up to
    # about 2 m near the borders (Geneva is the worst case). 2.5e-5 deg ~ 2.8 m.
    assert back_lat == pytest.approx(lat, abs=2.5e-5)
    assert back_lon == pytest.approx(lon, abs=2.5e-5)


def test_lv03_is_lv95_minus_offset():
    a, b = wgs84_to_lv95(46.2044, 6.1432), wgs84_to_lv03(46.2044, 6.1432)
    assert (a.east - b.east, a.north - b.north) == (2_000_000, 1_000_000)
    assert lv03_to_wgs84(b.east, b.north)[:2] == lv95_to_wgs84(a.east, a.north)[:2]


@pytest.mark.parametrize("a,b,want", [
    (46.2, 6.1, "wgs84"), (2_500_000, 1_118_000, "lv95"), (1_118_000, 2_500_000, "lv95"),
    (500_000, 118_000, "lv03"),
])
def test_detect(a, b, want):
    assert detect(a, b) == want


def test_detect_rejects_nonsense():
    with pytest.raises(ValueError):
        detect(5_000_000, 5_000_000)


@pytest.mark.parametrize("text,want", [
    ("46.5", 46.5), ("46,5", 46.5), ("46°30'", 46.5), ("46 30 0", 46.5),
    ("8°43'49.79\"E", EX_LON), ("8°30'W", -8.5), ("-8.5", -8.5),
])
def test_parse_dms(text, want):
    assert parse_dms(text) == pytest.approx(want)


def test_convert_accepts_any_system():
    from_wgs = convert(46.2044, 6.1432)
    from_lv95 = convert(from_wgs["lv95_e"], from_wgs["lv95_n"])
    assert from_lv95["lat"] == pytest.approx(46.2044, abs=2.5e-5)


def test_cli_prints_all_systems(capsys):
    assert main(["46.2044", "6.1432"]) == 0
    out = capsys.readouterr().out
    assert "LV95" in out and "LV03" in out and "map.geo.admin.ch" in out


def test_cli_csv(tmp_path, capsys):
    f = tmp_path / "p.csv"
    f.write_text("name,lat,lon\nGeneva,46.2044,6.1432\nbroken,x,y\n", encoding="utf-8")
    assert main(["--csv", str(f)]) == 0
    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert lines[0] == "name,lat,lon,lv95_e,lv95_n,lv03_e,lv03_n"
    assert lines[1].startswith("Geneva,46.2044,6.1432,25")
    assert "1 row(s)" in captured.err
