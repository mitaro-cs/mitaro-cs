#!/usr/bin/env python3
"""Builds every SVG of the profile README into ../assets from scripts/data.json.

Palette rule: pure black and pure white only. Depth comes from gradients, halftone dots,
hatching and hard offset shadows, never from flat grey tints.
"""
import base64
import json
import math
import os
import random
import sys
from datetime import date

from lib import (BLACK, WHITE, Svg, cap_height, jag, smoothstep, star_points, text_width)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
PNG = base64.b64encode(open(os.path.join(HERE, "src", "portrait-halftone.png"), "rb").read()).decode()
import struct
with open(os.path.join(HERE, "src", "portrait-halftone.png"), "rb") as _f:
    _f.seek(16)
    PW, PH = struct.unpack(">II", _f.read(8))
W = 888

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
REPO = {r["name"]: r for r in DATA["repos"]}
CODE_LANGS = ["Python", "JavaScript", "CSS", "HTML"]
NOT_CODE = {"Rich Text Format"}


# ------------------------------------------------------------------ shared drawing bits
def halftone_field(s, x0, x1, y0, y1, pitch=10.0, slope=0.28, color=BLACK, reverse=False, power=0.9):
    """Rotated dot grid whose dot size grows along x: a gradient made of dots."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ang = math.radians(45)
    ca, sa = math.cos(ang), math.sin(ang)
    n = int(math.hypot(x1 - x0, y1 - y0) / pitch) + 2
    d = []
    for i in range(-n, n):
        for j in range(-n, n):
            u, v = i * pitch, j * pitch
            x, y = cx + u * ca - v * sa, cy + u * sa + v * ca
            if not (x0 - pitch <= x <= x1 + pitch and y0 - pitch <= y <= y1 + pitch):
                continue
            t = (x + slope * y - x0) / (x1 - x0)
            t = 1 - t if reverse else t
            t = smoothstep(t) ** power
            r = pitch * 0.80 * t
            if r < 0.45:
                continue
            d.append(f"M{x - r:.1f} {y:.1f}a{r:.1f} {r:.1f} 0 1 0 {2 * r:.1f} 0a{r:.1f} {r:.1f} 0 1 0 {-2 * r:.1f} 0z")
    s.path("".join(d), fill=color)


def label(s, x, y, txt, key="elite", size=16, tone="b", rot=0.0, seed=1, weight=400, pad=14, ls=0):
    """Hand-cut text label. tone b = black tile, w = white tile."""
    tw_ = text_width(key, weight, size, txt, ls)
    h = size * 1.75
    fill, ink, edge = (BLACK, WHITE, WHITE) if tone == "b" else (WHITE, BLACK, BLACK)
    pts = jag(x, y, tw_ + pad * 2, h, 1.6, seed, 16)
    tr = f"rotate({rot} {x + tw_ / 2 + pad:.1f} {y + h / 2:.1f})"
    s.poly(pts, BLACK, transform=f"{tr} translate(4 4)")
    s.poly(pts, fill, edge, 2, transform=tr)
    capy = y + h / 2 + cap_height(key, weight, size) / 2
    s.text(x + pad, capy, txt, key, size, ink, weight, ls=ls, transform=tr)
    return tw_ + pad * 2


def patterns(s):
    """Returns fills that stay pure black and white: solid, stripes, dots, outline, hatch."""
    s.defs.append(
        '<pattern id="pStripe" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="7" height="7" fill="{BLACK}"/><rect width="3" height="7" fill="{WHITE}"/></pattern>'
        '<pattern id="pDot" width="7" height="7" patternUnits="userSpaceOnUse">'
        f'<rect width="7" height="7" fill="{BLACK}"/><circle cx="3.5" cy="3.5" r="2.1" fill="{WHITE}"/></pattern>'
        '<pattern id="pHatch" width="6" height="6" patternUnits="userSpaceOnUse">'
        f'<rect width="6" height="6" fill="{BLACK}"/><path d="M0 0L6 6M6 0L0 6" stroke="{WHITE}" stroke-width="1.2"/></pattern>'
    )
    return {"Python": WHITE, "JavaScript": "url(#pStripe)", "CSS": "url(#pDot)",
            "HTML": BLACK, "Other": "url(#pHatch)"}


def lang_bar(s, x, y, w, h, langs, pats, legend_y=None, legend_size=13, cols=2, legend_dx=None, kb=False):
    total = sum(v for k, v in langs if k not in NOT_CODE) or 1
    items = [(k, v) for k, v in langs if k not in NOT_CODE]
    cx = x
    s.rect(x - 2, y - 2, w + 4, h + 4, BLACK, WHITE, 1.5)
    for k, v in items:
        seg = w * v / total
        s.rect(cx, y, seg, h, pats.get(k, pats["Other"]), WHITE, 1.4)
        cx += seg
    if legend_y is None:
        return
    dx = legend_dx or (w / cols)
    for i, (k, v) in enumerate(items):
        lx = x + (i % cols) * dx
        ly = legend_y + (i // cols) * 24
        s.rect(lx, ly - 11, 14, 14, pats.get(k, pats["Other"]), WHITE, 1.4)
        pct = round(100 * v / total)
        s.text(lx + 22, ly, f"{k} {pct}%" + (f" · {v // 1000} KB" if kb else ""), "mono", legend_size, WHITE, 500)


def agg_langs(repos):
    tot = {}
    for r in repos:
        for k, v in r["langs"].items():
            if k in NOT_CODE:
                continue
            key = k if k in CODE_LANGS else "Other"
            tot[key] = tot.get(key, 0) + v
    return sorted(tot.items(), key=lambda kv: (kv[0] == "Other", -kv[1]))


def glow_panel(s, w, h, seed_x=0.85, seed_y=0.0, hard_shadow=True, radius=4):
    """Black card with a soft white light-leak gradient and a hard offset shadow."""
    if hard_shadow:
        s.rect(9, 9, w - 12, h - 12, WHITE, BLACK, 2, radius)
    s.rect(2, 2, w - 12, h - 12, BLACK, WHITE, 2, radius)
    g = s.gradient([(0, WHITE, 0.20), (0.5, WHITE, 0.04), (1, WHITE, 0)], seed_x, seed_y, 0.75,
                   kind="radial", extra="gradientTransform=\"translate(0 0)\"")
    s.rect(2, 2, w - 12, h - 12, g, rx=radius)


# ------------------------------------------------------------------ banner
def banner():
    H = 340
    s = Svg(W, H, "Mitaro. Computer science student at MTUCI, Python and Flask developer.",
            "Black and white collage banner: cut-out lettering spelling MITARO and a halftone portrait.")
    s.defs.append(f'<clipPath id="cp"><rect width="{W}" height="{H}" rx="6"/></clipPath>')
    s.add('<g clip-path="url(#cp)">')
    s.rect(0, 0, W, H, WHITE)
    under = s.gradient([(0, BLACK, 0), (0.30, BLACK, 0), (0.55, BLACK, 0.55), (0.72, BLACK, 1), (1, BLACK, 1)],
                       0, 0, 1, 0.12)
    s.rect(0, 0, W, H, under)
    halftone_field(s, 215, 600, -20, H + 20, pitch=10.5, slope=0.30)
    s.rect(590, 0, W - 590, H, BLACK)
    # portrait
    pw = 318
    ph = pw * PH / PW
    px, py = W - pw - 44, 4
    fade = s.gradient([(0, BLACK, 0), (0.4, WHITE, 1), (1, WHITE, 1)], 0, 0, 1, 0)
    s.defs.append(f'<mask id="pm" maskUnits="userSpaceOnUse" x="{px}" y="{py}" width="{pw}" height="{ph:.0f}">'
                  f'<rect x="{px}" y="{py}" width="{pw}" height="{ph:.0f}" fill="{fade}"/></mask>')
    s.add(f'<image href="data:image/png;base64,{PNG}" x="{px}" y="{py}" width="{pw}" height="{ph:.0f}" mask="url(#pm)"/>')
    # cut-out title
    tiles = [("M", "anton", 400, 84, "b", -4), ("I", "elite", 400, 78, "w", 3), ("T", "play", 900, 80, "b", -2),
             ("A", "anton", 400, 82, "w", 5), ("R", "bebas", 400, 90, "b", -3), ("O", "play", 900, 78, "w", 2)]
    x = 30
    for i, (ch, key, wt, cap, tone, rot) in enumerate(tiles):
        ratio = cap_height(key, wt, 100) / 100
        size = cap / ratio
        tw_ = text_width(key, wt, size, ch)
        w_, h_ = tw_ + 30, 118 - (i % 3) * 6
        y = 30 + (i % 2) * 5 - (i % 3) * 2
        fill, ink, edge = (BLACK, WHITE, WHITE) if tone == "b" else (WHITE, BLACK, BLACK)
        pts = jag(x, y, w_, h_, 2.2, 11 + i, 18)
        cxr, cyr = x + w_ / 2, y + h_ / 2
        tr = f"rotate({rot} {cxr:.1f} {cyr:.1f})"
        s.poly(pts, BLACK, transform=f"{tr} translate(5 5)")
        s.poly(pts, fill, edge, 2.4, transform=tr)
        s.text(x + 15, cyr + cap / 2, ch, key, size, ink, wt, transform=tr)
        x += w_ + 5
    label(s, 34, 176, "COMPUTER SCIENCE STUDENT @ MTUCI", "elite", 16, "b", -1.5, 5, ls=0.6)
    label(s, 58, 214, "PYTHON  /  FLASK  /  SECURITY", "elite", 16, "w", 1.2, 6, ls=0.6)
    # marker note + arrow
    label(s, 430, 240, "hi, I'm Omar", "marker", 25, "w", -5, 8, pad=16)
    for col, sw in ((BLACK, 8), (WHITE, 3)):
        s.path("M594 236C655 246 700 214 708 172", stroke=col, sw=sw)
        s.path("M694 186L708 168L724 182", stroke=col, sw=sw)
    # tape
    s.add('<g transform="rotate(-2.6 444 314)">')
    s.rect(-30, 296, W + 60, 36, BLACK, WHITE, 2)
    unit = "MTUCI  ///  PYTHON  ///  FLASK  ///  SECURITY  ///  LOCAL-FIRST  ///  "
    txt = unit * 4
    s.text(-14, 319, txt, "mono", 14, WHITE, 700, ls=2.2)
    s.add("</g>")
    s.grain(0.10)
    s.add("</g>")
    s.rect(1.5, 1.5, W - 3, H - 3, "none", BLACK, 3, 6)
    s.rect(9, 9, W - 18, H - 18, "none", WHITE, 1, 3, opacity=0.9, extra='stroke-dasharray="2 5"')
    s.save(OUT, "banner.svg")


# ------------------------------------------------------------------ stats row
def stats():
    repos = DATA["repos"]
    code_kb = sum(v for r in repos for k, v in r["langs"].items() if k not in NOT_CODE) // 1000
    items = [("REPOS", str(len(repos))), ("COMMITS", str(sum(r["commits"] for r in repos))),
             ("STARS", str(sum(r["stars"] for r in repos))), ("FOLLOWERS", str(DATA["followers"])),
             ("CODE", f"{code_kb} KB")]
    s = Svg(W, 64, "GitHub numbers: " + ", ".join(f"{a} {b}" for a, b in items))
    parts = []
    for a, b in items:
        lw = text_width("mono", 700, 13, a, 2) + 26
        vw = text_width("anton", 400, 24, b) + 28
        parts.append((a, b, lw, vw))
    total = sum(lw + vw for _, _, lw, vw in parts) + 16 * (len(parts) - 1)
    x = (W - total) / 2
    sk = 9

    def par(x, y, w, h, off=0):
        return f"{x + sk + off:.1f},{y + off:.1f} {x + w + sk + off:.1f},{y + off:.1f} {x + w + off:.1f},{y + h + off:.1f} {x + off:.1f},{y + h + off:.1f}"

    y = 10
    for a, b, lw, vw in parts:
        s.poly(par(x, y, lw + vw, 38, 4), BLACK)
        s.poly(par(x, y, lw, 38), BLACK, WHITE, 2)
        s.poly(par(x + lw, y, vw, 38), WHITE, BLACK, 2)
        s.text(x + 13 + sk / 2, y + 24, a, "mono", 13, WHITE, 700, ls=2)
        s.text(x + lw + 14 + sk / 2, y + 30, b, "anton", 24, BLACK, 400)
        x += lw + vw + 16
    s.save(OUT, "stats.svg")


# ------------------------------------------------------------------ section stickers
def sticker(name, txt, dark=False, rot=-1.6, seed=3, key="marker", size=34, alt=None):
    tw_ = text_width(key, 400, size, txt)
    w_, h_ = tw_ + 64, size * 1.85
    Wd, Hd = w_ + 44, h_ + 40
    s = Svg(round(Wd), round(Hd), alt or txt)
    fill, ink, edge, sh = (BLACK, WHITE, WHITE, WHITE) if dark else (WHITE, BLACK, BLACK, BLACK)
    x, y = 22, 20
    pts = jag(x, y, w_, h_, 2.4, seed, 15)
    tr = f"rotate({rot} {x + w_ / 2:.1f} {y + h_ / 2:.1f})"
    s.poly(pts, sh, edge, 2.5, transform=f"{tr} translate(6 6)")
    s.poly(pts, fill, edge, 2.5, transform=tr)
    s.text(x + w_ / 2, y + h_ / 2 + cap_height(key, 400, size) / 2, txt, key, size, ink, anchor="middle", transform=tr)
    s.poly(star_points(x + 4, y + 4, 19, 9, 8, 0.3), ink if dark else BLACK, edge, 2, transform=tr)
    tape_fill = WHITE if dark else BLACK
    s.rect(x + w_ - 66, y - 12, 54, 18, tape_fill, WHITE if not dark else BLACK, 1.5, transform=f"rotate(9 {x + w_ - 40} {y})")
    s.save(OUT, f"head-{name}.svg")


# ------------------------------------------------------------------ who am I: polaroid
def whoami_art():
    Wd, Hd = 292, 380
    s = Svg(Wd, Hd, "Portrait of Omar, halftone print")
    tr = "rotate(-2.2 146 190)"
    fr = jag(14, 12, 258, 348, 1.6, 21, 17)
    s.poly(fr, BLACK, transform=f"{tr} translate(8 8)")
    s.poly(fr, WHITE, BLACK, 3, transform=tr)
    s.add(f'<g transform="{tr}">')
    s.defs.append('<clipPath id="ph"><rect x="30" y="28" width="226" height="262"/></clipPath>')
    s.rect(30, 28, 226, 262, BLACK)
    s.add('<g clip-path="url(#ph)">')
    g = s.gradient([(0, WHITE, 0.30), (1, WHITE, 0)], 0.75, 0.15, 0.9, kind="radial")
    s.rect(30, 28, 226, 262, g)
    ph_h = 226 * PH / PW
    s.add(f'<image href="data:image/png;base64,{PNG}" x="30" y="36" width="226" height="{ph_h:.1f}"/>')
    halftone_field(s, 30, 256, 180, 292, pitch=8, slope=0, color=BLACK, reverse=True)
    s.add("</g>")
    s.rect(30, 28, 226, 262, "none", BLACK, 2)
    s.text(143, 336, "Omar, aka Mitaro", "marker", 22, BLACK, anchor="middle")
    s.rect(40, 2, 62, 20, BLACK, WHITE, 1.5, transform="rotate(-10 70 12)")
    s.rect(196, 4, 62, 20, BLACK, WHITE, 1.5, transform="rotate(8 226 14)")
    s.add("</g>")
    s.save(OUT, "whoami.svg")


# ------------------------------------------------------------------ contact buttons
def button(file, brand, kind, handle):
    Wd, Hd = 268, 68
    s = Svg(Wd, Hd, f"{kind}: {handle}")
    pts = jag(5, 5, 250, 52, 1.4, len(handle), 16)
    s.poly(pts, BLACK, transform="translate(5 5)")
    s.poly(pts, WHITE, BLACK, 2.5)
    s.icon(brand, 20, 17, 28, BLACK)
    s.text(64, 26, kind.upper(), "mono", 11, BLACK, 700, ls=3)
    s.text(64, 46, handle, "mono", 15, BLACK, 700)
    s.save(OUT, file)


# ------------------------------------------------------------------ numbers panel
def numbers():
    H = 330
    s = Svg(W, H, "By the numbers")
    pats = patterns(s)
    glow_panel(s, W, H)
    repos = DATA["repos"]
    years = date.today().year - int(DATA["created"][:4])
    code_kb = sum(v for r in repos for k, v in r["langs"].items() if k not in NOT_CODE) // 1000
    big = [(str(len(repos)), "PUBLIC REPOS"), (str(sum(r["commits"] for r in repos)), "COMMITS"),
           (str(code_kb), "KB OF CODE"), (str(years), "YEARS ON GITHUB")]
    colw = (W - 80) / 4
    tg = s.gradient([(0, WHITE, 1), (1, WHITE, 0.25)], 0, 0, 0, 1)
    for i, (n, lab) in enumerate(big):
        x = 40 + i * colw
        s.text(x, 112, n, "anton", 82, tg)
        s.text(x + 2, 142, lab, "mono", 13, WHITE, 700, ls=3)
        if i:
            s.line(x - 16, 60, x - 16, 146, WHITE, 1.2, dash="2 5")
    langs = agg_langs(repos)
    s.text(40, 200, "CODE BY LANGUAGE, ALL PROJECTS", "mono", 12, WHITE, 700, ls=3)
    lang_bar(s, 40, 214, W - 92, 30, langs, pats, legend_y=278, legend_size=13, cols=3, legend_dx=(W - 92) / 3, kb=True)
    s.save(OUT, "numbers.svg")


# ------------------------------------------------------------------ tech stack
STACK = [("python", "Python", 1), ("flask", "Flask", 1), ("javascript", "JavaScript", 0), ("html5", "HTML5", 0),
         ("css3", "CSS3", 0), ("sqlite", "SQLite", 0), ("docker", "Docker", 0), ("git", "Git", 0),
         ("github", "GitHub", 0), ("githubactions", "Actions", 0), ("gnubash", "Bash", 0), ("linux", "Linux", 0),
         ("figma", "Figma", 0), ("obsidian", "Obsidian", 0), ("openjdk", "Java", 0), ("zedindustries", "Zed", 0)]


def stack():
    H = 348
    s = Svg(W, H, "Tech stack: " + ", ".join(n for _, n, _ in STACK))
    glow_panel(s, W, H, seed_x=0.1)
    tile_w, tile_h, gap = 92, 104, 13
    x0, y0 = 34, 34
    rnd = random.Random(4)
    for i, (ic, name, hot) in enumerate(STACK):
        col, row = i % 8, i // 8
        x = x0 + col * (tile_w + gap)
        y = y0 + row * (tile_h + 14)
        rot = rnd.uniform(-1.6, 1.6)
        pts = jag(x, y, tile_w, tile_h, 1.3, 40 + i, 16)
        tr = f"rotate({rot:.2f} {x + tile_w / 2:.1f} {y + tile_h / 2:.1f})"
        fill, ink = (WHITE, BLACK) if hot else (BLACK, WHITE)
        s.poly(pts, WHITE if not hot else BLACK, transform=f"{tr} translate(4 4)", opacity=0.0 if not hot else 1)
        s.poly(pts, fill, WHITE, 2, transform=tr)
        s.add(f'<g transform="{tr}">')
        s.icon(ic, x + tile_w / 2 - 19, y + 20, 38, ink)
        s.text(x + tile_w / 2, y + 87, name, "mono", 12.5, ink, 700, anchor="middle")
        s.add("</g>")
    ny = y0 + 2 * (tile_h + 14) + 12
    s.line(34, ny - 12, W - 46, ny - 12, WHITE, 1.2, dash="2 5")
    s.text(36, ny + 14, "learning now:", "marker", 19, WHITE)
    s.text(176, ny + 13, "security basics, cleaner backend architecture, a Jarvis-style AI assistant", "elite", 15, WHITE)
    s.save(OUT, "stack.svg")


# ------------------------------------------------------------------ project cards
PROJECTS = [
    dict(repo="VantaVault", file="project-vantavault.svg", n="01", name="VantaVault",
         tag="A private vault for external drives. No cloud, only you and your files.",
         feats=["Password access, hashed locally with PBKDF2-SHA256",
                "Local AES-encrypted archives you can restore in a click",
                "Session protection and a timed lockout after failed logins",
                "Finds external drives automatically",
                "Runs on macOS and Windows, from source or as an app"],
         stack=["Python", "JavaScript", "HTML", "CSS"]),
    dict(repo="AetherCloud", file="project-aethercloud.svg", n="02", name="AetherCloud",
         tag="Turns your own disk into a private cloud with a web dashboard.",
         feats=["Nested folders, file and folder upload, downloads",
                "Image previews and generated file-type badges",
                "Per-user storage quota, storage meter, recent files",
                "Sync check between the database and real files on disk",
                "Installable PWA; runs on Docker Compose or gunicorn"],
         stack=["Flask", "SQLite", "PWA", "Docker"]),
    dict(repo="KworkingSystem", file="project-coworking.svg", n="03", name="Campus Coworking",
         tag="A booking panel for a university coworking space.",
         feats=["Seat booking with overlap and capacity checks",
                "Check-in by student ID and confirmation of the rules",
                "Profiles with avatars and per-user interface themes",
                "Pomodoro 25/5, lofi streams and a study library",
                "REST API for spots, bookings, profile and check-in"],
         stack=["Flask", "SQLite", "Vanilla JS", "REST"]),
]


def project_card(p):
    H = 318
    r = REPO[p["repo"]]
    s = Svg(W, H, f"{p['name']}: " + p["tag"], " ".join(p["feats"]))
    pats = patterns(s)
    glow_panel(s, W, H)
    label(s, 30, 26, p["n"], "anton", 20, "w", -3, int(p["n"]), pad=12)
    tg = s.gradient([(0, WHITE, 1), (1, WHITE, 0.55)], 0, 0, 0, 1)
    s.text(84, 56, p["name"], "anton", 44, tg)
    s.text(32, 90, p["tag"], "elite", 15, WHITE)
    s.line(32, 104, 540, 104, WHITE, 1.2, dash="2 5")
    for i, f in enumerate(p["feats"]):
        y = 134 + i * 34
        s.rect(32, y - 10, 9, 9, WHITE, rx=0, transform=f"rotate(45 36.5 {y - 5.5})")
        s.text(52, y, f, "mono", 13, WHITE, 500)
    s.line(566, 30, 566, H - 42, WHITE, 1.2, dash="2 5")
    rx = 592
    rw = W - 34 - rx - 6
    s.text(rx, 46, "STACK", "mono", 11, WHITE, 700, ls=3)
    cx, cy = rx, 58
    for t in p["stack"]:
        tw_ = text_width("mono", 700, 12, t) + 20
        if cx + tw_ > rx + rw:
            cx, cy = rx, cy + 30
        s.rect(cx, cy, tw_, 24, BLACK, WHITE, 1.6, 12)
        s.text(cx + tw_ / 2, cy + 16.5, t, "mono", 12, WHITE, 700, anchor="middle")
        cx += tw_ + 8
    langs = sorted(r["langs"].items(), key=lambda kv: -kv[1])
    top = [(k, v) for k, v in langs if k in CODE_LANGS]
    other = sum(v for k, v in langs if k not in CODE_LANGS and k not in NOT_CODE)
    if other:
        top.append(("Other", other))
    s.text(rx, 132, "LANGUAGES", "mono", 11, WHITE, 700, ls=3)
    lang_bar(s, rx, 142, rw, 15, top, pats, legend_y=184, legend_size=12, cols=2, legend_dx=rw / 2)
    y, m = r["created"].split("-")[0], MONTHS[int(r["created"].split("-")[1]) - 1]
    meta = [("CREATED", f"{m} {y}"), ("COMMITS", str(r["commits"])), ("STARS", str(r["stars"]))]
    xs = [rx, rx + 104, rx + 188]
    for (a_, b_), xx in zip(meta, xs):
        s.text(xx, 262, a_, "mono", 10, WHITE, 700, ls=2)
        s.text(xx, 288, b_, "anton", 22, WHITE)
    s.save(OUT, p["file"])


# ------------------------------------------------------------------ timeline
LABELS = {"Mouros": "Mouros, my first Python practice", "AetherCloud": "AetherCloud",
          "VantaVault": "VantaVault", "KworkingSystem": "Campus Coworking",
          "Java": "Java practice repo", "Python": "Python practice repo", "mitaro-cs": "This profile"}


def wrap(txt, key, weight, size, maxw):
    lines, cur = [], ""
    for wd in txt.split():
        t = (cur + " " + wd).strip()
        if text_width(key, weight, size, t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines


def timeline():
    H = 330
    s = Svg(W, H, "Timeline of my GitHub projects")
    glow_panel(s, W, H, seed_x=0.5, seed_y=1.0)
    ev = {}
    y, m = DATA["created"].split("-")[:2]
    ev[f"{y}-{m}"] = ["Joined GitHub"]
    for r in sorted(DATA["repos"], key=lambda r: r["created"]):
        ev.setdefault(r["created"][:7], []).append(LABELS.get(r["name"], r["name"]))
    keys = sorted(ev)
    n = len(keys)
    x0, x1, ly = 92, W - 104, 172
    s.line(x0 - 50, ly, x1 + 48, ly, WHITE, 3)
    s.poly(f"{x1 + 46},{ly - 9} {x1 + 62},{ly} {x1 + 46},{ly + 9}", WHITE)
    for i, k in enumerate(keys):
        x = x0 + (x1 - x0) * i / (n - 1)
        up = i % 2 == 0
        yy, mm = k.split("-")
        s.poly(star_points(x, ly, 15, 7, 8, i), WHITE, BLACK, 2)
        s.line(x, ly + (-17 if up else 17), x, ly + (-38 if up else 38), WHITE, 1.6, dash="2 4")
        lines = []
        for item in ev[k]:
            lines += wrap(item, "elite", 400, 14, 176)
        lines = lines[:4]
        if up:
            y0 = ly - 56 - (len(lines) - 1) * 18
            date_y = y0 - 28
        else:
            date_y, y0 = ly + 66, ly + 92
        s.text(x, date_y, f"{MONTHS[int(mm) - 1]} {yy}", "marker", 21, WHITE, anchor="middle")
        for j, ln in enumerate(lines):
            s.text(x, y0 + j * 18, ln, "elite", 14, WHITE, anchor="middle")
    s.save(OUT, "timeline.svg")


# ------------------------------------------------------------------ footer
def footer():
    H = 150
    s = Svg(W, H, "Thanks for reading")
    s.defs.append(f'<clipPath id="cp"><rect width="{W}" height="{H}" rx="6"/></clipPath>')
    s.add('<g clip-path="url(#cp)">')
    s.rect(0, 0, W, H, WHITE)
    under = s.gradient([(0, BLACK, 1), (0.3, BLACK, 1), (0.65, BLACK, 0.4), (1, BLACK, 0)], 0, 0, 1, 0.15)
    s.rect(0, 0, W, H, under)
    halftone_field(s, 250, 880, -10, H + 10, pitch=10.5, slope=0.2, reverse=True)
    s.rect(0, 0, 290, H, BLACK)
    s.text(34, 78, "thanks for reading.", "marker", 36, WHITE)
    s.text(36, 108, "the graphics here are generated by a Python script, see /scripts", "elite", 14, WHITE)
    label(s, W - 262, 50, "© 2026 MITARO", "mono", 15, "b", 1.6, 9, 700, ls=2)
    s.grain(0.10)
    s.add("</g>")
    s.rect(1.5, 1.5, W - 3, H - 3, "none", BLACK, 3, 6)
    s.save(OUT, "footer.svg")


if __name__ == "__main__":
    banner()
    stats()
    sticker("about", "WHO AM I", dark=False, rot=-1.8, seed=3)
    sticker("build", "WHAT I BUILD", dark=True, rot=1.4, seed=5)
    sticker("numbers", "BY THE NUMBERS", dark=False, rot=-1.2, seed=7)
    sticker("stack", "MY TECH STACK", dark=True, rot=1.8, seed=9)
    sticker("timeline", "TIMELINE", dark=False, rot=-1.6, seed=11)
    sticker("now", "RIGHT NOW", dark=True, rot=1.2, seed=13)
    whoami_art()
    button("btn-telegram.svg", "telegram", "Telegram", "@treadways")
    button("btn-email.svg", "gmail", "Email", "miri.saro@bk.ru")
    button("btn-instagram.svg", "instagram", "Instagram", "@stere.os")
    numbers()
    stack()
    for p in PROJECTS:
        project_card(p)
    timeline()
    footer()
