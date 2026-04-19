"""Re-layout long single-chain flowcharts into a snake/U-shaped grid.

Triggered when the mermaid source is a simple linear chain (A->B->C->...)
with more than 4 nodes. Up to 3 nodes per row, alternating direction:
    row 0: left -> right
    row 1: right -> left   (vertical drop on the right end of row 0)
    row 2: left -> right   (vertical drop on the left end of row 1)
    ...
Node visuals (shape, fill, font) stay exactly as mmdc rendered them; per-row
height and per-column width are unified so cells form a clean grid. The
mmdc-generated edges are dropped and we draw fresh orthogonal connectors.

Uses lxml (not stdlib ElementTree) to preserve the inline `xmlns="..."`
declarations on the xhtml <div> children of <foreignObject>; ElementTree
otherwise rewrites them as `html:div`, which chrome-headless mis-renders.
"""

from __future__ import annotations

import io
import re

from lxml import etree as ET

NAME = "snake_layout"

SVG_NS = "http://www.w3.org/2000/svg"
ROW_SIZE = 3
H_GAP = 60
V_GAP = 50
MARGIN = 20
STROKE = "#9ca3af"
STROKE_WIDTH = 2


# ---------- mermaid source parsing ----------


def _edges_from_mmd(mmd_text: str) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for line in mmd_text.splitlines():
        s = line.strip()
        if not s or s.startswith("%%"):
            continue
        if s.startswith(("classDef", "class ", "flowchart", "graph", "subgraph", "end", "direction")):
            continue
        tokens = re.split(r"\s*-->\s*", s)
        if len(tokens) < 2:
            continue
        cleaned: list[str] = []
        for t in tokens:
            m = re.match(r"([A-Za-z_][\w]*)", t.strip())
            if m:
                cleaned.append(m.group(1))
        for a, b in zip(cleaned, cleaned[1:]):
            edges.append((a, b))
    return edges


def _linear_chain_order(mmd_text: str) -> list[str] | None:
    edges = _edges_from_mmd(mmd_text)
    if not edges:
        return None
    out_deg: dict[str, int] = {}
    in_deg: dict[str, int] = {}
    nodes: set[str] = set()
    for a, b in edges:
        out_deg[a] = out_deg.get(a, 0) + 1
        in_deg[b] = in_deg.get(b, 0) + 1
        nodes.add(a); nodes.add(b)
    if len(edges) != len(nodes) - 1:
        return None
    if any(v > 1 for v in out_deg.values()) or any(v > 1 for v in in_deg.values()):
        return None
    sources = [n for n in nodes if in_deg.get(n, 0) == 0]
    sinks = [n for n in nodes if out_deg.get(n, 0) == 0]
    if len(sources) != 1 or len(sinks) != 1:
        return None
    nxt = dict(edges)
    order = [sources[0]]
    visited = {sources[0]}
    while order[-1] in nxt:
        nx = nxt[order[-1]]
        if nx in visited:
            return None
        order.append(nx); visited.add(nx)
    if set(order) != nodes:
        return None
    return order


# ---------- SVG manipulation ----------


def _node_bbox(g) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for rect in g.iter(f"{{{SVG_NS}}}rect"):
        try:
            x = float(rect.get("x", "0"))
            y = float(rect.get("y", "0"))
            w = float(rect.get("width", "0"))
            h = float(rect.get("height", "0"))
        except (TypeError, ValueError):
            continue
        if w == 0 or h == 0:
            continue
        xs.extend([x, x + w])
        ys.extend([y, y + h])
    if not xs:
        return (0, 0, 0, 0)
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def _resize_node(g, new_w: float, new_h: float) -> None:
    for rect in g.iter(f"{{{SVG_NS}}}rect"):
        cls = rect.get("class", "")
        if "basic" in cls and "label-container" in cls:
            rect.set("x", f"{-new_w / 2:.2f}")
            rect.set("y", f"{-new_h / 2:.2f}")
            rect.set("width", f"{new_w:.2f}")
            rect.set("height", f"{new_h:.2f}")
            break

    for fo in g.iter(f"{{{SVG_NS}}}foreignObject"):
        fo.set("width", f"{new_w:.2f}")
        fo.set("height", f"{new_h:.2f}")
        parent_label = fo.getparent()
        if parent_label is not None:
            parent_label.set("transform", f"translate({-new_w / 2:.2f}, {-new_h / 2:.2f})")
        for div in fo:
            style = div.get("style", "")
            cleaned = re.sub(
                r"(display|white-space|text-align|max-width|width|height)\s*:[^;]*;?",
                "",
                style,
            )
            div.set(
                "style",
                f"display: flex; align-items: center; justify-content: center;"
                f" width: {new_w:.2f}px; height: {new_h:.2f}px;"
                f" text-align: center; {cleaned}".strip(),
            )
            break


def _resolve_nodes(root, order: list[str]) -> dict | None:
    node_elems: dict = {}
    for g in root.iter(f"{{{SVG_NS}}}g"):
        cls = g.get("class", "")
        if "node " not in cls and not (cls == "node" or cls.startswith("node ")):
            continue
        gid = g.get("id", "")
        data_id = g.get("data-id", "")
        for name in order:
            if name in node_elems:
                continue
            if data_id == name:
                node_elems[name] = g; break
            if re.search(rf"(^|[-_]){re.escape(name)}(-\d+)?$", gid):
                node_elems[name] = g; break
    return node_elems if all(n in node_elems for n in order) else None


