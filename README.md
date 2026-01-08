# OSM Way Width

These scripts use multiple polylines from Strava running activies to estimate width of a single OSM way.

## Estimated Width (~11 meters)

<img width="2400" height="808" alt="estimated width" src="https://github.com/user-attachments/assets/23adc72e-b62c-4ec4-981c-2b121b83ff19" />

## Actual Width (13 meters)

<img width="1538" height="841" alt="actual width" src="https://github.com/user-attachments/assets/8ea5b3b4-e8fc-4039-9639-093057240b4a" />

## Workflow

1. Load the OSM way from `osm/way.osm` and build a polyline.
2. Decode all polyline files in `data/polylines` into points.
3. Project everything to a local UTM zone and, for each point, find the closest point on the way polyline.
4. Compute a signed perpendicular distance (positive = left of the way direction, negative = right).
5. Remove GPS noise by discarding points farther than `3 * MAD` (median absolute deviation) from the median signed distance.
6. Estimate width per file as `p95(abs_distance) - p5(abs_distance)`.
7. Aggregate widths across files and report mean/median with a percentile-based confidence interval.
8. Segment the way into 10 m chunks and compute local widths with the same method.
9. Plot the OSM way, local width segments, labels, and an OSM basemap for context.

## With Your Own Data

1. Put your encoded polylines in `data/polylines` (`POLYLINE_DIR` in `Makefile`).
   - Each file is JSON containing a list of encoded polylines (Google polyline format).
2. Update the OSM extract settings in `Makefile`.
   - Set `OSM_URL` to your Geofabrik (or other) `.osm.pbf` extract.
   - Replace `BOUNDARY_POLY` with your `.poly` boundary file.
3. Identify the target way segment (I use JOSM) and update `Makefile`.
   - Set `WAY_ID`, `WAY_START_NODE`, and `WAY_END_NODE`.
4. Run the extract pipeline.
   - `make country`
   - `make area`
   - `make way`
5. Run the width calculations.
   - `make width` or `make segments`
