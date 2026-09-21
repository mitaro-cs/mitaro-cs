#!/usr/bin/env python3
"""Builds every SVG of the profile README into ../assets from scripts/data.json.

Palette rule: pure black and pure white only. Depth comes from gradients, halftone dots,
hatching and hard offset shadows, never from flat grey tints.
Motion: CSS/SMIL only (stop-motion wobble, pop-in, marquee, film grain); it stops under
prefers-reduced-motion.
"""
import base64
import json
import math
import os
import random
import struct
import sys
from datetime import date

from lib import BLACK, WHITE, Svg, cap_height, ink_bounds, jag, smoothstep, star_points, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
_png = open(os.path.join(HERE, "src", "portrait-halftone.png"), "rb").read()
PNG = base64.b64encode(_png).decode()
PW, PH = struct.unpack(">II", _png[16:24])
W = 888

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
REPO = {r["name"]: r for r in DATA["repos"]}
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Python", "JavaScript", "CSS", "HTML"]
NOT_CODE = {"Rich Text Format"}


# ------------------------------------------------------------------ shared drawing bits
def dots_path(x0, x1, y0, y1, pitch=10.0, slope=0.28, reverse=False, power=0.9):
    """Path data of a rotated dot grid whose dot size grows along x: a gradient made of dots."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ca = sa = math.sqrt(0.5)
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
    return "".join(d)


def halftone_field(s, x0, x1, y0, y1, pitch=10.0, slope=0.28, color=BLACK, reverse=False, power=0.9):
    s.path(dots_path(x0, x1, y0, y1, pitch, slope, reverse, power), fill=color)


def label(s, x, y, txt, key="mono", size=16, tone="b", rot=0.0, seed=1, weight=700, pad=14, ls=0, anim=True):
    """Hand-cut text label. tone b = black tile, w = white tile."""
    tw_ = text_width(key, weight, size, txt, ls)
    h = size * 1.75
    fill, ink, edge = (BLACK, WHITE, WHITE) if tone == "b" else (WHITE, BLACK, BLACK)
    pts = jag(x, y, tw_ + pad * 2, h, 1.6, seed, 16)
    tr = f"rotate({rot} {x + tw_ / 2 + pad:.1f} {y + h / 2:.1f})"
    if anim:
        s.g("o wob", f"--a:.9deg;--d:{1.5 + seed % 4 * 0.23:.2f}s;animation-delay:-{seed * 0.37 % 1.5:.2f}s")
    s.poly(pts, BLACK, transform=f"{tr} translate(4 4)")
    s.poly(pts, fill, edge, 2, transform=tr)
    s.text(x + pad, y + h / 2 + cap_height(key, weight, size) / 2, txt, key, size, ink, weight, ls=ls, transform=tr)
    if anim:
        s.end()
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


def lang_bar(s, x, y, w, h, langs, pats, legend_y=None, legend_size=13, cols=2, legend_dx=None, kb=False, delay=0.5):
    items = [(k, v) for k, v in langs if k not in NOT_CODE]
    total = sum(v for _, v in items) or 1
    s.rect(x - 2, y - 2, w + 4, h + 4, BLACK, WHITE, 1.5)
    s.g("o grow", f"animation-delay:{delay}s")
    cx = x
    for k, v in items:
        seg = w * v / total
        s.rect(cx, y, seg, h, pats.get(k, pats["Other"]), WHITE, 1.4)
        cx += seg
    s.end()
    if legend_y is None:
        return
    dx = legend_dx or (w / cols)
    for i, (k, v) in enumerate(items):
        lx = x + (i % cols) * dx
        ly = legend_y + (i // cols) * 24
        s.g("rise", f"animation-delay:{delay + 0.5 + i * 0.08:.2f}s")
        s.rect(lx, ly - 11, 14, 14, pats.get(k, pats["Other"]), WHITE, 1.4)
        s.text(lx + 22, ly, f"{k} {round(100 * v / total)}%" + (f" · {v // 1000} KB" if kb else ""),
               "mono", legend_size, WHITE, 500)
        s.end()


def agg_langs(repos):
    tot = {}
    for r in repos:
        for k, v in r["langs"].items():
            if k in NOT_CODE:
                continue
            key = k if k in CODE_LANGS else "Other"
            tot[key] = tot.get(key, 0) + v
    return sorted(tot.items(), key=lambda kv: (kv[0] == "Other", -kv[1]))


def glow_panel(s, w, h, seed_x=0.85, seed_y=0.0, radius=4):
    """Black card with a soft white light-leak gradient and a hard offset shadow."""
    s.rect(9, 9, w - 12, h - 12, WHITE, BLACK, 2, radius)
    s.rect(2, 2, w - 12, h - 12, BLACK, WHITE, 2, radius)
    g = s.gradient([(0, WHITE, 0.20), (0.5, WHITE, 0.04), (1, WHITE, 0)], seed_x, seed_y, 0.75, kind="radial")
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

    # halftone portrait, drawn twice with a 1px offset and swapped in steps: hand-printed flicker
    pw = 388
    ph = pw * PH / PW
    px, py = W - pw - 16, 2
    fade = s.gradient([(0, BLACK, 0), (0.38, WHITE, 1), (1, WHITE, 1)], 0, 0, 1, 0)
    s.defs.append(f'<image id="pimg" href="data:image/png;base64,{PNG}" x="{px}" y="{py}" width="{pw}" height="{ph:.0f}"/>')
    s.defs.append(f'<mask id="pm" maskUnits="userSpaceOnUse" x="{px - 4}" y="{py - 4}" width="{pw + 8}" height="{ph + 8:.0f}">'
                  f'<rect x="{px - 4}" y="{py - 4}" width="{pw + 8}" height="{ph + 8:.0f}" fill="{fade}"/></mask>')
    s.add('<g mask="url(#pm)"><use href="#pimg" class="fA"/><use href="#pimg" x="1.6" y="-1.2" class="fB"/></g>')

    # cut-out title: every tile sized from the real ink of its letter
    tiles = [("M", "mono", 800, 80, "b", -4), ("I", "mono", 800, 76, "w", 3), ("T", "mono", 800, 80, "b", -2),
             ("A", "mono", 800, 82, "w", 5), ("R", "mono", 800, 86, "b", -3), ("O", "mono", 800, 78, "w", 2)]
    x = 30
    for i, (ch, key, wt, cap, tone, rot) in enumerate(tiles):
        bx0, by0, bx1, by1 = ink_bounds(key, wt, 100, ch)
        size = 100 * cap / (by1 - by0)
        bx0, by0, bx1, by1 = ink_bounds(key, wt, size, ch)
        w_ = max(58.0, (bx1 - bx0) + 36)
        h_ = cap + 40 - (i % 3) * 5
        y = 34 + (i % 2) * 5 - (i % 3) * 2
        fill, ink, edge = (BLACK, WHITE, WHITE) if tone == "b" else (WHITE, BLACK, BLACK)
        pts = jag(x, y, w_, h_, 2.2, 11 + i, 18)
        cxr, cyr = x + w_ / 2, y + h_ / 2
        tr = f"rotate({rot} {cxr:.1f} {cyr:.1f})"
        s.g("o pop", f"animation-delay:{i * 0.11:.2f}s")
        s.g("o wob", f"--a:1.7deg;--d:{0.85 + (i % 3) * 0.16:.2f}s;animation-delay:-{i * 0.29:.2f}s")
        s.poly(pts, BLACK, transform=f"{tr} translate(5 5)")
        s.poly(pts, fill, edge, 2.4, transform=tr)
        s.text(cxr - (bx0 + bx1) / 2, cyr + (by0 + by1) / 2, ch, key, size, ink, wt, transform=tr)
        s.end()
        s.end()
        x += w_ + 5
    label(s, 34, 178, "COMPUTER SCIENCE STUDENT @ MTUCI", "mono", 17, "b", -1.5, 5, ls=0.4)
    label(s, 58, 218, "PYTHON  /  FLASK  /  SECURITY", "mono", 17, "w", 1.2, 6, ls=0.4)
    s.g("bob")
    label(s, 372, 250, "hi, I'm Omar", "mono", 22, "w", -5, 8, pad=16, anim=False)
    for col, sw in ((BLACK, 8), (WHITE, 3)):
        s.path("M580 264C620 278 660 260 670 234", stroke=col, sw=sw)
        s.path("M652 240L671 230L679 248", stroke=col, sw=sw)
    s.end()
    # tape with a scrolling ticker
    unit = "MTUCI  ///  PYTHON  ///  FLASK  ///  SECURITY  ///  LOCAL-FIRST  ///  "
    uw = text_width("mono", 700, 15, unit, 2.2)
    s.add('<g transform="rotate(-2.6 444 314)">')
    s.rect(-30, 296, W + 60, 36, BLACK, WHITE, 2)
    s.g("marq", f"--shift:-{uw:.1f}px")
    s.text(-14, 320, unit * 3, "mono", 15, WHITE, 700, ls=2.2)
    s.end()
    s.add("</g>")
    shine = s.gradient([(0, WHITE, 0), (0.5, WHITE, 0.34), (1, WHITE, 0)], 0, 0, 1, 0)
    s.add(f'<g class="sweep"><rect x="-260" y="-30" width="120" height="400" fill="{shine}" transform="skewX(-20)"/></g>')
    s.grain(0.10)
    s.add("</g>")
    s.rect(1.5, 1.5, W - 3, H - 3, "none", BLACK, 3, 6)
    s.rect(9, 9, W - 18, H - 18, "none", WHITE, 1, 3, opacity=0.9, extra='stroke-dasharray="2 5"')
    s.save(OUT, "banner.svg")


# ------------------------------------------------------------------ stats row
def stats():
    repos = DATA["repos"]
    code_kb = sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k not in NOT_CODE) // 1000
    items = [("REPOS", str(len(repos))), ("COMMITS", str(sum(r["commits"] for r in repos))),
             ("STARS", str(sum(r["stars"] for r in repos))), ("FOLLOWERS", str(DATA["followers"])),
             ("CODE", f"{code_kb} KB")]
    s = Svg(W, 64, "GitHub numbers: " + ", ".join(f"{a} {b}" for a, b in items))
    parts = [(a, b, text_width("mono", 700, 14, a, 2) + 26, text_width("mono", 800, 25, b) + 28) for a, b in items]
    total = sum(lw + vw for _, _, lw, vw in parts) + 16 * (len(parts) - 1)
    x = (W - total) / 2
    sk = 9

    def par(x, y, w, h, off=0):
        return (f"{x + sk + off:.1f},{y + off:.1f} {x + w + sk + off:.1f},{y + off:.1f} "
                f"{x + w + off:.1f},{y + h + off:.1f} {x + off:.1f},{y + h + off:.1f}")

    y = 10
    for i, (a, b, lw, vw) in enumerate(parts):
        s.g("o pop", f"animation-delay:{0.9 + i * 0.12:.2f}s")
        s.poly(par(x, y, lw + vw, 38, 4), BLACK)
        s.poly(par(x, y, lw, 38), BLACK, WHITE, 2)
        s.poly(par(x + lw, y, vw, 38), WHITE, BLACK, 2)
        s.text(x + 13 + sk / 2, y + 24.5, a, "mono", 14, WHITE, 700, ls=2)
        s.text(x + lw + 14 + sk / 2, y + 29, b, "mono", 25, BLACK, 800)
        s.end()
        x += lw + vw + 16
    s.save(OUT, "stats.svg")


# ------------------------------------------------------------------ section stickers
def sticker(name, txt, dark=False, rot=-1.6, seed=3, key="mono", size=32, alt=None, weight=800):
    tw_ = text_width(key, weight, size, txt)
    w_, h_ = tw_ + 64, size * 1.85
    s = Svg(round(w_ + 44), round(h_ + 40), alt or txt)
    fill, ink, edge, sh = (BLACK, WHITE, WHITE, WHITE) if dark else (WHITE, BLACK, BLACK, BLACK)
    x, y = 22, 20
    pts = jag(x, y, w_, h_, 2.4, seed, 15)
    tr = f"rotate({rot} {x + w_ / 2:.1f} {y + h_ / 2:.1f})"
    s.g("o pop")
    s.g("o wob", f"--a:1deg;--d:{1.7 + seed % 3 * 0.25:.2f}s;animation-delay:-{seed * 0.13:.2f}s")
    s.poly(pts, sh, edge, 2.5, transform=f"{tr} translate(6 6)")
    s.poly(pts, fill, edge, 2.5, transform=tr)
    s.text(x + w_ / 2, y + h_ / 2 + cap_height(key, weight, size) / 2, txt, key, size, ink, weight, anchor="middle", transform=tr)
    s.g("o spin", f"animation-duration:{6 + seed % 4}s")
    s.poly(star_points(x + 4, y + 4, 19, 9, 8, 0.3), ink if dark else BLACK, edge, 2, transform=tr)
    s.end()
    s.rect(x + w_ - 66, y - 12, 54, 18, WHITE if dark else BLACK, BLACK if dark else WHITE, 1.5,
           transform=f"rotate(9 {x + w_ - 40} {y})")
    s.end()
    s.end()
    s.save(OUT, f"head-{name}.svg")


# ------------------------------------------------------------------ who am I: polaroid
def whoami_art():
    Wd, Hd = 292, 380
    s = Svg(Wd, Hd, "Portrait of Omar, halftone print")
    s.g("o sway")
    tr = "rotate(-2.2 146 190)"
    fr = jag(14, 12, 258, 348, 1.6, 21, 17)
    s.poly(fr, BLACK, transform=f"{tr} translate(8 8)")
    s.poly(fr, WHITE, BLACK, 3, transform=tr)
    s.add(f'<g transform="{tr}">')
    s.defs.append('<clipPath id="ph"><rect x="30" y="28" width="226" height="262"/></clipPath>')
    s.rect(30, 28, 226, 262, BLACK)
    s.add('<g clip-path="url(#ph)">')
    g = s.gradient([(0, WHITE, 0.30), (1, WHITE, 0)], 0.5, 0.25, 0.9, kind="radial")
    s.rect(30, 28, 226, 262, g)
    ph_h = 226 * PH / PW
    s.add(f'<image href="data:image/png;base64,{PNG}" x="30" y="34" width="226" height="{ph_h:.1f}"/>')
    s.add("</g>")
    s.rect(30, 28, 226, 262, "none", BLACK, 2)
    s.text(143, 336, "Omar, aka Mitaro", "mono", 20, BLACK, 800, anchor="middle")
    s.rect(40, 2, 62, 20, BLACK, WHITE, 1.5, transform="rotate(-10 70 12)")
    s.rect(196, 4, 62, 20, BLACK, WHITE, 1.5, transform="rotate(8 226 14)")
    s.add("</g>")
    s.end()
    s.save(OUT, "whoami.svg")


# ------------------------------------------------------------------ contact buttons
def button(file, brand, kind, handle, k):
    s = Svg(268, 68, f"{kind}: {handle}")
    s.g("o wob", f"--a:.7deg;--d:{1.8 + k * 0.3:.1f}s;animation-delay:-{k * 0.5}s")
    pts = jag(5, 5, 250, 52, 1.4, len(handle), 16)
    s.poly(pts, BLACK, transform="translate(5 5)")
    s.poly(pts, WHITE, BLACK, 2.5)
    s.icon(brand, 20, 17, 28, BLACK)
    s.text(64, 26, kind.upper(), "mono", 12, BLACK, 700, ls=3)
    s.text(64, 47, handle, "mono", 16, BLACK, 700)
    s.end()
    s.save(OUT, file)


# ------------------------------------------------------------------ numbers panel
def numbers():
    H = 330
    s = Svg(W, H, "By the numbers")
    pats = patterns(s)
    glow_panel(s, W, H)
    repos = DATA["repos"]
    years = date.today().year - int(DATA["created"][:4])
    code_kb = sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k not in NOT_CODE) // 1000
    big = [(str(len(repos)), "PUBLIC REPOS"), (str(sum(r["commits"] for r in repos)), "COMMITS"),
           (str(code_kb), "KB OF CODE"), (str(years), "YEARS ON GITHUB")]
    colw = (W - 80) / 4
    tg = s.gradient([(0, WHITE, 1), (1, WHITE, 0.25)], 0, 0, 0, 1)
    for i, (n, lab) in enumerate(big):
        x = 40 + i * colw
        s.g("rise", f"animation-delay:{0.15 + i * 0.14:.2f}s")
        s.text(x, 114, n, "mono", 80, tg, 800)
        s.text(x + 2, 144, lab, "mono", 14, WHITE, 700, ls=3)
        s.end()
        if i:
            s.line(x - 16, 60, x - 16, 146, WHITE, 1.2, dash="2 5")
    s.text(40, 200, "CODE BY LANGUAGE, ALL PROJECTS", "mono", 13, WHITE, 700, ls=3)
    lang_bar(s, 40, 214, W - 92, 30, agg_langs(CODE_REPOS), pats, legend_y=278, legend_size=14, cols=3,
             legend_dx=(W - 92) / 3, kb=True, delay=0.7)
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
        x, y = x0 + col * (tile_w + gap), y0 + row * (tile_h + 14)
        rot = rnd.uniform(-1.6, 1.6)
        pts = jag(x, y, tile_w, tile_h, 1.3, 40 + i, 16)
        tr = f"rotate({rot:.2f} {x + tile_w / 2:.1f} {y + tile_h / 2:.1f})"
        fill, ink = (WHITE, BLACK) if hot else (BLACK, WHITE)
        s.g("o pop", f"animation-delay:{0.1 + i * 0.06:.2f}s")
        s.g("o wob", f"--a:.9deg;--d:{1.4 + (i % 5) * 0.21:.2f}s;animation-delay:-{i * 0.23:.2f}s")
        s.poly(pts, fill, WHITE, 2, transform=tr)
        s.add(f'<g transform="{tr}">')
        s.icon(ic, x + tile_w / 2 - 19, y + 20, 38, ink)
        s.text(x + tile_w / 2, y + 87, name, "mono", 13.5, ink, 700, anchor="middle")
        s.add("</g>")
        s.end()
        s.end()
    ny = y0 + 2 * (tile_h + 14) + 12
    s.line(34, ny - 12, W - 46, ny - 12, WHITE, 1.2, dash="2 5")
    s.g("rise", "animation-delay:1.3s")
    s.text(36, ny + 14, "LEARNING NOW:", "mono", 15, WHITE, 800)
    s.text(176, ny + 14, "security basics, cleaner backend architecture, a Jarvis-style AI assistant", "mono", 14, WHITE, 500)
    s.end()
    s.save(OUT, "stack.svg")


# ------------------------------------------------------------------ project cards
PROJECTS = [
    dict(repo="VantaVault", file="project-vantavault.svg", n="01", name="VantaVault",
         tag="A private vault for external drives. No cloud.",
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
    label(s, 30, 26, p["n"], "mono", 20, "w", -3, int(p["n"]), 800, pad=12)
    tg = s.gradient([(0, WHITE, 1), (1, WHITE, 0.55)], 0, 0, 0, 1)
    s.g("rise")
    s.text(84, 56, p["name"], "mono", 38, tg, 800)
    s.end()
    s.text(32, 90, p["tag"], "mono", 14, WHITE, 500)
    s.line(32, 104, 540, 104, WHITE, 1.2, dash="2 5")
    for i, f in enumerate(p["feats"]):
        y = 134 + i * 34
        s.g("rise", f"animation-delay:{0.2 + i * 0.12:.2f}s")
        s.rect(32, y - 10, 9, 9, WHITE, transform=f"rotate(45 36.5 {y - 5.5})")
        s.text(52, y, f, "mono", 14, WHITE, 500)
        s.end()
    s.line(566, 30, 566, H - 42, WHITE, 1.2, dash="2 5")
    rx = 592
    rw = W - 34 - rx - 6
    s.text(rx, 46, "STACK", "mono", 12, WHITE, 700, ls=3)
    cx, cy = rx, 58
    for k, t in enumerate(p["stack"]):
        tw_ = text_width("mono", 700, 13, t) + 20
        if cx + tw_ > rx + rw:
            cx, cy = rx, cy + 30
        s.g("o pop", f"animation-delay:{0.3 + k * 0.1:.2f}s")
        s.rect(cx, cy, tw_, 24, BLACK, WHITE, 1.6, 12)
        s.text(cx + tw_ / 2, cy + 17, t, "mono", 13, WHITE, 700, anchor="middle")
        s.end()
        cx += tw_ + 8
    langs = sorted(r["langs"].items(), key=lambda kv: -kv[1])
    top = [(k, v) for k, v in langs if k in CODE_LANGS]
    other = sum(v for k, v in langs if k not in CODE_LANGS and k not in NOT_CODE)
    if other:
        top.append(("Other", other))
    s.text(rx, 132, "LANGUAGES", "mono", 12, WHITE, 700, ls=3)
    lang_bar(s, rx, 142, rw, 15, top, pats, legend_y=184, legend_size=12, cols=2, legend_dx=rw / 2, delay=0.5)
    y, m = r["created"].split("-")[0], MONTHS[int(r["created"].split("-")[1]) - 1]
    meta = [("CREATED", f"{m} {y}"), ("COMMITS", str(r["commits"])), ("STARS", str(r["stars"]))]
    for k, ((a_, b_), xx) in enumerate(zip(meta, [rx, rx + 104, rx + 188])):
        s.g("rise", f"animation-delay:{1.1 + k * 0.12:.2f}s")
        s.text(xx, 262, a_, "mono", 11, WHITE, 700, ls=2)
        s.text(xx, 288, b_, "mono", 20, WHITE, 800)
        s.end()
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
    total = (x1 + 48) - (x0 - 50)
    s.add(f'<line class="draw" style="--len:{total}px" x1="{x0 - 50}" y1="{ly}" x2="{x1 + 48}" y2="{ly}" '
          f'stroke="{WHITE}" stroke-width="3"/>')
    s.g("o pop", "animation-delay:1.5s")
    s.poly(f"{x1 + 46},{ly - 9} {x1 + 62},{ly} {x1 + 46},{ly + 9}", WHITE)
    s.end()
    for i, k in enumerate(keys):
        x = x0 + (x1 - x0) * i / (n - 1)
        up = i % 2 == 0
        yy, mm = k.split("-")
        d = 0.25 + i * 0.28
        s.g("o pop", f"animation-delay:{d:.2f}s")
        s.g("o spin", f"animation-duration:{9 + i}s")
        s.poly(star_points(x, ly, 15, 7, 8, i), WHITE, BLACK, 2)
        s.end()
        s.end()
        s.g("rise", f"animation-delay:{d + 0.25:.2f}s")
        s.line(x, ly + (-17 if up else 17), x, ly + (-38 if up else 38), WHITE, 1.6, dash="2 4")
        lines = []
        for item in ev[k]:
            lines += wrap(item, "mono", 500, 14, 176)
        lines = lines[:4]
        if up:
            y0 = ly - 56 - (len(lines) - 1) * 18
            date_y = y0 - 28
        else:
            date_y, y0 = ly + 66, ly + 92
        s.text(x, date_y, f"{MONTHS[int(mm) - 1]} {yy}", "mono", 19, WHITE, 800, anchor="middle")
        for j, ln in enumerate(lines):
            s.text(x, y0 + j * 18, ln, "mono", 14, WHITE, 500, anchor="middle")
        s.end()
    s.save(OUT, "timeline.svg")


# ------------------------------------------------------------------ commit reel
REPO_NAMES = {"KworkingSystem": "Campus Coworking"}
SKIP_MSG = ("Initial commit", "Merge ")


def reel():
    H = 240
    s = Svg(W, H, "Commit reel: a film strip of my latest real commits")
    allc = [c for c in DATA["commits"] if not c["msg"].startswith(SKIP_MSG)]
    frames = allc[:30]
    n = len(frames)
    FW, GAP = 196, 14
    pitch = FW + GAP                      # 210 = 7 sprocket holes of 30px, so the loop is seamless
    total = n * pitch
    mark = len(s.body)
    fy = 58
    for i, c in enumerate(frames):
        fx = i * pitch + GAP / 2
        inv = i % 3 == 1                                  # every third frame is "exposed": white
        bg, ink = (WHITE, BLACK) if inv else (BLACK, WHITE)
        for k in range(7):
            hx = fx - GAP / 2 + 6 + k * 30
            s.rect(hx, 34, 18, 12, WHITE, rx=3)
            s.rect(hx, 194, 18, 12, WHITE, rx=3)
        s.rect(fx, fy, FW, 124, bg, WHITE, 2)
        y, m, d = c["ts"][:10].split("-")
        s.text(fx + 12, fy + 21, f"#{len(allc) - i:03d}", "mono", 12, ink, 700, ls=1)
        s.text(fx + FW - 12, fy + 21, f"{d} {MONTHS[int(m) - 1]} {y}", "mono", 12, ink, 700, anchor="end", ls=0.5)
        s.line(fx + 12, fy + 30, fx + FW - 12, fy + 30, ink, 1.2, dash="2 4")
        lines = wrap(c["msg"], "mono", 500, 16, FW - 26)
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2][:max(1, len(lines[2]) - 3)].rstrip() + "..."
        for j, ln in enumerate(lines):
            s.text(fx + 12, fy + 55 + j * 21, ln, "mono", 16, ink, 500)
        tag = REPO_NAMES.get(c["repo"], c["repo"]).upper()
        tw_ = text_width("mono", 700, 11.5, tag, 1.2) + 14
        s.rect(fx + 12, fy + 104, tw_, 16, ink)
        s.text(fx + 19, fy + 116, tag, "mono", 11.5, bg, 700, ls=1.2)
    chunk = s.body[mark:]
    del s.body[mark:]
    s.defs.append('<g id="reelframes">' + "".join(chunk) + "</g>")
    s.defs.append('<clipPath id="stripclip"><rect x="0" y="0" width="888" height="240"/></clipPath>')
    s.add('<g transform="rotate(-1.2 444 120)">')
    s.rect(-30, 24, W + 60, 192, BLACK, WHITE, 2.5)
    s.add('<g clip-path="url(#stripclip)">')
    s.g("marq", f"--shift:-{total}px;animation-duration:{total / 38:.0f}s")
    s.add(f'<use href="#reelframes"/><use href="#reelframes" x="{total}"/>')
    s.end()
    s.add("</g>")
    fadeL = s.gradient([(0, BLACK, 1), (1, BLACK, 0)], 0, 0, 1, 0)
    fadeR = s.gradient([(0, BLACK, 0), (1, BLACK, 1)], 0, 0, 1, 0)
    s.rect(-30, 26, 90, 188, fadeL)
    s.rect(W - 60, 26, 90, 188, fadeR)
    s.add("</g>")
    label(s, 24, 4, f"{len(allc)} FRAMES / 1 REAL COMMIT EACH", "mono", 13, "w", -1.2, 4, 700, ls=1.2)
    s.save(OUT, "reel.svg")


# ------------------------------------------------------------------ footer
def footer():
    H = 150
    s = Svg(W, H, "Thanks for reading")
    s.defs.append(f'<clipPath id="cp"><rect width="{W}" height="{H}" rx="6"/></clipPath>')
    s.add('<g clip-path="url(#cp)">')
    s.rect(0, 0, W, H, WHITE)
    under = s.gradient([(0, BLACK, 1), (0.3, BLACK, 1), (0.65, BLACK, 0.4), (1, BLACK, 0)], 0, 0, 1, 0.15)
    s.rect(0, 0, W, H, under)
    halftone_field(s, 330, 880, -10, H + 10, pitch=10.5, slope=0.2, reverse=True)
    s.rect(0, 0, 370, H, BLACK)
    s.g("o wob", "--a:.8deg;--d:1.6s")
    s.text(34, 70, "thanks for reading.", "mono", 28, WHITE, 800)
    s.end()
    s.text(36, 98, "generated by a Python script, see /scripts", "mono", 13, WHITE, 500)
    label(s, W - 272, 34, "© 2026 MITARO", "mono", 16, "b", 1.6, 9, 700, ls=2)
    unit = "THANKS FOR READING  ///  MITARO  ///  "
    uw = text_width("mono", 700, 13, unit, 2.4)
    s.add('<g transform="rotate(-1.4 444 130)">')
    s.rect(-30, 116, W + 60, 28, BLACK, WHITE, 2)
    s.g("marq", f"--shift:-{uw:.1f}px;animation-duration:20s;animation-direction:reverse")
    s.text(-uw, 136, unit * 4, "mono", 13, WHITE, 700, ls=2.4)
    s.end()
    s.add("</g>")
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
    button("btn-telegram.svg", "telegram", "Telegram", "@treadways", 0)
    button("btn-email.svg", "gmail", "Email", "miri.saro@bk.ru", 1)
    button("btn-instagram.svg", "instagram", "Instagram", "@stere.os", 2)
    numbers()
    stack()
    for p in PROJECTS:
        project_card(p)
    timeline()
    reel()
    sticker("reel", "THE COMMIT REEL", dark=True, rot=-1.4, seed=15)
    footer()
