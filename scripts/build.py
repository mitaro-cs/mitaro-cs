#!/usr/bin/env python3
"""Builds every SVG of the profile README into ../assets from scripts/data.json.

Concept: the profile is a film. The avatar is a still from one, so the page reads like one:
an opening frame, numbered scenes with screenplay slug lines, dailies, box office, end credits.
Palette rule: only the ten colours pulled from the avatar (lib.PALETTE), nothing else.
Type: Instrument Serif for titles, JetBrains Mono for everything that is data.
Motion: CSS/SMIL only (film flicker, fades, a rolling strip); it stops under prefers-reduced-motion.
"""
import base64
import json
import math
import os
import re
import struct
import sys
from datetime import date

from lib import BENCH, CLAY, LEAF, MIST, NIGHT, PALETTE, SHADE, SHIRT, SKIN, STONE, WOOD, Svg, text_width

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
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]
NOT_CODE = {"Rich Text Format"}
LANG_COLOR = {"Java": SKIN, "Svelte": CLAY, "Python": SHIRT, "TypeScript": MIST, "JavaScript": STONE,
              "CSS": WOOD, "HTML": LEAF, "Other": BENCH}


# ------------------------------------------------------------------ data helpers
def bucket_langs(langs, min_pct):
    """Groups a {language: bytes} dict into known languages plus 'Other'; tiny slices fold into 'Other'."""
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


def agg_langs(repos):
    tot = {}
    for r in repos:
        for k, v in r["langs"].items():
            tot[k] = tot.get(k, 0) + v
    return bucket_langs(tot, 4)


def code_size(kb):
    """(value, unit) for the amount of code: megabytes once it passes 1000 KB."""
    return (f"{kb / 1000:.1f}", "MB") if kb >= 1000 else (str(kb), "KB")


def code_kb():
    return sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k not in NOT_CODE) // 1000


def commits():
    return sum(r["commits"] for r in DATA["repos"])


def wrap(txt, key, weight, size, maxw):
    """Greedy word wrap; long hyphenated names may also break after a hyphen."""
    lines, cur = [], ""
    for wd in re.findall(r"\S+?-(?=\S)|\S+\s*", txt):
        t = cur + wd
        if text_width(key, weight, size, t.strip()) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur.strip())
            cur = wd
    lines.append(cur.strip())
    return lines


# ------------------------------------------------------------------ shared drawing bits
def kicker(s, x, y, txt, fill=WOOD, size=11, anchor="start", ls=3, weight=700):
    """Small spaced capitals: the voice of every label, slug line and credit."""
    s.text(x, y, txt, "mono", size, fill, weight, anchor=anchor, ls=ls)


