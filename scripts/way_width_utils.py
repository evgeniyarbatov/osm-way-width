import json
import xml.etree.ElementTree as ET
from pathlib import Path

import polyline
from pyproj import CRS, Transformer
from shapely.geometry import LineString


class WayWidthUtils:
    @staticmethod
    def read_way_line(path: Path) -> LineString:
        # Load the target way as a LineString in WGS84.
        tree = ET.parse(path)
        root = tree.getroot()
        nodes = {
            node.get("id"): (float(node.get("lon")), float(node.get("lat")))
            for node in root.findall("node")
        }
        way = root.find("way")
        refs = [nd.get("ref") for nd in way.findall("nd")]
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
