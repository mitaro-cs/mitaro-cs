#!/usr/bin/env python3
"""Builds every SVG of the profile README into ../assets from scripts/data.json.

Style: an early-80s mission-control collage. Black glass, magenta frames, cyan grids, amber line
charts that glow, CRT monitors, and a starburst sun over a night ocean. Every chart is real data
from data.json: commits per day and week, commits by hour, cumulative commits per repository,
languages, and the pinned Campus project. The panels carry their own black background, so they read
the same on GitHub's light and dark themes. Text uses the system monospace font.
"""
import datetime as dt
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

BLACK = "#000000"
MAGENTA = "#e0479e"
PINK = "#ff6fb5"
CYAN = "#38c6ff"
BLUE = "#2a5cff"
NAVY = "#16306b"
AMBER = "#ffa63d"
YELLOW = "#ffd84a"
RED = "#ff3b30"
LAVENDER = "#b9a6ff"
GREEN = "#7be08a"
CREAM = "#f4ead0"
GREY = "#8a8aa0"
LANG_COLOR = {"Java": AMBER, "Svelte": PINK, "Python": CYAN, "TypeScript": LAVENDER, "JavaScript": YELLOW,
              "CSS": GREEN, "HTML": RED, "Other": GREY}
LINE_COLORS = [YELLOW, PINK, CYAN, GREEN, LAVENDER]

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MSK = dt.timezone(dt.timedelta(hours=3))
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]
NOT_CODE = {"Rich Text Format"}
PIN_NAMES = ("campus", "storagesystem")   # Campus was called StorageSystem before the rename
REPO_NAMES = {"campus": "CAMPUS", "storagesystem": "CAMPUS", "kworkingsystem": "KWORKING"}


# ------------------------------------------------------------------ data helpers
def pinned_repo():
    return next(r for r in DATA["repos"] if r["name"].lower() in PIN_NAMES)


def bucket_langs(langs, min_pct):
    tot = {}
    for k, v in langs.items():
        if k in NOT_CODE:
            continue
        key = k if k in CODE_LANGS else "Other"
        tot[key] = tot.get(key, 0) + v
    total = sum(tot.values()) or 1
    out = {}
    for k, v in tot.items():
        key = k if (k != "Other" and 100 * v / total >= min_pct) else "Other"
        out[key] = out.get(key, 0) + v
    return sorted(out.items(), key=lambda kv: (kv[0] == "Other", -kv[1]))


def all_langs():
    tot = {}
    for r in CODE_REPOS:
        for k, v in r["langs"].items():
            tot[k] = tot.get(k, 0) + v
    return bucket_langs(tot, 4)


def stamp(c):
    return dt.datetime.fromisoformat(c["ts"].replace("Z", "+00:00")).astimezone(MSK)


def times():
    return sorted(stamp(c) for c in DATA["commits"])


def per_day():
    out = {}
    for m in times():
        out[m.date()] = out.get(m.date(), 0) + 1
    return out


def today():
    return dt.datetime.now(MSK).date()


def repo_label(name):
    return REPO_NAMES.get(name.lower(), name.upper())


# ------------------------------------------------------------------ shared drawing bits
def screen(title, h, desc=""):
    s = Svg(W, h, title, desc)
    s.defs.append('<filter id="glow" x="-30%" y="-30%" width="160%" height="160%">'
                  '<feGaussianBlur stdDeviation="2.2" result="b"/>'
                  '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
                  '<filter id="soft"><feGaussianBlur stdDeviation="6"/></filter>')
    s.rect(0, 0, W, h, BLACK, rx=6)
    return s


def tiny(s, x, y, txt, fill=CREAM, size=10, anchor="start", weight=400, ls=0.6, opacity=1):
    s.text(x, y, txt, size, fill, weight, anchor=anchor, ls=ls, opacity=opacity)


