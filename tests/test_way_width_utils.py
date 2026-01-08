import json
import sys
import tempfile
import unittest
from pathlib import Path

import polyline
from shapely.geometry import LineString

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from way_width_utils import WayWidthUtils


class TestWayWidthUtils(unittest.TestCase):
    def test_read_way_line(self) -> None:
        osm = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lon="0.0" lat="0.0"/>
  <node id="2" lon="1.0" lat="1.0"/>
  <way id="10">
    <nd ref="1"/>
    <nd ref="2"/>
  </way>
</osm>
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "way.osm"
            path.write_text(osm, encoding="utf-8")
            line = WayWidthUtils.read_way_line(path)
            self.assertEqual(list(line.coords), [(0.0, 0.0), (1.0, 1.0)])

    def test_utm_crs(self) -> None:
        line = LineString([(12.0, 55.0), (12.1, 55.1)])
        crs = WayWidthUtils.utm_crs(line)
        self.assertEqual(crs.to_epsg(), 32633)

    def test_load_polylines(self) -> None:
        points = [(1.0, 2.0), (1.1, 2.1)]
        encoded = [polyline.encode(points)]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "poly.json"
            path.write_text(json.dumps(encoded), encoding="utf-8")
            decoded = WayWidthUtils.load_polylines(path)
            self.assertEqual(decoded, [points])
