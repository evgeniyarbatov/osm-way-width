# GPX OSM Way Width

Width is a useful property of OSM ways. The wider the way, the more pleasant it is for walking. However, width is not know or available in most cases. This is an attempt to use multiple GPX files to approximate width.

## Width estimation workflow

1. Load the OSM way from `osm/way.osm` and build a polyline.
2. Decode all polyline files in `data/polylines` into points.
3. Project everything to a local UTM zone and, for each point, find the closest point on the way polyline.
4. Compute a signed perpendicular distance (positive = left of the way direction, negative = right).
5. Remove GPS noise by discarding points farther than `3 * MAD` from the median signed distance.
6. Estimate width per file as `p95(abs_distance) - p5(abs_distance)`.
7. Aggregate widths across files and report mean/median with a percentile-based confidence interval.

## Outputs

- `data/width_points.csv`: per-point distances, nearest points, and whether the point was kept.
- `data/width_summary.json`: per-file widths plus overall mean/median and confidence interval.

## Run

```
make width
```
