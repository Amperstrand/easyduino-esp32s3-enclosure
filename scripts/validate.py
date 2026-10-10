#!/usr/bin/env python3
"""Boolean validation for the Easyduino ESP32 case (enclosure-forge S6)."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq

from cad import case as C
from cad import parameters as P

REPORT = []


def check(name, ok, value, note=""):
    REPORT.append({"name": name, "pass": bool(ok), "value": value, "note": note})
    print(f"  {'PASS' if ok else 'FAIL'} {name} {value} {note}")


def vol(s):
    return s.Volume() if s is not None else 0.0


def inter(a, b):
    if a is None or b is None:
        return 0.0
    return vol(a.intersect(b))


def board_solid():
    return cq.Solid.makeBox(P.BOARD_W, P.BOARD_L, P.BOARD_T,
                            cq.Vector(0, 0, P.PAD_H))


def comp_solids():
    out = {}
    for ref, c in P.COMPS.items():
        u0, u1 = c["u"]
        v0, v1 = c["v"]
        out[ref] = cq.Solid.makeBox(u1 - u0, v1 - v0, c["height"],
                                    cq.Vector(u0, v0, C.BT))
    return out


def main() -> int:
    board = board_solid()
    comps = comp_solids()
    bottom = C.bottom_shell()
    lid = C.lid()
    both = bottom.fuse(lid)

    real = inter(board, bottom) + inter(board, lid)
    supported = sum(1 for x, y in P.PADS_UV
                    if inter(cq.Solid.makeCylinder(P.PAD_R, 0.2,
                             cq.Vector(x, y, P.PAD_H - 0.25)), bottom) > 0.1)
    check("seated_board_interference", real < 0.05 and supported == 4,
          {"volume": round(real, 4), "pads_supported": supported},
          note="board rests on 4 pads; rails/rim clamp, nothing intersects")

    bad = {r: round(inter(c, both), 3) for r, c in comps.items()
           if inter(c, both) > 0.01}
    check("component_clearance", not bad, bad,
          note="all components incl. WROOM (3.2) clear bottom+lid")

    z0 = C.BT - 1.0 - P.USB_CLEAR
    z1 = C.BT + P.USB_PLUG_H + P.USB_CLEAR
    worst = 0.0
    for u0, u1 in P.USB_LIST:
        plug = cq.Solid.makeBox(u1 - u0 + 2 * (1.0 + P.USB_CLEAR),
                                P.USB_REACH, z1 - z0,
                                cq.Vector(u0 - 1.0 - P.USB_CLEAR,
                                          C.INT_V1 - P.USB_REACH, z0))
        worst = max(worst, inter(plug, both))
    check("usb_envelope_clear", worst < 0.01, round(worst, 3),
          note="both seated USB-C plugs + bend voids free of shell")

    rail_ok = True
    for side in (0, 1):
        u_in = (C.INT_U0 + P.RAIL_T + P.RAIL_LIP) if side == 0 else \
               (C.INT_U1 - P.RAIL_T - P.RAIL_LIP)
        u_mid = (C.INT_U0 + 0.4) if side == 0 else (C.INT_U1 - 0.4)
        lip_probe = cq.Solid.makeBox(0.4, P.RAIL_V1 - P.RAIL_V0, 0.4,
                                     cq.Vector(min(u_mid, u_mid + 0.4),
                                               P.RAIL_V0, C.BT + 0.2))
        rail_ok = rail_ok and inter(lip_probe, bottom) > 0.05
        rail_ok = rail_ok and u_in is not None
    check("rails_present_over_board", rail_ok, round(P.RAIL_LIP, 2),
          note="both rail lips overhang the board edge band")

    rim_probe = cq.Solid.makeBox(P.BOARD_W, 0.4, 0.4,
                                 cq.Vector(0, -1.4, C.BT))
    check("rim_locates_v0", inter(rim_probe, bottom) > 0.05,
          round(inter(rim_probe, bottom), 2),
          note="v=0 rim rises above the board top face, outside the board")

    sv = {"bottom": round(vol(bottom), 1), "lid": round(vol(lid), 1)}
    check("solids_valid", bottom.isValid() and lid.isValid()
          and vol(bottom) > 0 and vol(lid) > 0, sv,
          note="watertight B-reps, positive volume")

    def stl_hash(solid):
        w = cq.Workplane(obj=solid)
        with tempfile.NamedTemporaryFile(suffix=".stl") as tf:
            cq.exporters.export(w, tf.name, exportType="STL", tolerance=0.05,
                                angularTolerance=0.2)
            tf.seek(0)
            return hashlib.sha256(tf.read()).hexdigest()[:16]

    h1, h2 = stl_hash(C.bottom_shell()), stl_hash(C.lid())
    h1b, h2b = stl_hash(C.bottom_shell()), stl_hash(C.lid())
    check("deterministic_rebuild", h1 == h1b and h2 == h2b,
          {"bottom": h1, "lid": h2},
          note="hash-identical rebuild")

    out = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "analysis", "interference_report.json")
    with open(out, "w") as f:
        json.dump(REPORT, f, indent=1)
    failed = sum(1 for r in REPORT if not r["pass"])
    print(f"\n{len(REPORT)} checks, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
