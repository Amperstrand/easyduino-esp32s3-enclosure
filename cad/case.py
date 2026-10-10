"""Easyduino ESP32 case: pad-and-rail bottom + friction lid (target #4)."""

from __future__ import annotations

import cadquery as cq

from . import parameters as P

INT_U0, INT_U1 = -P.WALL_T, P.BOARD_W + P.WALL_T
INT_V0, INT_V1 = -P.WALL_T, P.BOARD_L + P.WALL_T
LID_Z0 = P.LID_INT_Z
BT = P.PAD_H + P.BOARD_T          # board top face z


def _box(x0, y0, x1, y1, z0, z1):
    if x1 <= x0 or y1 <= y0 or z1 <= z0:
        return None
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _fuse_all(solids):
    out = None
    for s in solids:
        if s is None:
            continue
        out = s if out is None else out.fuse(s)
    return out


def bottom_shell():
    ox0, oy0 = INT_U0 - P.WALL_T, INT_V0 - P.WALL_T
    ox1, oy1 = INT_U1 + P.WALL_T, INT_V1 + P.WALL_T
    cx, cy = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    walls = (
        cq.Workplane("XY", origin=(cx, cy, -P.FLOOR_T))
        .rect(ox1 - ox0, oy1 - oy0).extrude(LID_Z0 + P.FLOOR_T)
        .edges("|Z").fillet(P.CORNER_R)
    ).val()
    solid = walls.cut(_box(INT_U0, INT_V0, INT_U1, INT_V1,
                           -P.FLOOR_T - 0.01, LID_Z0 + 1))
    solid = solid.fuse(_box(INT_U0, INT_V0, INT_U1, INT_V1, -P.FLOOR_T, 0.0))

    parts = []
    for x, y in P.PADS_UV:
        parts.append(cq.Solid.makeCylinder(P.PAD_R, P.PAD_H,
                                           cq.Vector(x, y, 0.0)))
    # friction rails: wall strip outside the board + lip ABOVE the board
    # top face (coincident contact reads 0 mm3; the lip clamps the edge)
    for u_wall in (INT_U0, INT_U1 - P.RAIL_T):
        parts.append(_box(u_wall, P.RAIL_V0, u_wall + P.RAIL_T,
                          P.RAIL_V1, 0.0, BT + P.RAIL_LIP))
    for u_lip0, u_lip1 in ((INT_U0, INT_U0 + P.RAIL_T + P.RAIL_LIP),
                           (INT_U1 - P.RAIL_T - P.RAIL_LIP, INT_U1)):
        parts.append(_box(u_lip0, P.RAIL_V0, u_lip1, P.RAIL_V1,
                          BT, BT + P.RAIL_LIP))
    # v=0 locator rim (full width, plastic ahead of the WROOM antenna)
    parts.append(_box(INT_U0, INT_V0, INT_U1, INT_V0 + P.RIM_T, 0.0, P.RIM_H))
    solid = solid.fuse(_fuse_all(parts))

    # USB-C opening through the v-max wall
    z0 = BT - 1.0 - P.USB_CLEAR
    z1 = BT + P.USB_PLUG_H + P.USB_CLEAR
    for u0, u1 in P.USB_LIST:
        solid = solid.cut(_box(u0 - 1.0 - P.USB_CLEAR, INT_V1 - P.USB_REACH,
                               u1 + 1.0 + P.USB_CLEAR, oy1 + 1, z0, z1))
    return solid


def lid():
    ox0, oy0 = INT_U0 - P.WALL_T, INT_V0 - P.WALL_T
    ox1, oy1 = INT_U1 + P.WALL_T, INT_V1 + P.WALL_T
    cx, cy = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    roof = (
        cq.Workplane("XY", origin=(cx, cy, LID_Z0))
        .rect(ox1 - ox0, oy1 - oy0).extrude(1.6)
        .edges("|Z").fillet(P.CORNER_R)
    ).val()
    lip = _box(INT_U0 + P.LID_GAP, INT_V0 + P.LID_GAP,
               INT_U1 - P.LID_GAP, INT_V1 - P.LID_GAP,
               LID_Z0 - P.LID_LIP, LID_Z0)
    lip = lip.cut(_box(INT_U0 + P.LID_GAP + 1.2, INT_V0 + P.LID_GAP + 1.2,
                       INT_U1 - P.LID_GAP - 1.2, INT_V1 - P.LID_GAP - 1.2,
                       LID_Z0 - P.LID_LIP - 1, LID_Z0 + 1))
    return roof.fuse(lip)
