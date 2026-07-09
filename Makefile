# Uses uv (https://docs.astral.sh/uv) for dependency management — uv sync creates/updates .venv; run commands via uv run, no manual activation.

PYTHON := uv run python

OSM_URL = https://download.geofabrik.de/asia/vietnam-latest.osm.pbf
include $(HOME)/gitRepo/dotfiles/make/osm-country.mk

OSM_DIR = osm
BOUNDARY_POLY = osm/times-city.poly

WAY_ID = 1124683045
WAY_START_NODE = 10284859794
WAY_END_NODE = 10284859797

POLYLINE_DIR = data/polylines
SEGMENT_LENGTH = 10
WIDTH_SEGMENTS = data/width_segments.csv
WIDTH_SEGMENTS_PNG = data/width_segments.png

install:
	@uv sync

lock:
	@uv lock

area:
	@osmconvert $(OSM_DIR)/$(COUNTRY_OSM_FILE) -B=$(BOUNDARY_POLY) -o=$(OSM_DIR)/times-city.osm.pbf
	@osmium cat --overwrite $(OSM_DIR)/times-city.osm.pbf -o $(OSM_DIR)/times-city.osm

way: install
	@$(PYTHON) scripts/extract_way_segment.py $(OSM_DIR)/times-city.osm $(OSM_DIR)/way.osm $(WAY_ID) $(WAY_START_NODE) $(WAY_END_NODE)

width: install
	@$(PYTHON) scripts/estimate_way_width.py $(OSM_DIR)/way.osm $(POLYLINE_DIR)

segments: install
	@$(PYTHON) scripts/segment_way_width.py $(OSM_DIR)/way.osm $(POLYLINE_DIR) $(WIDTH_SEGMENTS) $(WIDTH_SEGMENTS_PNG) $(SEGMENT_LENGTH)

test: install
	@$(PYTHON) -m unittest discover -s tests

help:
	@echo "install   - uv sync (create/update .venv and install deps)"
	@echo "lock      - uv lock (refresh uv.lock)"
	@echo "area      - clip OSM extract to the boundary polygon"
	@echo "way       - extract a single way segment"
	@echo "width     - estimate way width along the polyline"
	@echo "segments  - segment way width estimates and plot"
	@echo "test      - run unit tests"
