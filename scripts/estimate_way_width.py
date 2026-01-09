#!/usr/bin/env python3
import bisect
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import transform

from way_width_utils import WayWidthUtils

MAD_MULTIPLIER = 3
WIDTH_PERCENTILES = (5, 95)
CONFIDENCE_INTERVAL_PERCENTILES = (2.5, 97.5)


def cumulative_segment_lengths(coords: list[tuple[float, float]]) -> list[float]:
    # Track cumulative distances so we can map a projected point to its segment.
    total = 0.0
    totals = []
    for start, end in zip(coords, coords[1:]):
        seg_len = math.hypot(end[0] - start[0], end[1] - start[1])
        total += seg_len
        totals.append(total)
    return totals


def signed_distance(
    point: Point,
    line: LineString,
    line_coords: list[tuple[float, float]],
    seg_ends: list[float],
) -> float:
    # Compute signed perpendicular distance (positive = left of way direction).
    dist_along = line.project(point)
    nearest = line.interpolate(dist_along)
    idx = bisect.bisect_left(seg_ends, dist_along)
    if idx >= len(seg_ends):
        idx = len(seg_ends) - 1
    start = line_coords[idx]
    end = line_coords[idx + 1]
    dx1 = end[0] - start[0]
    dy1 = end[1] - start[1]
    dx2 = point.x - nearest.x
    dy2 = point.y - nearest.y
    cross = dx1 * dy2 - dy1 * dx2
    if cross > 0:
        sign = 1.0
    elif cross < 0:
        sign = -1.0
    else:
        sign = 0.0
    return sign * point.distance(nearest)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: estimate_way_width.py OSM_WAY.osm POLYLINE_DIR")
        return 1

    osm_path = Path(sys.argv[1])
    polyline_dir = Path(sys.argv[2])
    # Project the OSM way to a local UTM zone for metric calculations.
    line_wgs84 = WayWidthUtils.read_way_line(osm_path)
    to_utm = WayWidthUtils.utm_transformer(line_wgs84)
    line_utm = transform(to_utm.transform, line_wgs84)
    line_coords = list(line_utm.coords)
    seg_ends = cumulative_segment_lengths(line_coords)

    widths = []
    polylines_used = 0

    # Compute a width estimate for each file, then aggregate across files.
    for poly_path in sorted(polyline_dir.glob("*.json")):
        distances = []
        polylines = WayWidthUtils.load_polylines(poly_path)
        polylines_used += len(polylines)
        for points in polylines:
            for lat, lon in points:
                x, y = to_utm.transform(lon, lat)
                point_utm = Point(x, y)
                distances.append(signed_distance(point_utm, line_utm, line_coords, seg_ends))

        # Keep points within MAD_MULTIPLIER * MAD, then estimate width from percentiles.
        dist_arr = np.array(distances)
        median = float(np.median(dist_arr))
        mad = float(np.median(np.abs(dist_arr - median)))
        if mad > 0:
            keep_mask = np.abs(dist_arr - median) <= MAD_MULTIPLIER * mad
        else:
            keep_mask = np.ones_like(dist_arr, dtype=bool)

        kept_abs = np.abs(dist_arr[keep_mask])
        low, high = np.percentile(kept_abs, WIDTH_PERCENTILES)
        width = float(high - low)
        widths.append(width)

    widths_arr = np.array(widths)
    ci_low, ci_high = np.percentile(widths_arr, CONFIDENCE_INTERVAL_PERCENTILES)
    summary = {
        "overall": {
            "files_used": int(len(widths_arr)),
            "polylines_used": int(polylines_used),
            "width_mean_m": float(np.mean(widths_arr)),
            "width_median_m": float(np.median(widths_arr)),
            "width_ci_low_m": float(ci_low),
            "width_ci_high_m": float(ci_high),
        },
    }

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
