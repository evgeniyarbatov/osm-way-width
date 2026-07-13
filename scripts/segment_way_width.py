#!/usr/bin/env python3
"""Compute width per segment and render a map image."""

import csv
import math
import sys
from pathlib import Path

import contextily as ctx
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform
from way_width_utils import WayWidthUtils


def signed_distance(point: Point, line: LineString) -> tuple[float, float]:
    # Signed perpendicular distance (positive = left of way direction).
    dist_along = line.project(point)
    nearest = line.interpolate(dist_along)
    delta = min(1.0, line.length / 1000)
    before = line.interpolate(max(0.0, dist_along - delta))
    after = line.interpolate(min(line.length, dist_along + delta))
    dx1 = after.x - before.x
    dy1 = after.y - before.y
    dx2 = point.x - nearest.x
    dy2 = point.y - nearest.y
    cross = dx1 * dy2 - dy1 * dx2
    if cross > 0:
        sign = 1.0
    elif cross < 0:
        sign = -1.0
    else:
        sign = 0.0
    return sign * point.distance(nearest), dist_along


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "usage: segment_way_width.py OSM_WAY.osm POLYLINE_DIR SEGMENT_CSV OUT_PNG SEGMENT_LENGTH_M"
        )
        return 1

    osm_path = Path(sys.argv[1])
    polyline_dir = Path(sys.argv[2])
    segment_csv = Path(sys.argv[3])
    out_png = Path(sys.argv[4])
    segment_length = float(sys.argv[5])

    # Project the way to UTM (for meters) and Web Mercator (for tiles).
    line_wgs84 = WayWidthUtils.read_way_line(osm_path)
    utm = WayWidthUtils.utm_crs(line_wgs84)
    to_utm = Transformer.from_crs(CRS.from_epsg(4326), utm, always_xy=True)
    to_web = Transformer.from_crs(utm, CRS.from_epsg(3857), always_xy=True)
    line_utm = transform(to_utm.transform, line_wgs84)

    total_len = line_utm.length
    segment_count = max(1, math.ceil(total_len / segment_length))
    # Collect signed distances for each segment along the way.
    segments: list[list[float]] = [[] for _ in range(segment_count)]

    for poly_path in sorted(polyline_dir.glob("*.json")):
        polylines = WayWidthUtils.load_polylines(poly_path)
        for points in polylines:
            for lat, lon in points:
                x, y = to_utm.transform(lon, lat)
                signed, dist_along = signed_distance(Point(x, y), line_utm)
                idx = int(dist_along // segment_length)
                if idx >= segment_count:
                    idx = segment_count - 1
                segments[idx].append(signed)

    rows = []
    midpoints = []
    widths = []

    for idx, distances in enumerate(segments):
        start_m = idx * segment_length
        end_m = min(total_len, (idx + 1) * segment_length)
        mid_m = (start_m + end_m) / 2
        mid = line_utm.interpolate(mid_m)
        midpoints.append((mid.x, mid.y))

        if not distances:
            rows.append(
                {
                    "segment_index": idx,
                    "start_m": start_m,
                    "end_m": end_m,
                    "mid_x": mid.x,
                    "mid_y": mid.y,
                    "points_total": 0,
                    "points_kept": 0,
                    "median_signed_m": float("nan"),
                    "mad_m": float("nan"),
                    "p5_abs_m": float("nan"),
                    "p95_abs_m": float("nan"),
                    "width_m": float("nan"),
                }
            )
            widths.append(float("nan"))
            continue

        dist_arr = np.array(distances)
        median = float(np.median(dist_arr))
        mad = float(np.median(np.abs(dist_arr - median)))
        if mad > 0:
            keep_mask = np.abs(dist_arr - median) <= 3 * mad
        else:
            keep_mask = np.ones_like(dist_arr, dtype=bool)

        # Use the 5th-95th percentile range as a robust width estimate.
        kept_abs = np.abs(dist_arr[keep_mask])
        p5, p95 = np.percentile(kept_abs, [5, 95])
        width = float(p95 - p5)

        rows.append(
            {
                "segment_index": idx,
                "start_m": start_m,
                "end_m": end_m,
                "mid_x": mid.x,
                "mid_y": mid.y,
                "points_total": int(len(dist_arr)),
                "points_kept": int(keep_mask.sum()),
                "median_signed_m": median,
                "mad_m": mad,
                "p5_abs_m": float(p5),
                "p95_abs_m": float(p95),
                "width_m": width,
            }
        )
        widths.append(width)

    median_width = float(np.nanmedian(np.array(widths)))
    print(f"median_width_m: {median_width}")

    segment_csv.parent.mkdir(parents=True, exist_ok=True)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    with segment_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Prepare plotting extents with a small buffer in meters.
    line_web = transform(to_web.transform, line_utm)
    minx_utm, miny_utm, maxx_utm, maxy_utm = line_utm.bounds
    buffer_m = 50.0
    minx_utm -= buffer_m
    miny_utm -= buffer_m
    maxx_utm += buffer_m
    maxy_utm += buffer_m
    corners_web = [
        to_web.transform(minx_utm, miny_utm),
        to_web.transform(minx_utm, maxy_utm),
        to_web.transform(maxx_utm, miny_utm),
        to_web.transform(maxx_utm, maxy_utm),
    ]
    minx = min(x for x, _ in corners_web)
    maxx = max(x for x, _ in corners_web)
    miny = min(y for _, y in corners_web)
    maxy = max(y for _, y in corners_web)
    span_x = maxx - minx
    span_y = maxy - miny
    base = 8.0
    if span_x >= span_y:
        fig_w = base
        fig_h = base * (span_y / span_x) if span_x else base
    else:
        fig_h = base
        fig_w = base * (span_x / span_y) if span_y else base
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ctx.add_basemap(
        ax,
        crs="EPSG:3857",
        source=ctx.providers.CartoDB.PositronNoLabels,
        alpha=0.9,
        attribution="",
        attribution_size=0,
        zorder=0,
    )

    line_x, line_y = line_web.xy
    ax.plot(line_x, line_y, color="black", linewidth=2, label="OSM way", zorder=3)

    valid_widths = [width for width in widths if not math.isnan(width) and width > 0]
    vmax = max(valid_widths) if valid_widths else 1.0
    label_positions = []
    for (mid_x, mid_y), width, row in zip(midpoints, widths, rows, strict=False):
        if math.isnan(width) or width == 0:
            continue
        mid_m = (row["start_m"] + row["end_m"]) / 2
        delta = min(1.0, segment_length / 2)
        before = line_utm.interpolate(max(0.0, mid_m - delta))
        after = line_utm.interpolate(min(line_utm.length, mid_m + delta))
        dx = after.x - before.x
        dy = after.y - before.y
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        nx = -dy / length
        ny = dx / length
        half = width / 2
        color = plt.cm.viridis(min(width / vmax, 1.0))
        start_x, start_y = to_web.transform(mid_x - nx * half, mid_y - ny * half)
        end_x, end_y = to_web.transform(mid_x + nx * half, mid_y + ny * half)
        ax.plot(
            [start_x, end_x],
            [start_y, end_y],
            color=color,
            linewidth=3,
            zorder=4,
        )

        label_offset = half + 5.0
        label_x, label_y = to_web.transform(mid_x + nx * label_offset, mid_y + ny * label_offset)
        label_positions.append((label_x, label_y, width))

    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    if label_positions:
        aligned_x = max(pos[0] for pos in label_positions)
        for _, label_y, width in label_positions:
            ax.text(
                aligned_x,
                label_y,
                f"{width:.1f} m",
                fontsize=7,
                ha="left",
                va="center",
                color="black",
                zorder=5,
                bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none", "pad": 1},
            )
    fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
