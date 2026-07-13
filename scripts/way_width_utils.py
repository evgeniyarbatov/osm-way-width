import json
from pathlib import Path

import defusedxml.ElementTree as ET
import polyline
from pyproj import CRS, Transformer
from shapely.geometry import LineString


class WayWidthUtils:
    @staticmethod
    def read_way_line(path: Path) -> LineString:
        # Load the target way as a LineString in WGS84.
        tree = ET.parse(path)
        root = tree.getroot()
        nodes: dict[str, tuple[float, float]] = {}
        for node in root.findall("node"):
            node_id, lon, lat = node.get("id"), node.get("lon"), node.get("lat")
            if node_id is None or lon is None or lat is None:
                raise ValueError(f"malformed <node> element in {path}")
            nodes[node_id] = (float(lon), float(lat))

        way = root.find("way")
        if way is None:
            raise ValueError(f"no <way> element found in {path}")
        refs = []
        for nd in way.findall("nd"):
            ref = nd.get("ref")
            if ref is None:
                raise ValueError(f"malformed <nd> element in {path}")
            refs.append(ref)
        coords = [nodes[ref] for ref in refs]
        return LineString(coords)

    @staticmethod
    def utm_crs(line: LineString) -> CRS:
        # Pick a local UTM CRS based on the line centroid.
        centroid = line.centroid
        zone = int((centroid.x + 180) // 6) + 1
        epsg = 32600 + zone if centroid.y >= 0 else 32700 + zone
        return CRS.from_epsg(epsg)

    @staticmethod
    def utm_transformer(line: LineString) -> Transformer:
        return Transformer.from_crs(
            CRS.from_epsg(4326), WayWidthUtils.utm_crs(line), always_xy=True
        )

    @staticmethod
    def load_polylines(path: Path) -> list[list[tuple[float, float]]]:
        # Each JSON file is a list of encoded polylines.
        encoded = json.loads(path.read_text(encoding="utf-8"))
        return [polyline.decode(item) for item in encoded]
