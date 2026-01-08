# OSM Way Width

Width is a useful property of OSM ways. This is an attempt to use multiple polylines to approximate width.

<img width="2400" height="808" alt="width_segments" src="https://github.com/user-attachments/assets/23adc72e-b62c-4ec4-981c-2b121b83ff19" />

## Workflow

1. Load the OSM way from `osm/way.osm` and build a polyline.
2. Decode all polyline files in `data/polylines` into points.
3. Project everything to a local UTM zone and, for each point, find the closest point on the way polyline.
4. Compute a signed perpendicular distance (positive = left of the way direction, negative = right).
5. Remove GPS noise by discarding points farther than `3 * MAD` from the median signed distance.
6. Estimate width per file as `p95(abs_distance) - p5(abs_distance)`.
7. Aggregate widths across files and report mean/median with a percentile-based confidence interval.
8. Segment the way into 10 m chunks and compute local widths with the same robust method.
9. Plot the OSM way, local width segments, labels, and an OSM basemap for context.

## Outputs

- `data/width_summary.json`: per-file widths plus overall mean/median, confidence interval, and total polyline count.
- `data/width_segments.csv`: local widths per 10 m segment.
- `data/width_segments.png`: plot of the way, segment widths, labels, and basemap.

## Inputs

- `osm/way.osm`: the target OSM way segment.
- `data/polylines/*.json`: JSON arrays of encoded polylines representing GPX tracks.

## Scripts

- `scripts/extract_way_segment.py`: extracts an OSM way segment into `osm/way.osm` and prints a buffered bbox GeoJSON for GPX collection.
- `scripts/estimate_way_width.py`: computes per-file widths using a MAD filter and percentile width estimate, then writes `data/width_summary.json`.
- `scripts/segment_way_width.py`: computes local widths per segment and renders `data/width_segments.png`.

## Run

Get overall way width:

```
make width
```

Get segment width and make plot:

```
make segments
```
