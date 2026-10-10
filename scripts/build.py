#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Style: a collage slide. A light grey canvas with drawn cut-outs that break out of its edges (an old
juniper, an arowana), a pen sketch on top of them, a vertical caption, and a dark column on the right
with a top-down view of a gym and the text set in quotes. Everything is vector, drawn here; nothing
outside the canvas has a background, so the cut-outs sit on GitHub's page in either theme.
"""
import json
import math
import os
import random
import sys

from lib import Svg, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
W = 888

CANVAS = "#dddcd8"
INK = "#1d1f1c"
PAPER = "#f1efe8"


def wrap(txt, size, maxw):
    lines, cur = [], ""
    for wd in txt.split():
        t = (cur + " " + wd).strip()
        if text_width(size, t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    return lines + [cur]


def ribbon(center, widths):
    """Polygon around a polyline: the left edge up, the right edge back down."""
    left, right = [], []
    for i, ((x, y), w) in enumerate(zip(center, widths)):
        (x0, y0), (x1, y1) = center[max(0, i - 1)], center[min(len(center) - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in left + right[::-1]) + "Z"


def smooth(points, steps=8):
    """Catmull-Rom through the points, returned as a dense polyline."""
    out = []
    p = [points[0]] + points + [points[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(points[-1])
    return out


# ------------------------------------------------------------------ the juniper
def foliage(s, rnd, cx, cy, rx, ry, n):
    """A juniper pad: hundreds of small needle tufts, lit from the top left."""
    s.add(f'<ellipse cx="{cx}" cy="{cy + ry * 0.25:.1f}" rx="{rx * 0.92:.1f}" ry="{ry * 0.7:.1f}" fill="#2a3420" '
          f'opacity=".85"/>')
    for _ in range(n):
        a = rnd.uniform(0, math.tau)
        rr = math.sqrt(rnd.random())
        x, y = cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr
        light = (cy - y) / ry * 0.6 + (cx - x) / rx * 0.25 + rnd.uniform(-0.35, 0.35)
        col = "#879a5c" if light > 0.45 else "#64773f" if light > 0.05 else "#46572f" if light > -0.4 else "#2f3b22"
        r = rnd.uniform(2.2, 5.2)
        s.add(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r:.1f}" ry="{r * 0.55:.1f}" fill="{col}" '
              f'transform="rotate({rnd.uniform(-60, 60):.0f} {x:.1f} {y:.1f})"/>')


def juniper(s):
    rnd = random.Random(21)
    trunk = smooth([(352, 500), (330, 440), (312, 380), (338, 318), (318, 262), (300, 214), (316, 168), (296, 128)])
    widths = [200 - 168 * (i / (len(trunk) - 1)) ** 0.8 for i in range(len(trunk))]
    # branches first, so the trunk covers their roots
    branches = [([(318, 262), (270, 236), (226, 226), (186, 214)], 26),
                ([(300, 214), (338, 170), (380, 148), (408, 132)], 20),
                ([(316, 168), (300, 120), (288, 84), (276, 58)], 18),
                ([(338, 318), (392, 296), (430, 268), (452, 236)], 16),
                ([(312, 380), (252, 360), (210, 330)], 14)]
    for pts, w in branches:
        line = smooth(pts, 6)
        s.path(ribbon(line, [w * (1 - 0.65 * i / (len(line) - 1)) for i in range(len(line))]), "#6d6652")
        s.path(ribbon(line, [w * 0.35 * (1 - 0.6 * i / (len(line) - 1)) for i in range(len(line))]), "#a39b7c",
               opacity=0.6)
    for cx, cy, rx, ry, n in ((176, 208, 70, 34, 260), (214, 324, 44, 22, 120), (404, 118, 64, 34, 240),
                              (268, 44, 74, 40, 300), (456, 226, 46, 24, 140), (330, 96, 40, 22, 120)):
        foliage(s, rnd, cx, cy, rx, ry, n)
    # the trunk: a lit side, a shaded side, and bark that twists with it
    s.path(ribbon(trunk, widths), s.gradient([(0, "#c9c1a2", 1), (0.45, "#8c8466", 1), (1, "#3f3a2e", 1)], 0, 0, 1, 0))
    for _ in range(70):
        u = rnd.uniform(-0.95, 0.95)
        phase, amp = rnd.uniform(0, math.tau), rnd.uniform(0.05, 0.18)
        pts = []
        for i in range(len(trunk)):
            (x0, y0), (x1, y1) = trunk[max(0, i - 1)], trunk[min(len(trunk) - 1, i + 1)]
            dx, dy = x1 - x0, y1 - y0
            n = math.hypot(dx, dy) or 1
            off = (u + amp * math.sin(i / 5 + phase)) * widths[i] / 2
            pts.append((trunk[i][0] - dy / n * off, trunk[i][1] + dx / n * off))
        a, b = sorted((rnd.randint(0, len(pts) - 1), rnd.randint(0, len(pts) - 1)))
        seg = pts[a:b + 6]
        if len(seg) < 3:
            continue
        col = "#e3dcc0" if u > 0.25 and rnd.random() < 0.6 else "#2e2a21"
        s.path("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in seg), "none", col, rnd.uniform(0.8, 3.2),
               round(rnd.uniform(0.25, 0.7), 2))
    for x, y, rx, ry in ((322, 300, 12, 18), (306, 222, 8, 12), (340, 410, 16, 10)):
        s.add(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#2e2a21" opacity=".7"/>')
        s.add(f'<ellipse cx="{x - 2}" cy="{y - 2}" rx="{rx * 0.55:.1f}" ry="{ry * 0.55:.1f}" fill="#b8b090" opacity=".5"/>')


# ------------------------------------------------------------------ the fish
def arowana(s):
    """A silver arowana swimming in from the left edge, scales and all."""
    s.g(transform="translate(-6 118) rotate(-4)")
    body = "M0 30C40 4 120 -6 196 6C214 9 226 20 230 30C226 42 210 52 190 56C120 66 40 58 0 44Z"
    s.path(body, s.gradient([(0, "#c4ccc2", 1), (0.45, "#8e9a8c", 1), (0.75, "#4f5c52", 1), (1, "#2c352f", 1)],
                            0, 0, 0, 1))
    cid = s.uid("fb")
    s.defs.append(f'<clipPath id="{cid}"><path d="{body}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    for row in range(5):
        for col in range(14):
            x, y = 14 + col * 13 + (row % 2) * 6.5, 10 + row * 10
            s.path(f"M{x - 6} {y}C{x - 6} {y + 7} {x + 6} {y + 7} {x + 6} {y}", "none", "#e8eee6", 1, 0.45)
            s.path(f"M{x - 6} {y + 1}C{x - 6} {y + 8} {x + 6} {y + 8} {x + 6} {y + 1}", "none", "#26302b", 0.8, 0.35)
    s.add("</g>")
    s.path("M168 8C186 10 204 16 218 26C222 34 220 44 210 50C196 54 180 54 170 50C176 36 176 20 168 8Z", "#3a4540",
           opacity=0.75)
    s.path("M171 14C174 26 174 40 168 52", "none", "#1d221f", 1.4, 0.8)
    s.circle(198, 26, 7.5, "#d9d4c4")
    s.circle(199, 26, 4.2, "#121512")
    s.circle(197, 24, 1.4, "#ffffff")
    s.path("M222 22C228 18 234 18 238 22", "none", "#1d221f", 1.6)
    s.path("M200 52C190 66 176 72 164 70C172 62 180 56 190 54Z", "#4a5650")
    s.end()


def sketch_fish(s, x, y):
    """A quick pen drawing over the trunk: outline, gill, eye, fin strokes."""
    rnd = random.Random(4)

    def j():
        return rnd.uniform(-1.2, 1.2)   # a small hand tremor

    s.g(transform=f"translate({x} {y}) rotate(14)")
    for k in range(2):
        s.path(f"M{j()} {16 + j()}C{30 + j()} {-8 + j()} {96 + j()} {-10 + j()} {126 + j()} {14 + j()}"
               f"C{96 + j()} {38 + j()} {30 + j()} {40 + j()} {j()} {16 + j()}", "none", INK, 1.5 - k * 0.5)
    s.path("M0 16L-26 0L-20 16L-26 34Z", "none", INK, 1.4)
    s.path("M98 2C92 12 92 22 98 32", "none", INK, 1.3)
    s.circle(110, 12, 3.2, "none", extra=f'stroke="{INK}" stroke-width="1.3"')
    s.circle(110, 12, 1, INK)
    s.path("M124 16L134 18", "none", INK, 1.3)
    s.path("M40 -2C52 -18 70 -20 82 -6", "none", INK, 1.3)
    for k in range(6):
        s.path(f"M{46 + k * 6} {-6 - (k % 2) * 2}L{50 + k * 6} {-14 + (k % 3)}", "none", INK, 1)
    s.path("M50 34C56 46 68 48 74 38", "none", INK, 1.3)
    for k in range(9):
        s.path(f"M{14 + k * 9} {10 + (k % 2)}C{17 + k * 9} 14 {17 + k * 9} 20 {14 + k * 9} {24 - (k % 2)}",
               "none", INK, 0.8, 0.8)
    s.end()


# ------------------------------------------------------------------ the dark column: a gym seen from above
def gym(s, x, y, w, h):
    rnd = random.Random(8)
    cid = s.uid("gy")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.rect(x, y, w, h, s.gradient([(0, "#4a554d", 1), (0.6, "#3a453f", 1), (1, "#2a332f", 1)], 0, 0, 0.4, 1))
    court = "#b5644e"
    s.circle(x + w * 0.42, y + h * 0.52, 46, "none", extra=f'stroke="{court}" stroke-width="3" opacity=".7"')
    s.circle(x + w * 0.42, y + h * 0.52, 46, court, 0.18)
    s.add(f'<path d="M{x - 20} {y + h * 0.18}Q{x + w * 0.5} {y + h * 0.05} {x + w + 20} {y + h * 0.22}" fill="none" '
          f'stroke="{court}" stroke-width="3" opacity=".6"/>')
    s.add(f'<path d="M{x - 20} {y + h * 0.86}Q{x + w * 0.5} {y + h * 0.74} {x + w + 20} {y + h * 0.9}" fill="none" '
          f'stroke="#d8d4c6" stroke-width="2" opacity=".35"/>')
    s.line(x, y + h * 0.52, x + w, y + h * 0.52, "#d8d4c6", 2, 0.3)
    for _ in range(46):
        px, py = rnd.uniform(x - 10, x + w + 10), rnd.uniform(y, y + h)
        sh = rnd.uniform(16, 30)
        s.add(f'<ellipse cx="{px + sh * 0.6:.1f}" cy="{py + sh * 0.35:.1f}" rx="{sh:.1f}" ry="3.2" fill="#0e1311" '
              f'opacity=".45" transform="rotate(28 {px:.1f} {py:.1f})"/>')
        s.add(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="5.5" ry="4" '
              f'fill="{rnd.choice(("#1c2220", "#2b2a2d", "#4b3b36", "#d6d2c6"))}"/>')
        s.circle(px, py - 1, 2.6, rnd.choice(("#151816", "#3a2d27", "#7a6450")))
    s.rect(x, y, w, h, "#10171a", opacity=0.55)
    s.add("</g>")


# ------------------------------------------------------------------ the hero slide
TEXT = [  # a draft; the idea for this column is still being decided
    "A study group should not need someone else's server.",
    "Campus lives on the group leader's own computer, and the data stays with the people who wrote it.",
]


def hero():
    H = 480
    cx0, cy0, cx1, cy1 = 70, 70, 650, 430
    col_x = 640
    s = Svg(W, H, "Mitaro. Omar, computer science student at MTUCI. Campus: a study-group app that lives on the "
            "group leader's own computer.", "A collage: an old juniper and an arowana breaking out of a grey "
            "canvas, a pen sketch of a fish over the trunk, and a dark column with a top-down gym and the text.")
    s.rect(cx0, cy0, cx1 - cx0, cy1 - cy0, CANVAS)
    juniper(s)
    sketch_fish(s, 300, 300)
    s.add(f'<text x="0" y="0" font-size="11" fill="{INK}" letter-spacing=".5" text-anchor="middle" '
          f'transform="translate({col_x - 14} 250) rotate(-90)">Campus — local-first software for study groups</text>')
    gym(s, col_x, 0, W - col_x, H)
    arowana(s)

    tx, tw = col_x + 26, W - col_x - 48
    s.text(tx, 52, "MITARO", 13, PAPER, 700, ls=3)
    s.text(tx, 72, "Omar · CS @ MTUCI", 11.5, "#c9c6bb")
    y = 150
    for para in TEXT:
        for ln in wrap(f"«{para}»", 14, tw):
            s.text(tx, y, ln, 14, PAPER)
            y += 21
        y += 18
    return s


if __name__ == "__main__":
    hero().save(OUT, "hero.svg")
