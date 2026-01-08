VENV_PATH := .venv

PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
REQUIREMENTS := requirements.txt

OSM_URL = https://download.geofabrik.de/asia/vietnam-latest.osm.pbf
COUNTRY_OSM_FILE = $$(basename $(OSM_URL))

OSM_DIR = osm
BOUNDARY_POLY = osm/times-city.poly

WAY_ID = 1124683045
WAY_START_NODE = 10284859794
WAY_END_NODE = 10284859797

POLYLINE_DIR = data/polylines
WIDTH_SUMMARY = data/width_summary.json
SEGMENT_LENGTH = 10
WIDTH_SEGMENTS = data/width_segments.csv
WIDTH_SEGMENTS_PNG = data/width_segments.png

venv:
	@python3 -m venv $(VENV_PATH)

install: venv
	@$(PIP) install --disable-pip-version-check -q --upgrade pip
	@$(PIP) install --disable-pip-version-check -q -r $(REQUIREMENTS)

country:
	if [ ! -f $(OSM_DIR)/$(COUNTRY_OSM_FILE) ]; then \
		wget $(OSM_URL) -P $(OSM_DIR); \
	fi

area:
	@osmconvert $(OSM_DIR)/$(COUNTRY_OSM_FILE) -B=$(BOUNDARY_POLY) -o=$(OSM_DIR)/times-city.osm.pbf
	@osmium cat --overwrite $(OSM_DIR)/times-city.osm.pbf -o $(OSM_DIR)/times-city.osm

way:
	@$(PYTHON) scripts/extract_way_segment.py $(OSM_DIR)/times-city.osm $(OSM_DIR)/way.osm $(WAY_ID) $(WAY_START_NODE) $(WAY_END_NODE)

width:
	@$(PYTHON) scripts/estimate_way_width.py $(OSM_DIR)/way.osm $(POLYLINE_DIR) $(WIDTH_SUMMARY)

segments:
	@$(PYTHON) scripts/segment_way_width.py $(OSM_DIR)/way.osm $(POLYLINE_DIR) $(WIDTH_SEGMENTS) $(WIDTH_SEGMENTS_PNG) $(SEGMENT_LENGTH)

test:
	@$(PYTHON) -m unittest discover -s tests