def _draw_line(parent, x1: float, y1: float, x2: float, y2: float) -> None:
    ln = ET.SubElement(parent, f"{{{SVG_NS}}}line")
    ln.set("x1", f"{x1:.2f}"); ln.set("y1", f"{y1:.2f}")
    ln.set("x2", f"{x2:.2f}"); ln.set("y2", f"{y2:.2f}")
    ln.set("stroke", STROKE); ln.set("stroke-width", str(STROKE_WIDTH))


def _draw_arrow(parent, tx: float, ty: float, direction: str) -> None:
    size = 6
    if direction == "right":
        pts = f"{tx - size},{ty - size} {tx},{ty} {tx - size},{ty + size}"
    elif direction == "left":
        pts = f"{tx + size},{ty - size} {tx},{ty} {tx + size},{ty + size}"
    else:
        pts = f"{tx - size},{ty - size} {tx},{ty} {tx + size},{ty - size}"
    tri = ET.SubElement(parent, f"{{{SVG_NS}}}polygon")
    tri.set("points", pts); tri.set("fill", STROKE)


# ---------- patch interface ----------


def match(mmd: str, svg: str) -> bool:
    order = _linear_chain_order(mmd)
    return order is not None and len(order) > 4


def apply(mmd: str, svg: str) -> str:
    order = _linear_chain_order(mmd)
    if order is None or len(order) <= 4:
        return svg

    tree = ET.parse(io.BytesIO(svg.encode("utf-8")))
    root = tree.getroot()

    node_elems = _resolve_nodes(root, order)
    if node_elems is None:
        return svg

    sizes = {name: _node_bbox(node_elems[name]) for name in order}

    rows: list[list[str]] = []
    for i in range(0, len(order), ROW_SIZE):
        chunk = order[i:i + ROW_SIZE]
        if (i // ROW_SIZE) % 2 == 1:
            chunk = list(reversed(chunk))
        rows.append(chunk)

    col_widths = [0.0] * ROW_SIZE
    for row in rows:
        for visual_col, name in enumerate(row):
            col_widths[visual_col] = max(col_widths[visual_col], sizes[name][2])
    row_heights = [max(sizes[n][3] for n in row) for row in rows]

    col_x = [MARGIN]
    for w in col_widths[:-1]:
        col_x.append(col_x[-1] + w + H_GAP)
    row_y_top = [MARGIN]
    for h in row_heights[:-1]:
        row_y_top.append(row_y_top[-1] + h + V_GAP)

    positions: dict[str, tuple[float, float]] = {}
    uniform_size: dict[str, tuple[float, float]] = {}
    for r, row in enumerate(rows):
        for visual_col, name in enumerate(row):
            cw = col_widths[visual_col]
            rh = row_heights[r]
            cx = col_x[visual_col] + cw / 2
            cy = row_y_top[r] + rh / 2
            positions[name] = (cx, cy)
            uniform_size[name] = (cw, rh)
            node_elems[name].set("transform", f"translate({cx:.2f}, {cy:.2f})")
            _resize_node(node_elems[name], cw, rh)

    sizes = {n: (0, 0, uniform_size[n][0], uniform_size[n][1]) for n in order}

    for parent in list(root.iter()):
        for child in list(parent):
            cls = child.get("class", "")
            if child.tag == f"{{{SVG_NS}}}path" and "flowchart-link" in cls:
                parent.remove(child)
            elif child.tag == f"{{{SVG_NS}}}g" and any(
                k in cls for k in ("edgeLabel", "edgePath", "edgePaths", "edgeLabels")
            ):
                parent.remove(child)

    layer = ET.SubElement(root, f"{{{SVG_NS}}}g")
    layer.set("class", "snake-edges")
    for i in range(len(order) - 1):
        a, b = order[i], order[i + 1]
        ax, ay = positions[a]
        bx, by = positions[b]
        aw, ah = sizes[a][2], sizes[a][3]
        bw, bh = sizes[b][2], sizes[b][3]
        if abs(ay - by) < 1:
            if bx > ax:
                x1 = ax + aw / 2; x2 = bx - bw / 2; dir_ = "right"
            else:
                x1 = ax - aw / 2; x2 = bx + bw / 2; dir_ = "left"
            _draw_line(layer, x1, ay, x2, by)
            _draw_arrow(layer, x2, by, dir_)
        else:
            x1 = ax; y1 = ay + ah / 2
            x2 = bx; y2 = by - bh / 2
            _draw_line(layer, x1, y1, x2, y2)
            _draw_arrow(layer, x2, y2, "down")

    total_w = col_x[-1] + col_widths[-1] + MARGIN
    total_h = row_y_top[-1] + row_heights[-1] + MARGIN
    root.set("viewBox", f"0 0 {total_w:.2f} {total_h:.2f}")
    root.set("width", f"{total_w:.2f}")
    root.set("height", f"{total_h:.2f}")
    style = root.get("style", "")
    if "max-width" in style:
        root.set("style", re.sub(r"max-width:[^;]+;?", "", style).strip())

    return ET.tostring(tree, encoding="unicode")
