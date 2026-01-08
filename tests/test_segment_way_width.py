import sys
import unittest
from pathlib import Path

from shapely.geometry import LineString, Point

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from segment_way_width import signed_distance


class TestSegmentWayWidth(unittest.TestCase):
    def test_signed_distance_along_line(self) -> None:
        line = LineString([(0.0, 0.0), (10.0, 0.0)])
        point = Point(5.0, 1.0)
        dist, along = signed_distance(point, line)
        self.assertEqual(dist, 1.0)
        self.assertEqual(along, 5.0)
