"""Easyduino ESP32-S3 case parameters (enclosure-forge target #5).

Rail-class (no holes), DUAL USB-C at the v-max edge. S2 via the
OpenCodeLM pipe; template reused from target #4.
"""

from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(ROOT, "analysis", name)) as f:
        return json.load(f)


GEOM = _load("pcb_geometry.json")
COMPS = _load("component_geometry.json")

BOARD_W = GEOM["outline"]["w"]          # 25.86
BOARD_L = GEOM["outline"]["h"]          # 63.897
BOARD_T = GEOM["thickness"]             # 1.6

WALL_T = 1.6            # enclosure_design_decision
FLOOR_T = 1.6           # enclosure_design_decision
CORNER_R = 2.5          # enclosure_design_decision

PAD_H = 1.8             # enclosure_design_decision
PAD_R = 2.0             # enclosure_design_decision
PADS_UV = [(2.5, 40.0), (23.3, 40.0), (2.5, 52.0), (23.3, 52.0)]  # USBs v>=56.9 clear

RAIL_LIP = 0.8          # enclosure_design_decision
RAIL_T = 1.6            # enclosure_design_decision
RAIL_V0, RAIL_V1 = 20.0, 55.0   # clear of module end + USB zone

RIM_T = 1.0             # enclosure_design_decision
RIM_H = 3.8             # enclosure_design_decision

USB_LIST = [c["u"] for r, c in sorted(COMPS.items())
            if "USB" in c["footprint"].upper()]   # derived_kicad: J1 + J2
USB_PLUG_W = 9.5        # manufacturer_doc class
USB_PLUG_H = 3.5        # manufacturer_doc class
USB_CLEAR = 0.6         # enclosure_design_decision
USB_REACH = 12.0        # enclosure_design_decision

TALLEST = max(c["height"] for c in COMPS.values())
LID_INT_Z = PAD_H + BOARD_T + TALLEST + 1.0

LID_LIP = 1.2           # enclosure_design_decision
LID_GAP = 0.25          # enclosure_design_decision
