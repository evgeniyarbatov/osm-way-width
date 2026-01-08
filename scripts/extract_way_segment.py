#!/usr/bin/env python3
import json
import sys
import xml.etree.ElementTree as ET

from pyproj import CRS, Transformer
from shapely.geometry import LineString, box, mapping
from shapely.ops import transform


def main() -> int:
    if len(sys.argv) != 6:
        print("usage: extract_way_segment.py INPUT.osm OUTPUT.osm WAY_ID START_NODE_ID END_NODE_ID")
        return 1

    in_path, out_path, way_id, start_node, end_node = sys.argv[1:]

    way_refs = None
    way_tags = []
    way_attribs = None
    in_target_way = False
    for event, elem in ET.iterparse(in_path, events=("start", "end")):
        if event == "start" and elem.tag == "way" and elem.get("id") == way_id:
            in_target_way = True
        elif event == "end" and elem.tag == "way" and elem.get("id") == way_id:
            way_refs = [nd.get("ref") for nd in elem.findall("nd")]
            way_tags = [(tag.get("k"), tag.get("v")) for tag in elem.findall("tag")]
            way_attribs = dict(elem.attrib)
            in_target_way = False
            break

        if event == "end" and not in_target_way:
            elem.clear()

    if way_refs is None:
        print(f"way {way_id} not found")
        return 1

    start_index = way_refs.index(start_node)
    end_index = way_refs.index(end_node)
    if start_index > end_index:
        start_index, end_index = end_index, start_index
    segment_refs = way_refs[start_index : end_index + 1]

    needed_nodes = set(segment_refs)
    node_xml = {}
    node_coords = {}
    for _, elem in ET.iterparse(in_path, events=("end",)):
        if elem.tag == "node" and elem.get("id") in needed_nodes:
            node_xml[elem.get("id")] = ET.tostring(elem, encoding="unicode")
            lat = float(elem.get("lat"))
            lon = float(elem.get("lon"))
            node_coords[elem.get("id")] = (lon, lat)
        elem.clear()

    with open(out_path, "w", encoding="utf-8") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write('<osm version="0.6" generator="extract_way_segment">\n')
        for node_id in segment_refs:
            node = node_xml.get(node_id)
            if node:
                out.write(f"  {node}\n")
        way_attr_text = " ".join(f'{key}="{value}"' for key, value in way_attribs.items())
        out.write(f"  <way {way_attr_text}>\n")
        for ref in segment_refs:
            out.write(f'    <nd ref="{ref}"/>\n')
        for key, value in way_tags:
            out.write(f'    <tag k="{key}" v="{value}"/>\n')
        out.write("  </way>\n")
        out.write("</osm>\n")

    line = LineString([node_coords[ref] for ref in segment_refs])
    centroid = line.centroid
    zone = int((centroid.x + 180) // 6) + 1
    epsg = 32600 + zone if centroid.y >= 0 else 32700 + zone
    wgs84 = CRS.from_epsg(4326)
    utm = CRS.from_epsg(epsg)
    to_utm = Transformer.from_crs(wgs84, utm, always_xy=True)
    to_wgs84 = Transformer.from_crs(utm, wgs84, always_xy=True)
    line_utm = transform(to_utm.transform, line)
    bbox_utm = box(*line_utm.buffer(20).bounds)
    bbox_wgs84 = transform(to_wgs84.transform, bbox_utm)
    geojson = json.dumps(mapping(bbox_wgs84), separators=(",", ":"))
    print(f"bbox_geojson = {geojson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