def polyline(s, pts, stroke, sw=1.6, glow=True, opacity=1):
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    s.path(d, "none", stroke, sw, opacity, extra='filter="url(#glow)"' if glow else "")


def scanlines(s, x, y, w, h, op=0.28):
    pid = s.uid("sl")
    s.defs.append(f'<pattern id="{pid}" width="4" height="3" patternUnits="userSpaceOnUse">'
                  f'<rect width="4" height="1" fill="#000" opacity="{op}"/></pattern>')
    s.rect(x, y, w, h, f"url(#{pid})")


def crt(s, x, y, w, h, glass):
    """A monitor bezel with a rounded glass; returns the inner screen box."""
    s.rect(x, y, w, h, s.gradient([(0, "#2a2a36", 1), (1, "#101016", 1)], 0, 0, 0, 1), "#45455a", 1.5, rx=14)
    ix, iy, iw, ih = x + 12, y + 12, w - 24, h - 30
    s.rect(ix, iy, iw, ih, glass, "#05050a", 2, rx=18)
    return ix, iy, iw, ih


def glass_shine(s, ix, iy, iw, ih):
    scanlines(s, ix, iy, iw, ih)
    s.rect(ix, iy, iw, ih, s.gradient([(0, "#ffffff", 0.10), (0.4, "#ffffff", 0), (1, "#000000", 0.35)],
                                      0, 0, 0.3, 1), rx=18)


