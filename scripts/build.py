#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Style: a collage slide. A light grey canvas with drawn cut-outs that break out of its edges (an old
juniper, an arowana), a pen sketch on top of them, a vertical caption, and a dark column on the right
with a top-down view of a gym and the text set in quotes. Everything is vector, drawn here; nothing
outside the canvas has a background, so the cut-outs sit on GitHub's page in either theme.
"""
import datetime as dt
import json
import math
import os
import random
import re
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


# ------------------------------------------------------------------ shared: pen marks, water, data
MSK = dt.timezone(dt.timedelta(hours=3))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
NIGHT_HOURS = (22, 23, 0, 1, 2, 3)
PIN_NAMES = ("campus", "storagesystem")   # Campus was called StorageSystem before the rename
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]
OLIVE = ["#c9c7bd", "#a9b48a", "#7f8f57", "#56663a", "#2f3b22"]   # empty cell to busiest, juniper greens


def pinned_repo():
    return next(r for r in DATA["repos"] if r["name"].lower() in PIN_NAMES)


def all_langs():
    tot = {}
    for r in CODE_REPOS:
        for k, v in r["langs"].items():
            if k == "Rich Text Format":
                continue
            key = k if k in CODE_LANGS else "Other"
            tot[key] = tot.get(key, 0) + v
    total = sum(tot.values()) or 1
    out = {}
    for k, v in tot.items():
        key = k if (k != "Other" and 100 * v / total >= 4) else "Other"
        out[key] = out.get(key, 0) + v
    return sorted(out.items(), key=lambda kv: (kv[0] == "Other", -kv[1]))


def facts():
    times = sorted(dt.datetime.fromisoformat(c["ts"].replace("Z", "+00:00")).astimezone(MSK)
                   for c in DATA["commits"])
    per_day, hours, by_wd = {}, [0] * 24, [0] * 7
    for m in times:
        per_day[m.date()] = per_day.get(m.date(), 0) + 1
        hours[m.hour] += 1
        by_wd[m.weekday()] += 1
    best = run = 0
    prev = None
    for d in sorted(per_day):
        run = run + 1 if prev and (d - prev).days == 1 else 1
        best, prev = max(best, run), d
    return dict(per_day=per_day, hours=hours, streak=best,
                night=round(100 * sum(hours[h] for h in NIGHT_HOURS) / max(1, len(times))),
                peak=max(range(24), key=lambda h: hours[h]), weekday=WEEKDAYS[max(range(7), key=lambda d: by_wd[d])])


def pen(s, rnd, d_fn, sw=1.4, passes=2, color=INK):
    """Draws a stroke twice with a small tremor, like a quick pen line."""
    for k in range(passes):
        s.path(d_fn(lambda: rnd.uniform(-1.1, 1.1)), "none", color, sw - k * 0.5)


def pen_ring(s, rnd, cx, cy, rx, ry, color=INK):
    """A hand-drawn loop around something, one and a bit turns."""
    pts = []
    start = rnd.uniform(0, math.tau)
    for k in range(44):
        a = start + k / 36 * math.tau
        f = 1 + 0.06 * math.sin(a * 3) + rnd.uniform(-0.02, 0.02)
        pts.append((cx + math.cos(a) * rx * f, cy + math.sin(a) * ry * f))
    s.path("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts), "none", color, 1.3)


def pen_arrow(s, rnd, x0, y0, x1, y1, bend=20, color=INK):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / n * bend, my + dx / n * bend
    pen(s, rnd, lambda j: f"M{x0 + j():.1f} {y0 + j():.1f}Q{cx:.1f} {cy:.1f} {x1:.1f} {y1:.1f}", 1.3, 1, color)
    a = math.atan2(y1 - cy, x1 - cx)
    for da in (2.6, -2.6):
        s.line(x1, y1, x1 + math.cos(a + da) * 9, y1 + math.sin(a + da) * 9, color, 1.3)


def water(s, x, y, w, h, seed=3):
    """Dark water seen from above: a deep gradient and short light wave strokes."""
    rnd = random.Random(seed)
    cid = s.uid("wa")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.rect(x, y, w, h, s.gradient([(0, "#2f4048", 1), (0.5, "#22323a", 1), (1, "#151f24", 1)], 0, 0, 0.3, 1))
    for _ in range(260):
        px, py = rnd.uniform(x - 10, x + w), rnd.uniform(y, y + h)
        ln = rnd.uniform(6, 22)
        s.path(f"M{px:.1f} {py:.1f}q{ln / 2:.1f} {-rnd.uniform(1, 3):.1f} {ln:.1f} 0", "none",
               rnd.choice(("#9fb7bf", "#d9e4e4", "#5f7a84")), rnd.uniform(0.6, 1.4), round(rnd.uniform(0.15, 0.6), 2))
    s.rect(x, y, w, h, "#0c1418", opacity=0.35)
    s.add("</g>")


def column_text(s, tx, y, tw, paras, size=13.5):
    for para in paras:
        for ln in wrap(f"«{para}»", size, tw):
            s.text(tx, y, ln, size, PAPER)
            y += size * 1.5
        y += 16
    return y


def vertical(s, x, y, txt, color=INK):
    s.add(f'<text x="0" y="0" font-size="11" fill="{color}" letter-spacing=".5" text-anchor="middle" '
          f'transform="translate({x} {y}) rotate(-90)">{txt}</text>')


# ------------------------------------------------------------------ slide 2: Campus
def campus_logo_sketch(s, rnd, x, y, size):
    """The Campus logo (Atlas carrying a globe) redrawn as a pen sketch with hatching."""
    src = open(os.path.join(HERE, "icons", "campus.svg"), encoding="utf-8").read()
    grid = re.search(r'id="grid"[^>]*\sd="([^"]+)"', src).group(1)
    figure = re.search(r'id="figure"[^>]*\sd="([^"]+)"', src).group(1)
    k = size / 600
    cid = s.uid("gl")
    s.defs.append(f'<clipPath id="{cid}"><circle cx="347.8" cy="273.1" r="165"/></clipPath>')
    s.g(transform=f"translate({x:.1f} {y:.1f}) scale({k:.4f}) translate(-66 -72)")
    s.add(f'<circle cx="347.8" cy="273.1" r="165" fill="{PAPER}"/>')
    s.add(f'<g clip-path="url(#{cid})">')
    for i in range(-20, 40):          # shading on the lower right of the globe
        x0 = 200 + i * 12
        s.add(f'<line x1="{x0}" y1="480" x2="{x0 + 260}" y2="220" stroke="{INK}" stroke-width="2.4" opacity=".55"/>')
    s.add(f'<circle cx="300" cy="225" r="150" fill="{PAPER}"/>')
    s.add("</g>")
    for dx, dy, sw in ((0, 0, 5), (3, -2, 2.6)):
        s.add(f'<circle cx="{347.8 + dx}" cy="{273.1 + dy}" r="165" fill="none" stroke="{INK}" stroke-width="{sw}"/>')
    s.add(f'<path d="{grid}" clip-path="url(#{cid})" fill="none" stroke="{INK}" stroke-width="3.2"/>')
    s.add(f'<path d="{figure}" fill="{CANVAS}" stroke="{INK}" stroke-width="5"/>')
    s.add(f'<path d="{figure}" fill="none" stroke="{INK}" stroke-width="2.4" transform="translate(4 -3)" opacity=".6"/>')
    s.add(f'<circle cx="503.5" cy="390" r="9" fill="{INK}"/>')
    s.end()


def campus():
    H = 450
    r = pinned_repo()
    pin = DATA.get("pin") or {}
    rnd = random.Random(31)
    # arrows land on the drawing: around the globe, then down the figure
    notes = [(pin.get("java"), "Java classes", (470, 64)), (pin.get("svelte"), "Svelte components", (494, 120)),
             (pin.get("tests"), "test files", (498, 186)), (pin.get("migrations"), "database migrations", (462, 228)),
             (pin.get("screens"), "screens", (440, 286)), (pin.get("versions"), "versions shipped", (392, 318))]
    notes = [n for n in notes if n[0]]
    s = Svg(W, H, f"Campus, the pinned project: a study-group site and app that lives on the group leader's own "
            f"computer. {r.get('release') or ''}, {r['commits']} commits, "
            + ", ".join(f"{v} {lab}" for v, lab, _ in notes) + ".",
            "The Campus logo, Atlas carrying a globe, drawn as a pen sketch on a grey canvas, with hand-drawn arrows "
            "to the project's numbers, and a column of dark water with the text.")
    col_w = 252
    s.rect(col_w - 16, 60, 600, H - 110, CANVAS)
    campus_logo_sketch(s, rnd, 248, 8, 330)
    for i, (v, lab, (ax, ay)) in enumerate(notes):
        ty = 104 + i * 50
        s.text(620, ty, str(v), 24, INK, 700)
        s.text(620 + text_width(24, str(v)) + 10, ty, lab, 12, INK)
        pen_arrow(s, rnd, 612, ty - 8, ax, ay, bend=10 if i % 2 else -10)
    vertical(s, col_w - 16 + 600 - 12, 230, "pinned project · github.com/mitaro-cs/Campus")
    water(s, 0, 0, col_w, H)
    tx, tw = 26, col_w - 48
    s.text(tx, 52, "CAMPUS", 13, PAPER, 700, ls=3)
    s.text(tx, 72, f"{r.get('release') or 'in progress'} · {r['commits']} commits · AGPL-3.0", 10.5, "#c9c6bb")
    column_text(s, tx, 128, tw, ["A site and an app for one study group: homework, a schedule, news and files.",
                                 "It runs on the group leader's computer. Every phone keeps a copy and syncs "
                                 "when the host is back on."], 12.5)
    s.text(tx, H - 34, "Windows · macOS · iPhone · Android", 10.5, "#c9c6bb")
    return s


# ------------------------------------------------------------------ slide 3: when I commit
def activity():
    H = 420
    f = facts()
    rnd = random.Random(17)
    langs = all_langs()
    repos = DATA["repos"]
    kb = sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k != "Rich Text Format") // 1000
    nums = [("repositories", len(repos)), ("commits", sum(r["commits"] for r in repos)),
            ("stars", sum(r["stars"] for r in repos)), ("followers", DATA["followers"]),
            ("of code", f"{kb / 1000:.1f} MB" if kb >= 1000 else f"{kb} KB")]
    s = Svg(W, H, "When I commit: 26 weeks of commits per day, commits by hour in Moscow time, and my numbers on "
            f"GitHub. Longest streak {f['streak']} days, peak hour {f['peak']:02d}:00, {f['night']}% after 22:00.",
            "A grey canvas with a heatmap and an hourly bar chart in juniper greens, pen notes on the busiest spots, "
            "and a dark column with the totals and languages.")
    cx0, cy0, cw, ch = 30, 46, 620, 330
    s.rect(cx0, cy0, cw, ch, CANVAS)
    s.text(cx0 + 30, cy0 + 40, "when I commit", 20, INK, 700)
    s.text(cx0 + 30, cy0 + 60, "Moscow time · last 26 weeks", 11, "#55574f")

    weeks, cell, gap = 26, 12, 3
    today = dt.datetime.now(MSK).date()
    start = today - dt.timedelta(days=today.weekday() + 7 * (weeks - 1))
    hx, hy = cx0 + 30, cy0 + 82
    busiest = None
    for w in range(weeks):
        for d in range(7):
            day = start + dt.timedelta(days=7 * w + d)
            if day > today:
                continue
            n = f["per_day"].get(day, 0)
            x, y = hx + w * (cell + gap), hy + d * (cell + gap)
            s.rect(x, y, cell, cell, OLIVE[0 if not n else 1 + (n >= 3) + (n >= 6) + (n >= 10)], rx=2)
            if n and (busiest is None or n > busiest[0]):
                busiest = (n, x + cell / 2, y + cell / 2, day)
    if busiest:
        pen_ring(s, rnd, busiest[1], busiest[2], 16, 14)
        bx = hx + weeks * (cell + gap) + 18
        pen_arrow(s, rnd, bx + 4, hy + 6, busiest[1] + 12, busiest[2] - 10, bend=-16)
        s.text(bx + 8, hy + 10, f"{busiest[0]} commits", 13, INK, 700)
        s.text(bx + 8, hy + 26, f"on {busiest[3].day} {MONTHS[busiest[3].month - 1]}", 11, "#55574f")
        s.text(bx + 8, hy + 58, f"{f['streak']}-day streak", 13, INK, 700)
        s.text(bx + 8, hy + 74, f"busiest: {f['weekday']}", 11, "#55574f")

    # by hour: pen-hatched bars, night hours in ink
    bx0, by0, bw, bh = hx, cy0 + 214, weeks * (cell + gap) - gap, 80
    top = max(f["hours"]) or 1
    slot = bw / 24
    for h, n in enumerate(f["hours"]):
        hgt = max(2.0, bh * n / top)
        x = bx0 + h * slot
        night = h in NIGHT_HOURS
        s.rect(x + 1, by0 + bh - hgt, slot - 3, hgt, INK if night else "#7f8f57", opacity=0.85 if night else 0.9)
    s.line(bx0, by0 + bh + 1, bx0 + bw, by0 + bh + 1, INK, 1.2)
    for h in (0, 6, 12, 18, 23):
        s.text(bx0 + h * slot + (slot if h == 23 else 0), by0 + bh + 16, f"{h:02d}", 10.5, "#55574f",
               anchor="end" if h == 23 else "start")
    px = bx0 + f["peak"] * slot + slot / 2
    nx = bx0 + bw + 18
    pen_arrow(s, rnd, nx + 4, by0 + 10, px + 4, by0 + 2, bend=18)
    s.text(nx + 8, by0 + 14, f"peak {f['peak']:02d}:00", 13, INK, 700)
    pen_arrow(s, rnd, nx + 4, by0 + 52, bx0 + bw - slot, by0 + bh - 30, bend=-10)
    s.text(nx + 8, by0 + 56, f"{f['night']}% after 22:00", 13, INK, 700)
    vertical(s, cx0 + cw - 12, cy0 + ch / 2, "data: GitHub API · refreshed every 6 hours")

    col_x = 640
    water(s, col_x, 0, W - col_x, H, seed=9)
    tx = col_x + 26
    s.text(tx, 52, "ON GITHUB", 13, PAPER, 700, ls=3)
    for i, (lab, v) in enumerate(nums):
        y = 96 + i * 36
        s.text(tx, y, str(v), 22, PAPER, 700)
        s.text(tx + text_width(22, str(v)) + 10, y, lab, 11.5, "#c9c6bb")
    total = sum(v for _, v in langs) or 1
    y = 96 + len(nums) * 36 + 6
    s.text(tx, y, "LANGUAGES", 11, PAPER, 700, ls=2)
    for i, (k, v) in enumerate(langs[:6]):
        yy = y + 22 + i * 18
        s.text(tx, yy, k, 11.5, PAPER)
        s.text(W - 26, yy, f"{round(100 * v / total)}%", 11.5, "#c9c6bb", anchor="end")
    return s


if __name__ == "__main__":
    hero().save(OUT, "hero.svg")
    campus().save(OUT, "campus.svg")
    activity().save(OUT, "activity.svg")
