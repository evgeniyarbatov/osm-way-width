import sys
import unittest
from pathlib import Path

from shapely.geometry import LineString, Point

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from estimate_way_width import cumulative_segment_lengths, signed_distance


class TestEstimateWayWidth(unittest.TestCase):
    def test_signed_distance_simple(self) -> None:
        line = LineString([(0.0, 0.0), (10.0, 0.0)])
        line_coords: list[tuple[float, float]] = [(x, y) for x, y, *_ in line.coords]
        seg_ends = cumulative_segment_lengths(line_coords)
        point = Point(5.0, 1.0)
        dist = signed_distance(point, line, line_coords, seg_ends)
        self.assertEqual(dist, 1.0)