# ------------------------------------------------------------------ 1. the night scene
def scene():
    H = 540
    rnd = random.Random(11)
    days = per_day()
    end = today()
    span = 90
    series = [days.get(end - dt.timedelta(days=span - 1 - i), 0) for i in range(span)]
    pin = DATA.get("pin") or {}
    r = pinned_repo()
    s = screen("Mitaro. Omar, computer science student at MTUCI. A mission-control collage: commits per day, "
               "the Campus project in orbit, a starburst sun over the ocean.", H,
               f"Commits over the last {span} days: {sum(series)}. Campus: {r['commits']} commits, "
               + ", ".join(f"{v} {k}" for k, v in pin.items()) + ".")
    hz, sx, sy = 338, 520, 312

    # stars
    for _ in range(170):
        s.circle(rnd.uniform(0, W), rnd.uniform(0, hz - 10), rnd.choice((0.5, 0.7, 0.9, 1.3)), "#ffffff",
                 round(rnd.uniform(0.25, 0.95), 2))

    # the sun: halo, rays, lens flares
    s.circle(sx, sy, 150, s.gradient([(0, "#ffe9c7", 0.55), (0.35, "#ff9e5e", 0.18), (1, "#ff9e5e", 0)],
                                     0.5, 0.5, 0.5, kind="radial"))
    s.circle(sx, sy, 46, s.gradient([(0, "#ffffff", 1), (0.5, "#fff1d6", 0.9), (1, "#ffcf9a", 0)],
                                    0.5, 0.5, 0.5, kind="radial"))
    for i in range(36):
        a = i / 36 * math.tau + rnd.uniform(-0.04, 0.04)
        ln = rnd.uniform(40, 120) * (1.6 if i % 9 == 0 else 1)
        s.line(sx, sy, sx + math.cos(a) * ln, sy + math.sin(a) * ln, "#fff3dc", 0.8, round(rnd.uniform(0.25, 0.7), 2))
    s.line(sx - 330, sy + 26, sx + 260, sy - 34, AMBER, 1.4, 0.55)
    s.line(sx - 220, sy + 46, sx + 340, sy - 6, "#9b6bff", 1, 0.45)

    # ocean with glints; the sun's path burns gold
    s.rect(0, hz, W, H - hz, s.gradient([(0, "#0b2a55", 1), (1, "#020a1a", 1)], 0, 0, 0, 1))
    s.line(0, hz, W, hz, "#bcd6ff", 1, 0.5)
    for _ in range(620):
        y = hz + 3 + rnd.random() ** 1.7 * (H - hz - 30)
        depth = (y - hz) / (H - hz)
        x = rnd.uniform(0, W)
        near = abs(x - sx) < 26 + depth * 150
        ln = (3 + depth * 16) * rnd.uniform(0.5, 1.2)
        col = rnd.choice(("#fff3dc", "#ffd9a0")) if near else rnd.choice(("#9fc4ff", "#5f8fe0", "#cfe0ff"))
        op = rnd.uniform(0.55, 1) if near else rnd.uniform(0.12, 0.5)
        s.line(x, y, x + ln, y, col, 0.8 + depth * 1.2, round(op, 2))

    # shore and the trees on the right
    s.path(f"M0 {H}L0 492C90 470 170 486 250 478C340 470 420 498 520 490C640 480 720 470 {W} 452L{W} {H}Z",
           "#030806")
    for _ in range(46):
        s.circle(rnd.uniform(760, W + 30), rnd.uniform(200, 520), rnd.uniform(18, 42), "#071309")
    for _ in range(260):
        s.circle(rnd.uniform(752, W), rnd.uniform(196, 520), rnd.uniform(0.8, 2.2),
                 rnd.choice(("#3f7a2f", "#6aa33f", "#2b5422")), round(rnd.uniform(0.3, 0.9), 2))

    # top left: commits per day, amber, glowing
    x0, y0, cw, ch = 34, 46, 300, 150
    s.rect(x0 - 8, y0 - 22, cw + 16, ch + 34, BLACK, BLUE, 1, opacity=0.9)
    for k in range(7):
        s.line(x0, y0 + k * ch / 6, x0 + cw, y0 + k * ch / 6, NAVY, 1)
    for k in range(0, span + 1, 15):
        s.line(x0 + cw * k / span, y0 + ch, x0 + cw * k / span, y0 + ch + 4, CYAN, 1)
    top = max(series) or 1
    pts = [(x0 + cw * i / (span - 1), y0 + ch - (ch - 8) * v / top) for i, v in enumerate(series)]
    s.path("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + f" L{x0 + cw} {y0 + ch} L{x0} {y0 + ch}Z",
           s.gradient([(0, AMBER, 0.75), (1, "#a8341a", 0.25)], 0, 0, 0, 1))
    polyline(s, pts, YELLOW, 1.4)
    tiny(s, x0, y0 - 8, f"COMMITS / DAY  ·  LAST {span} DAYS", CYAN, 9.5, weight=700)
    tiny(s, x0 + cw, y0 - 8, f"PEAK {top}", AMBER, 9.5, "end", 700)
    for k, (a, b) in enumerate((("TOTAL", sum(series)), ("ACTIVE DAYS", sum(1 for v in series if v)),
                                ("TODAY", days.get(end, 0)))):
        y = y0 + ch + 28 + k * 16
        s.line(x0 - 8, y + 4, x0 + cw + 8, y + 4, MAGENTA, 0.8, 0.8)
        tiny(s, x0, y, a, CREAM, 10)
        tiny(s, x0 + cw, y, str(b), YELLOW, 10, "end", 700)

    # top right: Campus in orbit, its parts as satellites, read out underneath
    cx, cy, tilt = 735, 126, math.radians(-18)
    s.rect(608, 56, 254, 196, "none", BLUE, 1.2, rx=40)
    s.line(608, cy, 862, cy, NAVY, 1)
    s.line(cx, 56, cx, 196, NAVY, 1)
    s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="96" ry="44" fill="none" stroke="{CYAN}" stroke-width="1" '
          f'stroke-dasharray="3 4" transform="rotate(-18 {cx} {cy})"/>')
    s.add(f'<rect x="{cx - 64}" y="{cy - 8}" width="128" height="16" rx="8" fill="#1b3f8f" fill-opacity=".45" '
          f'stroke="{CYAN}" stroke-width="1" transform="rotate(-28 {cx} {cy})"/>')
    s.circle(cx, cy, 22, s.gradient([(0, "#5b8cff", 1), (1, "#0b1d4a", 1)], 0.35, 0.35, 0.7, kind="radial"))
    for k in (-11, 0, 11):
        half = math.sqrt(22 ** 2 - k ** 2)
        s.line(cx - half, cy + k, cx + half, cy + k, "#9fc4ff", 0.7, 0.6)
    s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="9" ry="22" fill="none" stroke="#9fc4ff" stroke-width=".7" opacity=".6"/>')
    tiny(s, cx, 50, f"CAMPUS  ·  {r.get('release') or 'DEV'}", CYAN, 10, "middle", 700, 1.2)
    short = {"java": "JAVA", "svelte": "UI", "tests": "TESTS", "migrations": "DB", "screens": "SCREENS",
             "versions": "VERS"}
    sats = [(short.get(k, k.upper()), v) for k, v in pin.items()][:6]
    for i, (k, v) in enumerate(sats):
        a = i / len(sats) * math.tau + 0.5
        ex, ey = math.cos(a) * 96, math.sin(a) * 44
        px, py = cx + ex * math.cos(tilt) - ey * math.sin(tilt), cy + ex * math.sin(tilt) + ey * math.cos(tilt)
        s.circle(px, py, 3.4, RED, extra='filter="url(#glow)"')
        tiny(s, 622 + (i % 3) * 80, 214 + (i // 3) * 18, f"{v} {k}", AMBER, 9.5, weight=700)
    s.line(616, 200, 854, 200, MAGENTA, 0.8, 0.7)

    # the name, in the dark between the charts
    s.text(470, 70, "MITARO", 30, CYAN, 700, anchor="middle", ls=8)
    tiny(s, 470, 94, "OMAR  ·  CS @ MTUCI", CREAM, 11, "middle", 400, 2)
    tiny(s, 470, 112, "LOCAL-FIRST  ·  SECURITY", PINK, 10, "middle", 400, 2)

    # bottom left: a listing over the water
    rows = [("name", "'Omar'  # aka Mitaro"), ("school", "'MTUCI, computer science'"),
            ("stack", "[java, svelte, python, flask]"), ("focus", "'security, local-first'"),
            ("pinned", "'Campus'  # study-group app"), ("online", f"since {DATA['created'][:4]}"),
            ("contact", "t.me/treadways")]
    s.rect(22, 374, 330, len(rows) * 17 + 18, BLACK, opacity=0.55)
    for i, (k, v) in enumerate(rows):
        y = 394 + i * 17
        tiny(s, 30, y, f"{i + 1:03d}", PINK, 10.5, weight=700)
        tiny(s, 62, y, f"{k:<8}= {v}", CREAM, 10.5)
    last = f"{rows[-1][0]:<8}= {rows[-1][1]}"
    s.rect(62 + text_width(10.5, last, ls=0.6) + 4, 394 + (len(rows) - 1) * 17 - 9, 6, 11, GREEN,
           extra='class="blink"')
    s.rect(1, 1, W - 2, H - 2, "none", MAGENTA, 1.5, rx=6)
    return s


# ------------------------------------------------------------------ 2. the monitor wall
def monitors():
    H = 262
    rnd = random.Random(5)
    langs = all_langs()
    pin = DATA.get("pin") or {}
    r = pinned_repo()
    hours = [0] * 24
    for m in times():
        hours[m.hour] += 1
    peak = max(range(24), key=lambda h: hours[h])
    night = round(100 * sum(hours[i] for i in (22, 23, 0, 1, 2, 3)) / max(1, sum(hours)))
    s = screen("A wall of monitors: languages as a wireframe, the Campus project, the moon and commits by hour.", H)
    s.line(0, 14, W, 14, MAGENTA, 1.2)
    for x, txt, col in ((12, "SYS:MITARO-CS", RED), (300, f"CAMPUS {r.get('release') or ''}", AMBER),
                        (650, "LIVE · UPDATED EVERY 6H", CYAN)):
        s.rect(x, 6, text_width(9.5, txt, ls=0.6) + 12, 16, BLACK, col, 1)
        tiny(s, x + 6, 18, txt, col, 9.5, weight=700)

    # 1: languages as a wireframe mountain range
    ix, iy, iw, ih = crt(s, 10, 30, 200, 222, "#05060c")
    total = sum(v for _, v in langs) or 1
    for gx in range(int(ix + 8), int(ix + iw - 4), 12):
        for gy in range(int(iy + 10), int(iy + ih - 10), 12):
            s.circle(gx, gy, 0.6, "#6a6aa0", 0.6)
    for i, (k, v) in enumerate(langs):
        peak_x = ix + 18 + (iw - 36) * (i + 0.5) / len(langs)
        top = iy + ih - 18 - (ih - 50) * (0.25 + 0.75 * v / langs[0][1])
        for j in range(3):
            spread = 22 + j * 16
            polyline(s, [(peak_x - spread, iy + ih - 18), (peak_x + rnd.uniform(-6, 6), top + j * 10),
                         (peak_x + spread, iy + ih - 18)], LANG_COLOR.get(k, GREY), 1, opacity=0.9 - j * 0.25)
    tiny(s, ix + 10, iy + ih - 4, "LANG " + " ".join(f"{k[:2].upper()}{round(100 * v / total)}"
                                                     for k, v in langs[:4]), CREAM, 8.5)
    glass_shine(s, ix, iy, iw, ih)

    # 2: Campus readout on a teal glass
    ix, iy, iw, ih = crt(s, 220, 30, 210, 222, s.gradient([(0, "#2e6e66", 1), (1, "#0d2b2a", 1)], 0, 0, 0, 1))
    s.circle(ix + 30, iy + 62, 34, s.gradient([(0, "#ffe7c4", 0.95), (0.6, "#e9a25f", 0.5), (1, "#e9a25f", 0)],
                                              0.5, 0.5, 0.5, kind="radial"))
    lines = [f"CAMPUS {r.get('release') or ''}", f"JAVA    {pin.get('java', '-')}", f"UI      {pin.get('svelte', '-')}",
             f"TESTS   {pin.get('tests', '-')}", f"DB      {pin.get('migrations', '-')}",
             f"SCREENS {pin.get('screens', '-')}", f"COMMITS {r['commits']}"]
    for i, ln in enumerate(lines):
        tiny(s, ix + 70, iy + 34 + i * 19, ln, "#e8fff6" if i else YELLOW, 11, weight=700)
    tiny(s, ix + 14, iy + ih - 10, "STUDY-GROUP APP", "#bdf5e6", 9)
    glass_shine(s, ix, iy, iw, ih)

    # 3: the moon over clouds, and the year I came online
    ix, iy, iw, ih = crt(s, 440, 30, 210, 222, "#07070b")
    s.circle(ix + 52, iy + 70, 16, s.gradient([(0, "#ff8a5c", 1), (1, "#7a2412", 1)], 0.35, 0.35, 0.7, kind="radial"))
    s.circle(ix + 118, iy + 104, 62, s.gradient([(0, "#ffffff", 1), (0.6, "#c9cbe0", 1), (1, "#5b5d78", 1)],
                                                0.35, 0.3, 0.75, kind="radial"))
    for cx, cy, rr in ((ix + 132, iy + 92, 14), (ix + 98, iy + 120, 9), (ix + 146, iy + 128, 7)):
        s.circle(cx, cy, rr, "#9a9cb8", 0.55)
    for k in range(14):
        s.circle(ix + 20 + k * 13, iy + 162 + (k % 3) * 4, 16 + (k * 7 % 9), "#e9ecf7", 0.85,
                 extra='filter="url(#soft)"')
    tiny(s, ix + 14, iy + 24, f"ONLINE SINCE {DATA['created'][:4]}", CREAM, 9.5, weight=700)
    glass_shine(s, ix, iy, iw, ih)

    # 4: commits by hour as a stepped mountain under a green-to-amber sky
    x, y, w, h = 660, 30, 218, 222
    s.rect(x, y, w, h, "#05050a", "#45455a", 1.5, rx=6)
    s.rect(x + 8, y + 26, w - 16, 120,
           s.gradient([(0, "#0c3d1c", 1), (0.55, "#3fae4a", 0.85), (1, "#ff9a3d", 0.9)], 0, 0, 1, 0))
    top = max(hours) or 1
    bw = (w - 16) / 24
    for h_, n in enumerate(hours):
        bh = 8 + 110 * n / top
        s.rect(x + 8 + h_ * bw, y + 146 - bh, bw - 1, bh, "#020203")
        for k in range(int(bh // 9)):
            if rnd.random() < 0.45:
                s.rect(x + 9 + h_ * bw + rnd.uniform(0, bw - 4), y + 140 - k * 9, 2, 2,
                       rnd.choice((CYAN, "#ffffff", AMBER)), opacity=0.8)
    tiny(s, x + 8, y + 18, "COMMITS BY HOUR · MSK", GREEN, 9.5, weight=700)
    for k, (a, b) in enumerate((("PEAK", f"{peak:02d}:00"), ("AFTER 22:00", f"{night}%"))):
        tiny(s, x + 10, y + 172 + k * 18, a, CREAM, 10)
        tiny(s, x + w - 10, y + 172 + k * 18, b, YELLOW, 10, "end", 700)
    s.rect(1, 1, W - 2, H - 2, "none", MAGENTA, 1.5, rx=6)
    return s


# ------------------------------------------------------------------ 3. the data desk
def desk():
    H = 312
    ts = times()
    langs = all_langs()
    days = per_day()
    end = today()
    weeks = 26
    start = end - dt.timedelta(days=end.weekday() + 7 * (weeks - 1))
    weekly = [sum(days.get(start + dt.timedelta(days=7 * w + d), 0) for d in range(7)) for w in range(weeks)]
    by_repo = {}
    for c in DATA["commits"]:
        by_repo[c["repo"]] = by_repo.get(c["repo"], 0) + 1
    top_repos = sorted(by_repo.items(), key=lambda kv: -kv[1])
    s = screen("Data desk: commits per repository, languages, commits per week and cumulative commits over time.", H)
    s.line(0, 14, W, 14, MAGENTA, 1.2)

    # left: repositories table and language bars
    tiny(s, 14, 34, "REPO", CYAN, 9.5, weight=700)
    tiny(s, 228, 34, "COMMITS", CYAN, 9.5, "end", 700)
    for i, (name, n) in enumerate(top_repos[:7]):
        y = 54 + i * 17
        tiny(s, 14, y, repo_label(name)[:18], CREAM, 10)
        tiny(s, 228, y, str(n), YELLOW, 10, "end", 700)
        s.line(14, y + 5, 228, y + 5, NAVY, 0.8)
    total = sum(v for _, v in langs) or 1
    tiny(s, 14, 190, "LANGUAGES", CYAN, 9.5, weight=700)
    for i, (k, v) in enumerate(langs[:6]):
        y = 200 + i * 17
        s.rect(92, y, 100 * v / langs[0][1], 11, LANG_COLOR.get(k, GREY), opacity=0.9)
        s.rect(92, y, 100, 11, "none", "#3a2a10", 0.8)
        tiny(s, 14, y + 9.5, k[:10].upper(), CREAM, 9.5)
        tiny(s, 228, y + 9.5, f"{round(100 * v / total)}%", AMBER, 9.5, "end", 700)

    # center: commits per week, lavender bars under a green band
    x0, y0, w0, h0 = 246, 30, 222, 262
    s.rect(x0, y0, w0, h0, "#05050a", "#3b3b55", 1)
    s.rect(x0 + 1, y0 + 1, w0 - 2, 52, s.gradient([(0, GREEN, 0.55), (1, "#2f6b3a", 0.25)], 0, 0, 0, 1))
    tiny(s, x0 + 8, y0 + 18, f"COMMITS / WEEK · {weeks} WK", "#0b1f0f", 9.5, weight=700)
    tiny(s, x0 + w0 - 8, y0 + 18, f"TOTAL {sum(weekly)}", "#0b1f0f", 9.5, "end", 700)
    topw = max(weekly) or 1
    bw = (w0 - 16) / weeks
    for k in range(5):
        s.line(x0 + 4, y0 + 66 + k * 44, x0 + w0 - 4, y0 + 66 + k * 44, "#ffffff", 0.5, 0.15)
    for k, n in enumerate(weekly):
        bh = 4 + (h0 - 90) * n / topw
        s.rect(x0 + 8 + k * bw, y0 + h0 - 14 - bh, bw - 1.5, bh, LAVENDER, opacity=0.85 if n else 0.25)
    tiny(s, x0 + 8, y0 + h0 - 3, MONTHS[start.month - 1], GREY, 8.5)
    tiny(s, x0 + w0 - 8, y0 + h0 - 3, MONTHS[end.month - 1], GREY, 8.5, "end")

    # right: cumulative commits over time, one glowing line per repository
    x0, y0, w0, h0 = 484, 30, 390, 230
    s.rect(x0, y0, w0, h0, "#03030a", "#3b3b55", 1)
    for k in range(1, 8):
        s.line(x0 + w0 * k / 8, y0, x0 + w0 * k / 8, y0 + h0, BLUE, 0.6, 0.5)
    for k, col in enumerate((PINK, CYAN, RED, AMBER)):
        s.line(x0, y0 + h0 * (k + 1) / 5, x0 + w0, y0 + h0 * (k + 1) / 5, col, 0.5, 0.35)
    t0 = ts[0] if ts else dt.datetime.now(MSK)
    t1 = dt.datetime.now(MSK)
    span = max(1.0, (t1 - t0).total_seconds())
    every = len(ts) or 1

    def curve(stamps):
        pts, n = [(x0, y0 + h0)], 0
        for t in stamps:
            x = x0 + w0 * (t - t0).total_seconds() / span
            pts.append((x, y0 + h0 - (h0 - 16) * n / every))
            n += 1
            pts.append((x, y0 + h0 - (h0 - 16) * n / every))
        pts.append((x0 + w0, pts[-1][1]))
        return pts

    for i, (name, _) in enumerate(top_repos[:3]):
        polyline(s, curve(sorted(stamp(c) for c in DATA["commits"] if c["repo"] == name)), LINE_COLORS[i + 1], 1.1,
                 opacity=0.85)
        tiny(s, x0 + 8, y0 + 34 + i * 14, repo_label(name), LINE_COLORS[i + 1], 9, weight=700)
    polyline(s, curve(ts), YELLOW, 2.2)
    tiny(s, x0 + 8, y0 + 18, f"CUMULATIVE COMMITS · {len(ts)}", YELLOW, 9.5, weight=700)
    tiny(s, x0 + 4, y0 + h0 + 14, str(t0.year), GREY, 9)
    tiny(s, x0 + w0 - 4, y0 + h0 + 14, str(t1.year), GREY, 9, "end")

    # a small amber wave along the bottom: the same weeks
    polyline(s, [(x0 + w0 * k / (weeks - 1), 300 - 12 * n / topw) for k, n in enumerate(weekly)], AMBER, 1.2)
    s.rect(1, 1, W - 2, H - 2, "none", MAGENTA, 1.5, rx=6)
    return s


if __name__ == "__main__":
    for name, fn in (("scene", scene), ("monitors", monitors), ("desk", desk)):
        fn().save(OUT, f"{name}.svg")