def card(s, h, glow=(0.88, 0.0), w=W):
    """Opens a rounded shade card lit like the avatar: green from the trees, warm halation from the sun."""
    cid = s.uid("c")
    s.defs.append(f'<clipPath id="{cid}"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.rect(0, 0, w, h, SHADE)
    s.rect(0, 0, w, h, s.gradient([(0, LEAF, 0.55), (1, LEAF, 0)], 1 - glow[0], 1 - glow[1], 0.9, kind="radial"))
    s.rect(0, 0, w, h, s.gradient([(0, SKIN, 0.13), (1, SKIN, 0)], glow[0], glow[1], 0.7, kind="radial"))


def card_end(s, h, w=W, grain=0.07):
    s.grain(grain, w, h)
    s.add("</g>")
    s.rect(1, 1, w - 2, h - 2, "none", BENCH, 1.5, 16)


def dots_path(x0, x1, y0, y1, pitch=9.0):
    """Path data of a rotated halftone grid whose dots grow towards the bottom right."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ca = sa = math.sqrt(0.5)
    n = int(math.hypot(x1 - x0, y1 - y0) / pitch) + 2
    d = []
    for i in range(-n, n):
        for j in range(-n, n):
            u, v = i * pitch, j * pitch
            x, y = cx + u * ca - v * sa, cy + u * sa + v * ca
            if not (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            t = (x - x0) / (x1 - x0) * 0.4 + (y - y0) / (y1 - y0) * 0.6
            r = pitch * 0.42 * t * t
            if r < 0.4:
                continue
            d.append(f"M{x - r:.1f} {y:.1f}a{r:.1f} {r:.1f} 0 1 0 {2 * r:.1f} 0a{r:.1f} {r:.1f} 0 1 0 {-2 * r:.1f} 0z")
    return "".join(d)


def lang_bar(s, x, y, w, h, langs, delay=0.4):
    """Rounded bar of code by language, segments in palette colours with a hairline gap."""
    items = [(k, v) for k, v in langs if k not in NOT_CODE]
    total = sum(v for _, v in items) or 1
    cid = s.uid("lb")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}"/></clipPath>')
    s.rect(x, y, w, h, NIGHT, rx=h / 2)
    s.add(f'<g clip-path="url(#{cid})">')
    s.g("grow", f"animation-delay:{delay}s")
    cx = x
    for k, v in items:
        seg = w * v / total
        s.rect(cx, y, max(0.0, seg - 2), h, LANG_COLOR.get(k, BENCH))
        cx += seg
    s.end()
    s.add("</g>")
    return items, total


def legend(s, x, y, items, total, cols, dx, size=12, kb=False, delay=0.8):
    for i, (k, v) in enumerate(items):
        lx, ly = x + (i % cols) * dx, y + (i // cols) * 24
        s.g("rise", f"animation-delay:{delay + i * 0.07:.2f}s")
        s.add(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{LANG_COLOR.get(k, BENCH)}" stroke="{WOOD}" '
              f'stroke-width=".8"/>')
        s.text(lx + 18, ly, k, "mono", size, MIST, 600)
        s.text(lx + 18 + text_width("mono", 600, size, k + " "), ly,
               f"{round(100 * v / total)}%" + (f" · {v // 1000} KB" if kb else ""), "mono", size, WOOD, 500)
        s.end()


# ------------------------------------------------------------------ opening frame
def hero():
    H, y0, y1 = 420, 46, 374
    s = Svg(W, H, "Mitaro. Computer science student at MTUCI. Python, Flask, Java, security.",
            "An opening film frame in the colours of the avatar: letterbox bars, the title Mitaro, "
            "a duotone halftone portrait and a subtitle that says hi, I'm Omar.")
    s.defs.append(f'<clipPath id="hc"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
                  f'<clipPath id="fc"><rect x="0" y="{y0}" width="{W}" height="{y1 - y0}"/></clipPath>')
    s.add('<g clip-path="url(#hc)">')
    s.rect(0, 0, W, H, NIGHT)

    # the frame: park light. Trees top left, warm sun behind the head, bench brown at the bottom
    s.add('<g clip-path="url(#fc)" class="flick">')
    s.rect(0, y0, W, y1 - y0, s.gradient([(0, SHADE, 1), (0.6, SHADE, 1), (1, BENCH, 1)], 0, 0, 0.2, 1))
    s.rect(0, y0, W, y1 - y0, s.gradient([(0, LEAF, 0.95), (1, LEAF, 0)], 0.12, 0.05, 0.75, kind="radial"))
    s.rect(0, y0, W, y1 - y0, s.gradient([(0, SKIN, 0.30), (0.5, CLAY, 0.08), (1, CLAY, 0)], 0.76, 0.32, 0.5,
                                         kind="radial"))

    # duotone halftone portrait: the dots mask a skin-to-shirt gradient, so the face is warm and the
    # shirt is blue, as in the avatar. Two copies 1px apart swap in steps: projector judder
    pw = 352
    ph = pw * PH / PW
    px, py = W - pw - 26, y1 - ph + 8
    box = f'x="{px - 4}" y="{py - 4:.0f}" width="{pw + 8}" height="{ph + 8:.0f}"'
    fade = s.gradient([(0, "#000", 0), (0.30, "#fff", 1), (1, "#fff", 1)], 0, 0, 1, 0)
    tone = s.gradient([(0, SKIN, 1), (0.42, SKIN, 1), (0.62, STONE, 1), (0.8, SHIRT, 1), (1, SHIRT, 1)], 0, 0, 0, 1)
    s.defs.append(f'<image id="pimg" href="data:image/png;base64,{PNG}" x="{px}" y="{py:.0f}" width="{pw}" '
                  f'height="{ph:.0f}"/>')
    s.defs.append(f'<mask id="pm" maskUnits="userSpaceOnUse" {box}><rect {box} fill="{fade}"/></mask>')
    for mid, off in (("pdA", ""), ("pdB", ' x="1.4" y="-1"')):
        s.defs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" {box}><use href="#pimg"{off}/></mask>')
    s.add(f'<g mask="url(#pm)" class="fade"><rect {box} fill="{tone}" mask="url(#pdA)" class="fA"/>'
          f'<rect {box} fill="{tone}" mask="url(#pdB)" class="fB"/></g>')

    # title block
    s.g("rise", "animation-delay:.2s")
    kicker(s, 48, 108, "MTUCI  ·  COMPUTER SCIENCE  ·  SINCE 2022", STONE)
    s.end()
    s.g("rise", "animation-delay:.35s")
    s.text(42, 232, "Mitaro", "serif", 150, MIST)
    s.end()
    s.g("rise", "animation-delay:.55s")
    s.text(48, 280, "a local-first story", "italic", 34, SKIN)
    s.end()
    s.g("rise", "animation-delay:.75s")
    kicker(s, 48, 326, "PYTHON  ·  FLASK  ·  JAVA  ·  SECURITY", SHIRT, 12)
    s.end()

    # viewfinder corners
    for cx, cy, dx, dy in ((22, y0 + 18, 1, 1), (W - 22, y0 + 18, -1, 1), (22, y1 - 18, 1, -1), (W - 22, y1 - 18, -1, -1)):
        s.path(f"M{cx} {cy + 20 * dy}V{cy}H{cx + 20 * dx}", stroke=MIST, sw=1.5, opacity=0.55)
    s.add("</g>")

    # letterbox bars: recording state, slate and the subtitle
    s.add(f'<circle cx="40" cy="25" r="4.5" fill="{SKIN}" class="blink"/>')
    kicker(s, 54, 29, "REC", MIST)
    kicker(s, W / 2, 29, f"SC. 01  ·  TAKE {commits()}", WOOD, anchor="middle")
    kicker(s, W - 40, 29, "35 MM  ·  2.39 : 1", WOOD, anchor="end")
    s.g("fade", "animation-delay:1.1s")
    s.text(W / 2, 405, "Hi, I'm Omar. I build software that keeps your data at home.", "italic", 21, MIST,
           anchor="middle")
    s.end()
    s.grain(0.09)
    s.add("</g>")
    s.rect(1, 1, W - 2, H - 2, "none", BENCH, 1.5, 16)
    s.save(OUT, "hero.svg")


# ------------------------------------------------------------------ slate: the numbers in one row
def slate():
    H = 104
    items = [("REPOS", str(len(DATA["repos"]))), ("COMMITS", str(commits())),
             ("STARS", str(sum(r["stars"] for r in DATA["repos"]))), ("FOLLOWERS", str(DATA["followers"])),
             ("CODE", " ".join(code_size(code_kb())))]
    s = Svg(W, H, "GitHub in numbers: " + ", ".join(f"{a} {b}" for a, b in items))
    card(s, H, glow=(0.5, 0.0))
    cw = (W - 48) / len(items)
    for i, (a, b) in enumerate(items):
        x = 24 + i * cw + 22
        s.g("rise", f"animation-delay:{0.1 + i * 0.1:.2f}s")
        kicker(s, x, 40, a, SKIN if i == 1 else WOOD, 10.5)
        s.text(x - 2, 82, b, "serif", 44, MIST)
        s.end()
        if i:
            s.line(24 + i * cw, 26, 24 + i * cw, H - 26, BENCH, 1.2)
    card_end(s, H)
    s.save(OUT, "slate.svg")


# ------------------------------------------------------------------ scene headings
SCENES = [("about", "01", "Who I am", "INT. LECTURE HALL, MTUCI — DAY"),
          ("build", "02", "Feature presentation", "EXT. CAMPUS — MORNING"),
          ("stack", "03", "The toolkit", "INT. TERMINAL — LATE NIGHT"),
          ("reel", "04", "Dailies", "INT. EDITING ROOM — CONTINUOUS"),
          ("numbers", "05", "Box office", "EXT. GITHUB — ALL DAY"),
          ("timeline", "06", "Chapters", "MONTAGE — 2022 TO NOW"),
          ("now", "07", "Now shooting", "EXT. PARK BENCH — LATER")]


def scene_head(name, n, title, slug):
    H = 76
    s = Svg(W, H, f"Scene {n}: {title}")
    s.defs.append(f'<clipPath id="sh"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>')
    s.add('<g clip-path="url(#sh)">')
    s.rect(0, 0, W, H, NIGHT)
    s.rect(0, 0, W, H, s.gradient([(0, LEAF, 0.6), (1, LEAF, 0)], 0, 0.5, 0.45, kind="radial"))
    s.add("</g>")
    s.g("rise")
    s.text(26, 52, n, "italic", 40, SKIN)
    s.text(30 + text_width("italic", 400, 40, n) + 14, 52, title, "serif", 40, MIST)
    s.end()
    s.g("fade", "animation-delay:.3s")
    kicker(s, W - 28, 44, slug, WOOD, 10.5, anchor="end", ls=2.4)
    s.end()
    s.rect(1, 1, W - 2, H - 2, "none", BENCH, 1.5, 14)
    s.save(OUT, f"head-{name}.svg")


# ------------------------------------------------------------------ contact tickets
def ticket(file, brand, kind, handle, accent):
    w, h = 280, 64
    s = Svg(w, h, f"{kind}: {handle}")
    s.defs.append(f'<clipPath id="tk"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12"/></clipPath>')
    s.add('<g clip-path="url(#tk)">')
    s.rect(0, 0, w, h, SHADE)
    s.rect(0, 0, 62, h, accent)
    s.add("</g>")
    s.line(62, 8, 62, h - 8, NIGHT, 2, dash="3 4")
    s.icon(brand, 19, 20, 24, NIGHT)
    kicker(s, 80, 27, kind.upper(), WOOD, 10.5)
    s.text(80, 47, handle, "mono", 15, MIST, 700)
    s.rect(1, 1, w - 2, h - 2, "none", BENCH, 1.5, 12)
    s.save(OUT, file)


# ------------------------------------------------------------------ director's notes
RULES = ["Working product beats endless planning.",
         "Readable code beats clever code.",
         "Anything that touches user data gets security from day one."]


def notes():
    H = 222
    s = Svg(W, H, "Director's notes: " + " ".join(RULES))
    card(s, H, glow=(0.1, 1.0))
    kicker(s, 36, 44, "DIRECTOR'S NOTES", SKIN)
    for i, line in enumerate(RULES):
        y = 96 + i * 44
        s.g("rise", f"animation-delay:{0.15 + i * 0.15:.2f}s")
        s.text(36, y, ["i.", "ii.", "iii."][i], "italic", 28, SKIN)
        s.text(84, y, line, "serif", 29, MIST)
        s.end()
    card_end(s, H)
    s.save(OUT, "notes.svg")


# ------------------------------------------------------------------ feature: project poster card
PROJECTS = [
    dict(repo="StorageSystem", file="project-groupbase.svg", title=["group", "base"],
         tag="A study-group app that runs on the group leader's own PC.",
         feats=["Works offline, syncs when the host computer is back on",
                "Files encrypted on disk, AES-256-GCM, a key per file",
                "Sign in with a QR code, a fingerprint or Face ID",
                "Roles, moderation, deadlines and an exam countdown",
                "Host app for Windows and macOS, updates in one click"],
         stack=["Java", "Spring Boot", "Svelte", "Tauri"]),
    dict(repo="VantaVault", file="project-vantavault.svg", title=["Vanta", "Vault"],
         tag="A private vault for external drives. No cloud.",
         feats=["Password access, hashed locally with PBKDF2-SHA256",
                "Local AES-encrypted archives you can restore in a click",
                "Session protection and a timed lockout after failed logins",
                "Finds external drives automatically",
                "Runs on macOS and Windows, from source or as an app"],
         stack=["Python", "JavaScript", "HTML", "CSS"]),
    dict(repo="AetherCloud", file="project-aethercloud.svg", title=["Aether", "Cloud"],
         tag="Turns your own disk into a private cloud.",
         feats=["Nested folders, file and folder upload, downloads",
                "Image previews and generated file-type badges",
                "Per-user storage quota, storage meter, recent files",
                "Sync check between the database and real files on disk",
                "Installable PWA; runs on Docker Compose or gunicorn"],
         stack=["Flask", "SQLite", "PWA", "Docker"]),
    dict(repo="KworkingSystem", file="project-coworking.svg", title=["Campus", "Coworking"],
         tag="A booking panel for a university coworking space.",
         feats=["Seat booking with overlap and capacity checks",
                "Check-in by student ID and confirmation of the rules",
                "Profiles with avatars and per-user interface themes",
                "Pomodoro 25/5, lofi streams and a study library",
                "REST API for spots, bookings, profile and check-in"],
         stack=["Flask", "SQLite", "Vanilla JS", "REST"]),
]
SHOWCASE = ["KworkingSystem"]   # repos whose cards are built, in this order


def feature(p, n):
    H = 404
    r = REPO[p["repo"]]
    name = " ".join(p["title"])
    s = Svg(W, H, f"Feature {n:02d}, {name}: " + p["tag"], " ".join(p["feats"]))
    card(s, H)

    # the poster
    px, py, pw, ph = 22, 22, 252, H - 44
    s.defs.append(f'<clipPath id="pc"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10"/></clipPath>')
    s.add('<g clip-path="url(#pc)">')
    s.rect(px, py, pw, ph, s.gradient([(0, LEAF, 1), (0.55, SHADE, 1), (1, NIGHT, 1)], 0, 0, 0, 1))
    s.rect(px, py, pw, ph, s.gradient([(0, SKIN, 0.35), (1, SKIN, 0)], 0.9, 0.95, 0.75, kind="radial"))
    s.path(dots_path(px, px + pw, py + ph * 0.35, py + ph), fill=SKIN, opacity=0.35)
    s.add("</g>")
    s.rect(px, py, pw, ph, "none", BENCH, 1.5, 10)
    kicker(s, px + 20, py + 34, f"FEATURE {n:02d}", SKIN, 10.5)
    s.g("rise", "animation-delay:.15s")
    for k, word in enumerate(p["title"]):
        s.text(px + 18, py + 104 + k * 50, word, "serif", 54, MIST)
    s.end()
    y_, m_ = r["created"].split("-")[:2]
    s.text(px + 20, py + 104 + len(p["title"]) * 50 + 4, f"in theatres {MONTHS[int(m_) - 1].lower()} {y_}",
           "italic", 20, STONE)
    cx, cy = px + 18, py + ph - 70
    for k, t in enumerate(p["stack"]):
        tw_ = text_width("mono", 700, 11, t) + 18
        if cx + tw_ > px + pw - 14:
            cx, cy = px + 18, cy + 30
        s.g("rise", f"animation-delay:{0.4 + k * 0.08:.2f}s")
        s.rect(cx, cy, tw_, 22, NIGHT, STONE, 1, 11, opacity=0.9)
        s.text(cx + tw_ / 2, cy + 15, t, "mono", 11, STONE, 700, anchor="middle")
        s.end()
        cx += tw_ + 6

    # the synopsis
    rx = 306
    kicker(s, rx, 50, "SYNOPSIS", WOOD)
    s.text(rx, 86, p["tag"], "italic", 25, MIST)
    for i, f in enumerate(p["feats"]):
        y = 130 + i * 30
        s.g("rise", f"animation-delay:{0.25 + i * 0.1:.2f}s")
        s.text(rx, y, "—", "mono", 14, SKIN, 700)
        s.text(rx + 24, y, f, "mono", 13.5, STONE, 500)
        s.end()
    s.line(rx, 286, W - 34, 286, BENCH, 1.2)
    meta = [("RELEASED", f"{MONTHS[int(m_) - 1].capitalize()} {y_}"), ("COMMITS", str(r["commits"])),
            ("RELEASE", r["release"]) if r.get("release") else ("STARS", str(r["stars"]))]
    x = rx
    for k, (a_, b_) in enumerate(meta):
        s.g("rise", f"animation-delay:{0.9 + k * 0.1:.2f}s")
        kicker(s, x, 318, a_, WOOD, 10)
        s.text(x, 354, b_, "serif", 32, MIST)
        s.end()
        x += max(text_width("serif", 400, 32, b_), text_width("mono", 700, 10, a_, 3)) + 30
    lx = max(x + 6, rx + 290)
    lw = W - 34 - lx
    kicker(s, lx, 318, "LANGUAGES", WOOD, 10)
    items, total = lang_bar(s, lx, 330, lw, 10, bucket_langs(r["langs"], 3), delay=0.6)
    legend(s, lx, 362, items[:4], total, 2, lw / 2, size=11, delay=1.0)
    card_end(s, H)
    s.save(OUT, p["file"])


# ------------------------------------------------------------------ the toolkit
STACK = [("python", "Python", 1), ("flask", "Flask", 1), ("openjdk", "Java", 1), ("springboot", "Spring", 0),
         ("svelte", "Svelte", 0), ("typescript", "TypeScript", 0), ("javascript", "JavaScript", 0), ("html5", "HTML5", 0),
         ("css3", "CSS3", 0), ("sqlite", "SQLite", 0), ("docker", "Docker", 0), ("git", "Git", 0),
         ("github", "GitHub", 0), ("githubactions", "Actions", 0), ("gnubash", "Bash", 0), ("linux", "Linux", 0),
         ("figma", "Figma", 0), ("obsidian", "Obsidian", 0), ("rust", "Rust", 0), ("tauri", "Tauri", 0),
         ("zedindustries", "Zed", 0)]


def stack():
    cols, gap, ch = 6, 10, 46
    cw = (W - 64 - gap * (cols - 1)) / cols
    rows = (len(STACK) + cols - 1) // cols
    H = 32 + rows * (ch + gap) + 64
    s = Svg(W, H, "Tech stack: " + ", ".join(n for _, n, _ in STACK))
    card(s, H, glow=(0.1, 0.0))
    for i, (ic, name, hot) in enumerate(STACK):
        x, y = 32 + (i % cols) * (cw + gap), 32 + (i // cols) * (ch + gap)
        s.g("rise", f"animation-delay:{0.05 + i * 0.035:.2f}s")
        s.rect(x, y, cw, ch, NIGHT if hot else SHADE, SKIN if hot else BENCH, 1.3, 10, opacity=0.95)
        s.icon(ic, x + 15, y + 13, 20, SKIN if hot else STONE)
        s.text(x + 46, y + 28, name, "mono", 13, MIST if hot else STONE, 700 if hot else 500)
        s.end()
    ny = 32 + rows * (ch + gap) + 28
    kicker(s, 34, ny, "LEARNING NOW", SKIN, 10.5)
    s.text(150, ny, "security basics, cleaner backend architecture, a Jarvis-style AI assistant", "mono", 13,
           STONE, 500)
    card_end(s, H)
    s.save(OUT, "stack.svg")


# ------------------------------------------------------------------ dailies: the commit reel
REPO_NAMES = {"KworkingSystem": "Campus Coworking", "StorageSystem": "groupbase"}
SKIP_MSG = ("Initial commit", "Merge ")


def reel():
    H = 252
    s = Svg(W, H, "Dailies: a film strip of my latest real commits")
    allc = [c for c in DATA["commits"] if not c["msg"].startswith(SKIP_MSG)]
    seen, frames = {}, []
    for c in allc:                        # allc is newest first
        if seen.get(c["repo"], 0) < 8:
            seen[c["repo"]] = seen.get(c["repo"], 0) + 1
            frames.append(c)
    frames = frames[:30]
    order = {id(c): i for i, c in enumerate(allc)}
    FW, GAP = 196, 14
    pitch = FW + GAP                      # 210 = 7 sprocket holes of 30px, so the loop is seamless
    total = len(frames) * pitch
    mark = len(s.body)
    fy = 56
    for i, c in enumerate(frames):
        fx = i * pitch + GAP / 2
        lit = i % 4 == 1                                  # every fourth frame is overexposed: shirt or skin
        bg, ink, sub = ((SHIRT, SKIN)[i // 4 % 2], NIGHT, BENCH) if lit else (SHADE, MIST, WOOD)
        for k in range(7):
            hx = fx - GAP / 2 + 6 + k * 30
            s.rect(hx, 34, 18, 11, WOOD, rx=3)
            s.rect(hx, 191, 18, 11, WOOD, rx=3)
        s.rect(fx, fy, FW, 124, bg, BENCH, 1.5, 6)
        y, m, d = c["ts"][:10].split("-")
        s.text(fx + 12, fy + 21, f"#{len(allc) - order[id(c)]:03d}", "mono", 11.5, sub, 700, ls=1)
        s.text(fx + FW - 12, fy + 21, f"{d} {MONTHS[int(m) - 1]} {y}", "mono", 11.5, sub, 700, anchor="end")
        lines = wrap(c["msg"], "mono", 500, 15, FW - 26)
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2][:max(1, len(lines[2]) - 3)].rstrip() + "..."
        for j, ln in enumerate(lines):
            s.text(fx + 12, fy + 50 + j * 20, ln, "mono", 15, ink, 500)
        tag = REPO_NAMES.get(c["repo"], c["repo"]).upper()
        s.text(fx + 12, fy + 112, tag, "mono", 10.5, sub, 700, ls=1.6)
    chunk = s.body[mark:]
    del s.body[mark:]
    s.defs.append('<g id="reelframes">' + "".join(chunk) + "</g>")
    s.defs.append(f'<clipPath id="strip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16"/></clipPath>')
    s.add('<g clip-path="url(#strip)">')
    s.rect(0, 0, W, H, NIGHT)
    s.add('<g transform="translate(0 26)">')
    s.g("marq", f"--shift:-{total}px;animation-duration:{total / 36:.0f}s")
    s.add(f'<use href="#reelframes"/><use href="#reelframes" x="{total}"/>')
    s.end()
    s.add("</g>")
    s.rect(0, 0, 90, H, s.gradient([(0, NIGHT, 1), (1, NIGHT, 0)], 0, 0, 1, 0))
    s.rect(W - 90, 0, 90, H, s.gradient([(0, NIGHT, 0), (1, NIGHT, 1)], 0, 0, 1, 0))
    s.add("</g>")
    s.rect(1, 1, W - 2, H - 2, "none", BENCH, 1.5, 16)
    kicker(s, 26, 34, f"{len(allc)} TAKES  ·  ONE REAL COMMIT EACH  ·  NEWEST FIRST", SKIN, 10.5)
    s.save(OUT, "reel.svg")


# ------------------------------------------------------------------ box office
def box_office():
    H = 344
    s = Svg(W, H, "Box office: repositories, commits, code and years on GitHub, plus code by language")
    card(s, H, glow=(0.95, 0.1))
    years = date.today().year - int(DATA["created"][:4])
    val, unit = code_size(code_kb())
    big = [(str(len(DATA["repos"])), "PUBLIC REPOS"), (str(commits()), "COMMITS"),
           (val, f"{unit} OF CODE"), (str(years), "YEARS ON GITHUB")]
    colw = (W - 72) / 4
    for i, (n, lab) in enumerate(big):
        x = 40 + i * colw
        s.g("rise", f"animation-delay:{0.1 + i * 0.12:.2f}s")
        s.text(x - 3, 122, n, "serif", 96, SKIN if i == 1 else MIST)
        kicker(s, x, 152, lab, WOOD, 10.5)
        s.end()
        if i:
            s.line(x - 18, 56, x - 18, 156, BENCH, 1.2)
    kicker(s, 40, 210, "CODE BY LANGUAGE, ALL PROJECTS", STONE, 10.5)
    items, total = lang_bar(s, 40, 226, W - 80, 16, agg_langs(CODE_REPOS), delay=0.5)
    legend(s, 40, 280, items, total, 3, (W - 80) / 3, size=13, kb=True, delay=0.9)
    card_end(s, H)
    s.save(OUT, "box-office.svg")


# ------------------------------------------------------------------ chapters: the timeline
LABELS = {"Mouros": "Mouros, my first Python practice", "AetherCloud": "AetherCloud",
          "VantaVault": "VantaVault", "KworkingSystem": "Campus Coworking",
          "Java": "Java practice repo", "Python": "Python practice repo", "StorageSystem": "groupbase",
          "mitaro-cs": "This profile"}


def chapters():
    H = 330
    s = Svg(W, H, "Chapters: a timeline of my GitHub projects")
    card(s, H, glow=(0.5, 1.0))
    ev = {}
    y, m = DATA["created"].split("-")[:2]
    ev[f"{y}-{m}"] = ["Joined GitHub"]
    for r in sorted(DATA["repos"], key=lambda r: r["created"]):
        ev.setdefault(r["created"][:7], []).append(LABELS.get(r["name"], r["name"]))
    keys = sorted(ev)
    n = len(keys)
    x0, x1, ly = 100, W - 100, 168
    s.add(f'<line class="draw" style="--len:{W - 80}px" x1="40" y1="{ly}" x2="{W - 40}" y2="{ly}" '
          f'stroke="{WOOD}" stroke-width="1.5"/>')
    for i, k in enumerate(keys):
        x = x0 + (x1 - x0) * i / max(1, n - 1)
        up = i % 2 == 0
        yy, mm = k.split("-")
        accent = SKIN if i == n - 1 else (SHIRT if up else STONE)
        s.g("rise", f"animation-delay:{0.2 + i * 0.16:.2f}s")
        s.add(f'<circle cx="{x:.1f}" cy="{ly}" r="7" fill="{NIGHT}" stroke="{accent}" stroke-width="2"/>')
        s.add(f'<circle cx="{x:.1f}" cy="{ly}" r="2.5" fill="{accent}"/>')
        s.line(x, ly + (-14 if up else 14), x, ly + (-34 if up else 34), BENCH, 1.5)
        lines = []
        for item in ev[k]:
            lines += wrap(item, "mono", 500, 13, 170)
        lines = lines[:4]
        if up:
            y0 = ly - 50 - (len(lines) - 1) * 18
            date_y = y0 - 30
        else:
            date_y, y0 = ly + 66, ly + 88
        s.text(x, date_y, f"{MONTHS[int(mm) - 1].capitalize()} {yy}", "serif", 26, accent, anchor="middle")
        for j, ln in enumerate(lines):
            s.text(x, y0 + j * 18, ln, "mono", 13, STONE, 500, anchor="middle")
        s.end()
    card_end(s, H)
    s.save(OUT, "chapters.svg")


# ------------------------------------------------------------------ end credits with the colour grade
def credits():
    H = 330
    s = Svg(W, H, "The end. Credits and the ten colours this profile is graded with, all taken from the avatar.")
    s.defs.append(f'<clipPath id="ec"><rect width="{W}" height="{H}" rx="16"/></clipPath>')
    s.add('<g clip-path="url(#ec)">')
    s.rect(0, 0, W, H, NIGHT)
    s.rect(0, 0, W, H, s.gradient([(0, SKIN, 0.10), (1, SKIN, 0)], 0.5, 0, 0.6, kind="radial"))
    s.g("fade")
    s.text(W / 2, 92, "The End", "italic", 76, MIST, anchor="middle")
    s.end()
    for i, line in enumerate(["WRITTEN, DIRECTED AND COMMITTED BY MITARO",
                              "GENERATED BY A PYTHON SCRIPT IN /SCRIPTS, RE-SHOT EVERY SIX HOURS"]):
        s.g("rise", f"animation-delay:{0.4 + i * 0.15:.2f}s")
        kicker(s, W / 2, 132 + i * 22, line, STONE if i == 0 else WOOD, 11, anchor="middle")
        s.end()
    kicker(s, 34, 206, "COLOUR GRADE", SKIN, 10.5)
    kicker(s, W - 34, 206, "K-MEANS ON THE AVATAR'S PIXELS", WOOD, 10.5, anchor="end")
    sw = (W - 68) / len(PALETTE)
    for i, (name, hexc) in enumerate(PALETTE):
        x = 34 + i * sw
        s.g("rise", f"animation-delay:{0.7 + i * 0.06:.2f}s")
        s.rect(x, 220, sw - 6, 56, hexc, BENCH, 1, 6)
        s.text(x, 296, name, "mono", 10.5, STONE, 700, ls=1.5)
        s.text(x, 312, hexc, "mono", 10.5, WOOD, 500)
        s.end()
    s.grain(0.08)
    s.add("</g>")
    s.rect(1, 1, W - 2, H - 2, "none", BENCH, 1.5, 16)
    s.save(OUT, "credits.svg")


if __name__ == "__main__":
    hero()
    slate()
    for sc in SCENES:
        scene_head(*sc)
    ticket("btn-telegram.svg", "telegram", "Telegram", "@treadways", SHIRT)
    ticket("btn-email.svg", "gmail", "Email", "miri.saro@bk.ru", STONE)
    ticket("btn-instagram.svg", "instagram", "Instagram", "@stere.os", SKIN)
    notes()
    for i, repo in enumerate(SHOWCASE, 1):
        feature(next(p for p in PROJECTS if p["repo"] == repo), i)
    stack()
    reel()
    box_office()
    chapters()
    credits()
