#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Concept: an editorial profile in the colours of the avatar where every page has its own character and the real
data is always the object. The cover is a poster with the Earth turning in ASCII characters (Natural Earth
coastlines in land.txt) and Moscow marked; Campus is a dark terminal page with a live diagram of how it syncs
and its git log typing itself out; About is neofetch for a person; Map is a night sky where the repositories
are a constellation; Toolkit fills ASCII bars; Now types out what I am working on.
All motion is CSS and stops under prefers-reduced-motion; every element rests in its final state.
Every page sits on black in both GitHub themes and has a single-column version for phones.
"""
import datetime as dt
import json
import math
import os
import random
import sys

from lib import MONO, MONO_EM, Svg, mono_width, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
W, X0, X1 = 888, 40, 848
MOBILE = False
# every page is built twice more for phones: a single column, 440 wide, picked by <picture> under 600px
LAYOUTS = {"": (888, 40, 848, False), "-mobile": (440, 20, 420, True)}

NIGHT_HOURS = (22, 23, 0, 1, 2, 3)
# black is the base in both GitHub themes, so the page looks the same for everyone; the accents are the avatar's
# colours (a pale blue shirt, sunlit skin, khaki trousers, suede boots, the trees and the bark behind), each
# with 4.5:1 contrast or more on black
DARK = dict(bg="#000000", ink="#f2f2f2", grey="#bdb5ae", rule="#262626", panel="#121212",
            accent="#a9c4d4", second="#e8a882", khaki="#d6c6a6", suede="#c9976f", leaf="#9fbb88", bark="#ada294")
THEMES = {"light": DARK, "dark": DARK}
PALETTE = ["leaf", "bark", "suede", "second", "khaki", "accent"]   # the avatar, trees to shirt
LANG_TOKEN = {"Java": "accent", "Svelte": "suede", "Python": "khaki", "TypeScript": "leaf", "JavaScript": "bark",
              "CSS": "second", "HTML": "grey", "Other": "grey"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MSK = dt.timezone(dt.timedelta(hours=3))
CORE_NAMES = ("campus", "storagesystem")   # Campus was called StorageSystem before the rename
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]
REPO_NAMES = {"campus": "Campus", "storagesystem": "Campus", "kworkingsystem": "Kworking"}


# ------------------------------------------------------------------ data
def core_repo():
    return next(r for r in DATA["repos"] if r["name"].lower() in CORE_NAMES)


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


def code_size():
    kb = sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k != "Rich Text Format") // 1000
    return f"{kb / 1000:.1f} MB" if kb >= 1000 else f"{kb} KB"


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
    return dict(per_day=per_day, hours=hours, by_wd=by_wd, streak=best, last=times[-1] if times else None,
                night=round(100 * sum(hours[h] for h in NIGHT_HOURS) / max(1, len(times))),
                peak=max(range(24), key=lambda h: hours[h]), weekday=WEEKDAYS[max(range(7), key=lambda d: by_wd[d])])


def wrap(txt, size, maxw, weight=400):
    lines, cur = [], ""
    for wd in txt.split():
        t = (cur + " " + wd).strip()
        if text_width(size, t, weight) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    return lines + [cur]


def esc(txt):
    return txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------------ type, rules and motion
def page(t, h, title, desc=""):
    s = Svg(W, h, title, desc)
    s.rect(0, 0, W, h, t["bg"])
    return s


def caps(s, x, y, txt, fill, anchor="start", size=12.5, weight=600):
    s.text(x, y, txt.upper(), size, fill, weight, anchor, ls=1.5)


def head(s, t, num, label, right=""):
    """Section line: number in the accent, label in caps, a hairline that draws itself, a note on the right."""
    right = "" if MOBILE else right
    caps(s, X0, 42, num, t["accent"], size=13.5, weight=700)
    caps(s, X0 + 34, 42, label, t["ink"], size=13.5, weight=700)
    start = X0 + 34 + text_width(13.5, label.upper(), 700, 1.5) + 14
    end = X1 - (text_width(12.5, right.upper(), 600, 1.5) + 14 if right else 0)
    s.g("wide", "--t:.1s")
    s.line(start, 37, end, 37, t["rule"], 1.2)
    s.end()
    if right:
        caps(s, X1, 42, right, t["grey"], "end")


def headline(s, x, baseline, txt, size, fill, ls, delay=0.0, glint=None):
    """A big word that lifts out of the line it stands on; with glint, a band of colour sweeps across it."""
    cid = s.uid("hl")
    s.defs.append(f'<clipPath id="{cid}"><rect x="0" y="{baseline - size}" width="{W}" height="{size * 1.12:.0f}"/>'
                  "</clipPath>")
    s.add(f'<g clip-path="url(#{cid})">')
    s.g("lift", f"--dy:{size:.0f}px;--t:{delay}s")
    s.text(x, baseline, txt, size, fill, 700, ls=ls)
    if glint:
        mid, gid = s.uid("gm"), s.uid("gg")
        band = size * 1.4
        s.defs.append(f'<linearGradient id="{gid}"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                      f'<stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
                      f"</linearGradient>"
                      f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{baseline + size}">'
                      f'<rect x="{W + 40}" y="{baseline - size}" width="{band:.0f}" height="{size * 1.2:.0f}" '
                      f'fill="url(#{gid})" transform="skewX(-18)" class="shine" '
                      f'style="--from:-{W + band + 80:.0f}px;--to:0px;--t:{delay + 1.6:.1f}s"/></mask>')
        s.add(f'<g mask="url(#{mid})">')
        s.text(x, baseline, txt, size, glint, 700, ls=ls)
        s.add("</g>")
    s.end()
    s.add("</g>")


def odometer(s, x, y, value, size, fill, delay=0.0):
    """Digits roll up into place like a split-flap board; other characters fade in."""
    lh = size * 1.15
    dw = size * 0.62
    for i, ch in enumerate(str(value)):
        if ch.isdigit():
            d = int(ch)
            cid = s.uid("od")
            s.defs.append(f'<clipPath id="{cid}"><rect x="{x - 2:.1f}" y="{y - size * 0.92:.1f}" width="{dw + 4:.1f}" '
                          f'height="{size * 1.12:.1f}"/></clipPath>')
            s.add(f'<g clip-path="url(#{cid})"><g transform="translate(0 {-d * lh:.1f})">')
            s.g("roll", f"--from:{d * lh:.1f}px;--t:{delay + i * 0.12:.2f}s")
            for k in range(10):
                s.text(x, y + k * lh, str(k), size, fill, 700)
            s.end()
            s.add("</g></g>")
            x += dw
        else:
            s.g("fade", f"--t:{delay + 0.9:.2f}s")
            s.text(x, y, ch, size, fill, 700)
            s.end()
            x += text_width(size, ch, 700)


def figures(s, t, y, items, accent_last=False, delay=0.2, cols=None):
    """Big numbers with labels in a grid split by hairlines; numbers roll in. One row unless cols is set."""
    cols = cols or len(items)
    cw = (X1 - X0) / cols
    for i, (v, lab) in enumerate(items):
        col, row = i % cols, i // cols
        x, yy = X0 + col * cw + (16 if col else 0), y + row * 86
        fill = t["accent"] if accent_last and i == len(items) - 1 else t["ink"]
        if any(c.isdigit() for c in str(v)):
            odometer(s, x, yy, v, 38, fill, delay + i * 0.15)
        else:
            s.g("fade", f"--t:{delay + i * 0.15 + 0.6:.2f}s")
            s.text(x, yy, str(v), 38, fill, 700, ls=-0.8)
            s.end()
        s.text(x, yy + 25, lab, 14.5, t["grey"])
        if col:
            s.line(X0 + col * cw, yy - 36, X0 + col * cw, yy + 30, t["rule"], 1.2)


def para(s, x, y, txt, size, fill, maxw, lead=1.45, weight=400, delay=0.0):
    s.g("fade", f"--t:{delay}s")
    for ln in wrap(txt, size, maxw, weight):
        s.text(x, y, ln, size, fill, weight)
        y += size * lead
    s.end()
    return y


def mono_text(s, x, y, parts, size, delay=None, steps_per_s=36, mask=None):
    """One monospace line from (text, colour) parts. With a delay it types itself out, cursor-style."""
    txt = "".join(p for p, _ in parts)
    width = mono_width(size, txt)
    if delay is not None:
        cid = s.uid("ty")
        s.defs.append(f'<clipPath id="{cid}"><rect x="{x - 1:.1f}" y="{y - size:.1f}" width="{width + 12:.1f}" '
                      f'height="{size * 1.45:.1f}"/></clipPath>')
        s.add(f'<g clip-path="url(#{cid})">')
    spans = "".join(f'<tspan fill="{c}">{esc(p)}</tspan>' for p, c in parts)
    s.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-family="{MONO}" xml:space="preserve" '
          f'style="white-space:pre">{spans}</text>')
    if delay is not None:
        dur = max(0.2, len(txt) / steps_per_s)
        s.rect(x + width + 2, y - size, width + 12, size * 1.45, mask or BG_HOLDER[0],
               extra=f'class="type" style="--dx:-{width + 2:.1f}px;--t:{delay:.2f}s;--d:{dur:.2f}s;'
                     f'animation-timing-function:steps({len(txt)})"')
        s.add("</g>")
        return delay + dur
    return 0


BG_HOLDER = ["#000"]   # the page colour the typing mask paints with, set per theme


def both(fn, name):
    global W, X0, X1, MOBILE
    for suffix, (w, x0, x1, mobile) in LAYOUTS.items():
        W, X0, X1, MOBILE = w, x0, x1, mobile
        for theme, t in THEMES.items():
            BG_HOLDER[0] = t["bg"]
            fn(t).save(OUT, f"{name}-{theme}{suffix}.svg")


# ------------------------------------------------------------------ cover: a poster with an ASCII Earth
def fade_edge(s, t):
    gid = s.uid("fd")
    s.defs.append(f'<linearGradient id="{gid}"><stop offset="0" stop-color="{t["bg"]}" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="{t["bg"]}"/></linearGradient>')
    return f"url(#{gid})"


def ticker(s, t, y):
    """A band with my latest real commits running right to left."""
    rows = [c for c in DATA["commits"] if not c["msg"].startswith(("Initial commit", "Merge "))][:8]
    items = []
    for c in rows:
        _, m, d = c["ts"][:10].split("-")
        items.append(f"{c['msg']}  —  {REPO_NAMES.get(c['repo'].lower(), c['repo'])}, {int(d)} {MONTHS[int(m) - 1]}")
    line = "     ·     ".join(items) + "     ·     "
    width = text_width(14, line)
    lx = X0 + 86
    caps(s, X0, y, "Latest", t["suede"], weight=700)
    cid = s.uid("tk")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{lx}" y="{y - 18}" width="{X1 - lx}" height="26"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.g("ticker", f"--shift:-{width:.0f}px;--d:{width / 45:.0f}s")
    for k in range(2):
        s.add(f'<text x="{lx + k * width:.1f}" y="{y}" font-size="14" fill="{t["ink"]}" xml:space="preserve">'
              f'{esc(line)}</text>')
    s.end()
    s.add("</g>")
    s.rect(X1 - 40, y - 18, 40, 26, fade_edge(s, t))


LAND = [ln.rstrip("\n") for ln in open(os.path.join(HERE, "land.txt"), encoding="utf-8")]   # 2° cells, Natural Earth
RAMP = ".:-=+*#%@"
MOSCOW = (55.75, 37.62)


def displacement_png(n, rad):
    """The map that wraps a flat strip onto a sphere for feDisplacementMap: red moves pixels sideways, green up
    and down, 128 means stay. Each disc pixel looks up the longitude and latitude it shows."""
    import base64
    import io
    import zlib
    raw = bytearray()
    for j in range(n):
        raw.append(0)
        for i in range(n):
            nx, ny = (i + 0.5) / n * 2 - 1, 1 - (j + 0.5) / n * 2
            d = nx * nx + ny * ny
            if d >= 1:
                raw += bytes((128, 128, 0))
                continue
            lat = math.asin(ny)
            lon = math.asin(max(-1.0, min(1.0, nx / max(1e-6, math.cos(lat)))))
            dx, dy = lon / (math.pi / 2) - nx, -(lat / (math.pi / 2) - ny)   # in radii, both within -1..1
            raw += bytes((round(127.5 + dx * 127.5), round(127.5 + dy * 127.5), 0))
    def chunk(kind, data):
        return (len(data).to_bytes(4, "big") + kind + data
                + (zlib.crc32(kind + data) & 0xffffffff).to_bytes(4, "big"))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", n.to_bytes(4, "big") * 2 + bytes((8, 2, 0, 0, 0)))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    del io
    return "data:image/png;base64," + base64.b64encode(png).decode()


def land_char(lat, lon):
    """Inland reads denser than the coast: the share of land around the cell picks the glyph."""
    r0, c0 = int((90 - lat) / 2), int((lon + 180) / 2)
    cells = [LAND[min(89, max(0, r0 + dr))][(c0 + dc) % 180] for dr in (-1, 0, 1) for dc in (-2, -1, 0, 1, 2)]
    share = cells.count("#") / len(cells)
    if LAND[min(89, r0)][c0 % 180] != "#" and share < 0.5:
        return " "
    return RAMP[min(len(RAMP) - 1, 2 + int(share * (len(RAMP) - 2)))]


def globe(s, t, cx, top, size, period=24.0):
    """The Earth in ASCII, turning without a single jump: a flat strip of real coastlines slides sideways
    and a displacement filter wraps it onto the sphere, so the land squeezes at the limb as it should.
    Meridians and parallels ride on the strip, Moscow is marked on it, and a satellite circles the
    globe, passing behind it. Returns the bottom edge."""
    cw = size * MONO_EM
    cols = 76                                   # columns around the whole Earth
    rad = cols * cw / 4                         # 90 degrees of longitude is one radius
    rows = round(2 * rad / (size * 1.04))
    lh = 2 * rad / rows
    cy = top + rad
    ocean, land, shade, fid, clip = s.uid("oc"), s.uid("ld"), s.uid("sh"), s.uid("gf"), s.uid("gc")
    s.defs.append(
        f'<radialGradient id="{ocean}" cx=".38" cy=".34" r=".75"><stop offset="0" stop-color="{t["accent"]}" '
        f'stop-opacity=".30"/><stop offset="1" stop-color="{t["accent"]}" stop-opacity=".05"/></radialGradient>'
        f'<linearGradient id="{land}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["khaki"]}"/>'
        f'<stop offset=".5" stop-color="{t["leaf"]}"/><stop offset="1" stop-color="{t["suede"]}"/></linearGradient>'
        f'<radialGradient id="{shade}" cx=".36" cy=".32" r=".8"><stop offset=".35" stop-color="{t["bg"]}" '
        f'stop-opacity="0"/><stop offset="1" stop-color="{t["bg"]}" stop-opacity=".8"/></radialGradient>'
        f'<clipPath id="{clip}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}"/></clipPath>'
        f'<filter id="{fid}" filterUnits="userSpaceOnUse" primitiveUnits="userSpaceOnUse" '
        f'x="{cx - rad:.1f}" y="{top:.1f}" width="{2 * rad:.1f}" height="{2 * rad:.1f}" '
        f'color-interpolation-filters="sRGB"><feImage href="{displacement_png(112, rad)}" x="{cx - rad:.1f}" '
        f'y="{top:.1f}" width="{2 * rad:.1f}" height="{2 * rad:.1f}" preserveAspectRatio="none" result="map"/>'
        f'<feDisplacementMap in="SourceGraphic" in2="map" scale="{2 * rad:.1f}" xChannelSelector="R" '
        f'yChannelSelector="G"/></filter>')

    # the satellite's orbit: the far half is drawn before the globe, the near half after it
    orx, ory, tilt = rad * 1.32, rad * 0.30, -16
    orbit = f"M{cx - orx:.1f} {cy:.1f}A{orx:.1f} {ory:.1f} 0 1 1 {cx + orx:.1f} {cy:.1f}A{orx:.1f} {ory:.1f} 0 1 1 {cx - orx:.1f} {cy:.1f}"
    turn = f"rotate({tilt} {cx:.1f} {cy:.1f})"
    s.add(f'<g transform="{turn}">')
    s.path(f"M{cx - orx:.1f} {cy:.1f}A{orx:.1f} {ory:.1f} 0 0 1 {cx + orx:.1f} {cy:.1f}", "none", t["grey"], 1,
           0.35, extra='stroke-dasharray="2 5"')
    s.add("</g>")

    s.g("grow", f"transform-origin:{cx:.0f}px {cy:.0f}px;--t:.3s;animation-duration:1.6s")
    s.circle(cx, cy, rad, t["bg"])           # hides the far half of the orbit
    s.circle(cx, cy, rad, f"url(#{ocean})")
    # the strip: two copies of a 360-degree map side by side, sliding east by one copy per period
    strip = []
    for r in range(rows):
        lat = 90 - (r + 0.5) * 180 / rows
        strip.append("".join(land_char(lat, -180 + (c + 0.5) * 360 / cols) for c in range(cols)))
    s.add(f'<g clip-path="url(#{clip})"><g filter="url(#{fid})">')
    s.add(f'<g class="spin" style="--w:{4 * rad:.1f}px;animation:spin-strip {period}s linear infinite">')
    for copy in (0, -1):
        x0 = cx - 2 * rad + copy * 4 * rad
        for lon in range(-180, 180, 30):
            x = cx + (lon / 90 + copy * 4) * rad
            s.line(x, top, x, top + 2 * rad, t["accent"], 0.9, 0.45)
        for lat in (-60, -30, 0, 30, 60):
            y = cy - lat / 90 * rad
            s.line(x0, y, x0 + 4 * rad, y, t["accent"], 0.9, 0.6 if lat == 0 else 0.4)
        spans = "".join(f'<tspan x="{x0:.1f}" y="{top + (r + 0.5) * lh + size * 0.35:.1f}">{esc(ln)}</tspan>'
                        for r, ln in enumerate(strip) if ln.strip())
        s.add(f'<text font-family="{MONO}" font-size="{size}" font-weight="700" fill="url(#{land})" '
              f'xml:space="preserve" style="white-space:pre">{spans}</text>')
        mx = cx + (MOSCOW[1] / 90 + copy * 4) * rad
        my = cy - MOSCOW[0] / 90 * rad
        s.circle(mx, my, 7, t["second"], 0.35)
        s.circle(mx, my, 3.6, t["second"])
    s.add("</g></g></g>")
    s.css["spin-strip"] = ("@keyframes spin-strip{from{transform:translateX(0)}to{transform:translateX(var(--w))}}"
                           "@media (prefers-reduced-motion:reduce){.spin{animation:none!important}}")
    # night falls on the far side; the rim catches the light
    s.circle(cx, cy, rad, f"url(#{shade})")
    s.circle(cx, cy, rad, "none", extra=f'stroke="{t["accent"]}" stroke-opacity=".5" stroke-width="1.2"')
    s.end()

    s.add(f'<g transform="{turn}">')
    s.path(f"M{cx + orx:.1f} {cy:.1f}A{orx:.1f} {ory:.1f} 0 0 1 {cx - orx:.1f} {cy:.1f}", "none", t["grey"], 1,
           0.55, extra='stroke-dasharray="2 5"')
    # the satellite rides the whole ellipse; it fades out while it is behind the globe
    s.add(f'<g class="sat" style="offset-path:path(\'{orbit}\');offset-rotate:0deg;'
          f'animation:sat 9s linear infinite">')
    s.circle(0, 0, 3.4, t["khaki"])
    s.circle(0, 0, 7, t["khaki"], 0.25)
    s.add("</g></g>")
    s.css["sat"] = ("@keyframes sat{0%{offset-distance:0%;opacity:0}2%,48%{opacity:0}52%{opacity:1}"
                    "96%{opacity:1}100%{offset-distance:100%;opacity:0}}"
                    ".sat{opacity:0}@media (prefers-reduced-motion:reduce){.sat{display:none}}")
    return cy + rad


def cover(t):
    f = facts()
    repos = DATA["repos"]
    last = f["last"]
    deck = "I build local-first software: the data stays on a machine you control, not on someone else's server."
    if MOBILE:
        head_y, head_size, name_y, para_y, para_w = 150, 100, 202, 236, X1 - X0
        para_end = para_y + 18.5 * 1.45 * len(wrap(deck, 18.5, para_w))
        globe_cx, globe_top, globe_size = W / 2, para_end + 30, 11
        y_rule = globe_top + 76 * globe_size * MONO_EM / 2 + 78
    else:
        head_y, head_size, name_y, para_y, para_w = 184, 124, 240, 274, 420
        globe_cx, globe_top, globe_size, y_rule = 680, 74, 11, 372
    fig_y = y_rule + 56
    fig_end = fig_y + (86 if MOBILE else 0) + 54
    H = fig_end + (52 if MOBILE else 80)
    s = page(t, H, "Mitaro. Omar, computer science student at MTUCI. I build local-first software: the data stays "
             "on a machine you control. Core project: Campus.",
             "A poster: the Earth in ASCII characters turning, with Moscow marked, the key figures and a ticker of my latest "
             "commits.")
    caps(s, X0, 42, "mitaro-cs" if MOBILE else "mitaro-cs · GitHub profile", t["grey"])
    if last:
        note = f"last commit {last.day} {MONTHS[last.month - 1]} {last.year}"
        caps(s, X1, 42, note, t["grey"], "end")
        dx = X1 - text_width(12.5, note.upper(), 600, 1.5) - 12
        s.circle(dx, 37.5, 7, t["leaf"], extra='class="ping" opacity="0"')
        s.circle(dx, 37.5, 3.5, t["leaf"])
    seg = (X1 - X0) / len(PALETTE)
    for i, tok in enumerate(PALETTE):
        s.g("wide", f"--t:{i * 0.07:.2f}s")
        s.rect(X0 + i * seg, 53, seg, 4, t[tok])
        s.end()
    band, cl = s.uid("bd"), s.uid("bc")
    s.defs.append(f'<linearGradient id="{band}"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" '
                  f'stop-opacity="0"/></linearGradient><clipPath id="{cl}"><rect x="{X0}" y="53" width="{X1 - X0}" '
                  f'height="4"/></clipPath>')
    s.add(f'<g clip-path="url(#{cl})">')
    s.rect(X0 - 120, 53, 120, 4, f"url(#{band})", extra=f'class="glide" style="--w:{X1 - X0 + 120}px"')
    s.add("</g>")
    headline(s, X0 - 5, head_y, "Mitaro", head_size, t["ink"], -4, 0.15, glint=t["accent"])
    s.g("fade", "--t:.6s")
    s.text(X0, name_y, "Omar, CS student at MTUCI.", 21, t["ink"], 700)
    s.end()
    para(s, X0, para_y, deck, 18.5, t["grey"], para_w, 1.45, delay=0.75)
    bottom = globe(s, t, globe_cx, globe_top, globe_size)
    lat, lon = MOSCOW
    mono_text(s, globe_cx - mono_width(12, f"{lat}°N {lon}°E · Moscow · UTC+3") / 2, bottom + 30,
              [(f"{lat}°N {lon}°E", t["grey"]), (" · ", t["rule"]), ("Moscow", t["second"]), (" · UTC+3", t["grey"])],
              12, delay=1.4)
    s.line(X0, y_rule, X1, y_rule, t["rule"], 1.2)
    figures(s, t, fig_y, [(sum(r["commits"] for r in repos), "commits"), (len(repos), "public repositories"),
                          (code_size(), "of code"), ("Campus", "core project")], accent_last=True, delay=0.5,
            cols=2 if MOBILE else None)
    s.line(X0, fig_end, X1, fig_end, t["ink"], 1.5)
    if MOBILE:
        ticker(s, t, fig_end + 32)
        return s
    caps(s, X0, fig_end + 26, "Contents", t["grey"])
    x = X0 + 112
    for num, name in SECTIONS:
        caps(s, x, fig_end + 26, num, t["accent"], weight=700)
        caps(s, x + 26, fig_end + 26, name, t["ink"], weight=700)
        x += 26 + text_width(12.5, name.upper(), 700, 1.5) + 24
    s.line(X0, fig_end + 40, X1, fig_end + 40, t["rule"], 1.2)
    ticker(s, t, fig_end + 66)
    return s


SECTIONS = [("01", "Campus"), ("02", "About"), ("03", "Map"), ("04", "Toolkit"), ("05", "Now")]


# ------------------------------------------------------------------ 01 Campus: a dark terminal page
SPINNER = "|/-\\"
CAMPUS_TEXT = ("A site and an app for one study group: homework, a schedule from an .ics file, news and files. It "
               "lives on the group leader's own computer, and every phone keeps a copy that syncs when the host is "
               "back on.")


def cubic_len(p0, p1, p2, p3, n=24):
    pts = [tuple((1 - u) ** 3 * a + 3 * (1 - u) ** 2 * u * b + 3 * (1 - u) * u * u * c + u ** 3 * d
                 for a, b, c, d in zip(p0, p1, p2, p3)) for u in (k / n for k in range(n + 1))]
    return sum(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(n))


def route(start, mid, end, vertical):
    """A lane from start straight to mid (through the tunnel), then an S-curve to end. Returns the path there,
    the path back and the length."""
    bend = (end[1] - mid[1] if vertical else end[0] - mid[0]) / 2
    if vertical:
        c1, c2 = (mid[0], mid[1] + bend), (end[0], end[1] - bend)
        there = f"M{start[0]:.1f} {start[1]:.1f}V{mid[1]:.1f}"
        back_tail = f"V{start[1]:.1f}"
    else:
        c1, c2 = (mid[0] + bend, mid[1]), (end[0] - bend, end[1])
        there = f"M{start[0]:.1f} {start[1]:.1f}H{mid[0]:.1f}"
        back_tail = f"H{start[0]:.1f}"
    there += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {end[0]:.1f} {end[1]:.1f}"
    back = (f"M{end[0]:.1f} {end[1]:.1f}C{c2[0]:.1f} {c2[1]:.1f} {c1[0]:.1f} {c1[1]:.1f} {mid[0]:.1f} {mid[1]:.1f}"
            + back_tail)
    return there, back, math.dist(start, mid) + cubic_len(mid, c1, c2, end)


def cycle(s, name, spans, period, on=1.0, off=0.0):
    """Keyframes that hold `on` inside the spans (in % of the period) and `off` outside, with soft edges."""
    keys, edge = [], 0.8
    for a, b in spans:
        # the fades sit inside the span, so neighbouring spans hand over without overlapping
        a_in, b_out = (a, a + edge) if a else (0, 0), (b - edge, b) if b < 100 else (100, 100)
        keys.append(f"{a_in[0]:.1f}%{{opacity:{off if a else on}}}{a_in[1]:.1f}%,{b_out[0]:.1f}%{{opacity:{on}}}"
                    f"{b_out[1]:.1f}%{{opacity:{off if b < 100 else on}}}")
    first = "" if spans[0][0] == 0 else f"0%{{opacity:{off}}}"
    last = "" if spans[-1][1] == 100 else f"100%{{opacity:{off}}}"
    s.css[name] = f"@keyframes {name}{{{first}{''.join(keys)}{last}}}"
    return f"animation:{name} {period}s linear infinite"


def sync_diagram(s, t, top):
    """How Campus syncs: the host computer, an HTTPS tunnel with two lanes (changes out, edits back) and the
    devices. One phone drops offline every cycle, queues its edits, comes back and sends them in a burst."""
    period = 12
    tones = dict(down=t["accent"], up=t["khaki"])
    caps(s, X0, top, "How it syncs", t["grey"])
    statuses = (["synced", "1 queued", "2 queued", "3 queued", "sending 3"] if MOBILE else
                ["synced", "offline · 1 queued", "offline · 2 queued", "offline · 3 queued", "back · sending 3"])
    names = ([("phone", "offline copy"), ("phone", None), ("laptop", "browser")] if MOBILE else
             [("phone", "offline copy"), ("phone", None), ("laptop", "browser · live")])
    host_lines = ["Spring Boot · SQLite", "files in AES-256-GCM"] + (["a spare takes over in 1 min"] if MOBILE else [])
    spare_lines = ["full copy every 5 s", "takes over in 1 min"]
    mono = 11 if MOBILE else 12.5

    def fit(title, lines):
        """A card wide enough for its words: padding, dot, the longer of the title and the lines."""
        return 46 + max([text_width(15, title, 700)] + [mono_width(mono, ln) for ln in lines])

    gap = 4.5   # between lanes; six of them share the pipe, in the order of the devices
    if MOBILE:
        host = (X0, top + 20, X1 - X0, 100)
        spare = None
        pipe = (W / 2 - 17, top + 136, 34, 70)
        cw = (X1 - X0 - 28) / 3
        devices = [(X0 + i * (cw + 14), top + 270, cw, 62) for i in range(3)]
        bottom = top + 270 + 62
    else:
        hw = fit("spare computer", host_lines + spare_lines)
        host = (X0, top + 22, hw, 78)
        spare = (X0, top + 136, hw, 78)
        dw = max(fit("phone", statuses + [ln for _, ln in names if ln]), 190)
        devices = [(X1 - dw, top + 22 + i * 66, dw, 56) for i in range(3)]
        mid_y = top + 22 + 66 + 28
        pipe = (X0 + hw + 40, mid_y - 17, (X1 - dw - 110) - (X0 + hw + 40), 34)
        host = (X0, mid_y - 39, hw, 78)
        spare = (X0, mid_y + 62, hw, 78)
        bottom = mid_y + 140

    def card(box, title, lines, dot=None):
        x, y, w, h = box
        s.rect(x, y, w, h, t["panel"], t["rule"], 1.2, rx=8)
        s.text(x + 30, y + 24, title, 15 if not MOBILE else 14, t["ink"], 700)
        for k, ln in enumerate(lines):
            s.add(f'<text x="{x + 30:.1f}" y="{y + 44 + k * 19:.1f}" font-size="{11 if MOBILE else 12.5}" '
                  f'font-family="{MONO}" fill="{t["grey"]}">{esc(ln)}</text>')
        if dot:
            s.circle(x + 16, y + 19.5, 4, dot)

    # the tunnel: a pipe with two lanes; the labels sit beside it
    px, py, pw, ph = pipe
    vertical = MOBILE
    s.rect(px, py, pw, ph, t["panel"], t["rule"], 1.2, rx=ph / 2 if not vertical else pw / 2)
    if vertical:
        caps(s, px + pw + 14, py + ph / 2 - 4, "HTTPS tunnel", t["ink"], size=11.5, weight=700)
        s.add(f'<text x="{px + pw + 14:.1f}" y="{py + ph / 2 + 14:.1f}" font-size="11" font-family="{MONO}" '
              f'fill="{t["grey"]}">CloudPub · SSE</text>')
    else:
        caps(s, px + pw / 2, py - 12, "HTTPS tunnel", t["ink"], "middle", size=11.5, weight=700)
        s.add(f'<text x="{px + pw / 2:.1f}" y="{py + ph + 22:.1f}" font-size="12" font-family="{MONO}" '
              f'fill="{t["grey"]}" text-anchor="middle">CloudPub · live updates over SSE</text>')

    # lanes: changes go out on one side of the pipe, edits come back on the other
    hx, hy, hw, hh = host
    lanes = []
    for i, (dx, dy, dw, dh) in enumerate(devices):
        for j, lane in enumerate(("down", "up")):
            off = (i * 2 + j - 2.5) * gap          # lane order matches device order, so no two lanes cross
            end_off = (j - 0.5) * 12
            if vertical:
                start, mid, end = (W / 2 + off, hy + hh), (W / 2 + off, py + ph), (dx + dw / 2 + end_off, dy)
            else:
                start, mid, end = (hx + hw, py + ph / 2 + off), (px + pw, py + ph / 2 + off), (dx, dy + dh / 2 + end_off)
            there, back, length = route(start, mid, end, vertical)
            lanes.append((i, lane, there if lane == "down" else back, length))
    off_link = cycle(s, "offlink", [(36, 76)], period, on=0.2, off=1)
    off_pk = cycle(s, "offpk", [(36, 76)], period, on=0, off=1)
    for i, lane, d, length in lanes:
        style = f' class="cyc" style="{off_link}"' if i == 1 else ""
        s.add(f"<g{style}>")
        s.path(d, "none", t["rule"], 1.4)
        s.add("</g>")
    for i, lane, d, length in lanes:
        style = f' class="cyc" style="{off_pk}"' if i == 1 else ""
        s.add(f"<g{style}>")
        lag = i * 0.7 + (1.3 if lane == "up" else 0)
        s.path(d, "none", tones[lane], 3, extra=f'class="packet" stroke-dasharray="10 {length + 30:.0f}" '
                                                f'style="--start:10;--end:-{length:.0f};--t:{lag:.2f}s;'
                                                f'animation-duration:{2.4 + i * 0.3:.1f}s"')
        s.add("</g>")
    # the burst: three queued edits leave the phone the moment it is back
    i, _, d, length = next(x for x in lanes if x[0] == 1 and x[1] == "up")
    s.css["burst"] = ("@keyframes burst{0%,76%{stroke-dashoffset:10;opacity:0}76.5%{opacity:1}"
                      "86%{stroke-dashoffset:var(--end);opacity:1}87%,100%{stroke-dashoffset:var(--end);opacity:0}}")
    for k in range(3):
        s.path(d, "none", tones["up"], 3, opacity=0,
               extra=f'class="cyc" stroke-dasharray="10 {length + 30:.0f}" style="--end:-{length:.0f};'
                     f'animation:burst {period}s cubic-bezier(.4,0,.6,1) infinite;animation-delay:{k * 0.3:.1f}s"')

    # the cards, over the lanes
    card(host, "host computer", host_lines, t["leaf"])
    s.circle(hx + 16, hy + 19.5, 9, t["leaf"], extra='class="pulse" opacity=".3"')
    if spare:
        sx, sy, sw, sh = spare
        card(spare, "spare computer", spare_lines, t["bark"])
        s.path(f"M{sx + 30} {hy + hh}V{sy}", "none", t["rule"], 1.4, extra='stroke-dasharray="3 4"')
        s.path(f"M{sx + 30} {hy + hh}V{sy}", "none", t["leaf"], 3,
               extra=f'class="packet" stroke-dasharray="6 {sy - hy - hh + 20:.0f}" '
                     f'style="--start:6;--end:-{sy - hy - hh:.0f};animation-duration:3.2s"')
    for i, box in enumerate(devices):
        title, line = names[i]
        if line:
            card(box, title, [line], t["leaf"])
            continue
        card(box, title, [], None)
        x, y = box[0], box[1]
        windows = [[(0, 36), (86, 100)], [(36, 52)], [(52, 64)], [(64, 76)], [(76, 86)]]
        for k, (txt, spans) in enumerate(zip(statuses, windows)):
            anim = cycle(s, f"st{k}", spans, period)
            s.add(f'<text x="{x + 30:.1f}" y="{y + 44:.1f}" font-size="{11 if MOBILE else 12.5}" font-family="{MONO}" '
                  f'fill="{t["second"] if 0 < k < 4 else t["grey"]}" class="cyc" '
                  f'style="opacity:{1 if k == 0 else 0};{anim}">{esc(txt)}</text>')
        s.circle(x + 16, y + 19.5, 4, t["leaf"], extra=f'class="cyc" style="{cycle(s, "dotok", [(0, 36), (76, 100)], period)}"')
        s.circle(x + 16, y + 19.5, 4, t["second"], extra=f'class="cyc" style="opacity:0;'
                                                         f'{cycle(s, "dotoff", [(36, 76)], period)}"')
    # what the colours mean
    ly = bottom + 30
    lx = X0
    for lane, label in (("down", "changes to devices"), ("up", "edits back to the host")):
        s.line(lx, ly - 4, lx + 22, ly - 4, tones[lane], 3)
        s.add(f'<text x="{lx + 30}" y="{ly:.1f}" font-size="12" font-family="{MONO}" fill="{t["grey"]}">{label}</text>')
        lx += 30 + mono_width(12, label) + 28
    return ly


def terminal_theme():
    """The Campus page is a dark terminal in both themes, so it reads as its own place."""
    return dict(THEMES["dark"], panel="#141414", rule="#2c2c2c")


def campus(_t):
    t = terminal_theme()
    BG_HOLDER[0] = t["bg"]
    r = core_repo()
    pin = DATA.get("pin") or {}
    items = [(pin.get(k), lab) for k, lab in (("java", "Java classes"), ("svelte", "UI components"),
                                              ("tests", "test files"), ("migrations", "migrations"),
                                              ("versions", "versions"))]
    items = [(v, lab) for v, lab in items if v] + [(r.get("release") or "—", "release")]
    log = [c for c in DATA["commits"] if c["repo"].lower() in CORE_NAMES and not c["msg"].startswith("Merge ")][:7]
    if MOBILE:
        text_end = 158 + 18 * 1.5 * len(wrap(CAMPUS_TEXT, 18, X1 - X0))
        diagram_top = text_end + 24
        log_x, log_y = X0, diagram_top + 424
        log_room = int((X1 - X0) / (12.5 * MONO_EM))
    else:
        diagram_top = 340
        log_x, log_y = 486, 100
        log_room = int((X1 - log_x) / (12.5 * MONO_EM))
    log_end = log_y + 26 + len(log) * 22
    rule = (log_end if MOBILE else diagram_top + 312) + 18
    fig_y = rule + 58
    fig_rows = (len(items) + 2) // 3 if MOBILE else 1
    end = fig_y + (fig_rows - 1) * 86 + 48
    H = end + (74 if MOBILE else 48)
    s = page(t, H, "01 Campus, my core project: a site and an app for one study group that lives on the group "
             "leader's own computer. " + ", ".join(f"{v} {lab}" for v, lab in items) + ".",
             "A dark terminal page: how Campus syncs, from the host computer through an HTTPS tunnel to phones that "
             "keep working offline, and git log --graph of the latest Campus commits typing itself out.")
    head(s, t, "01", "Core project", "github.com/mitaro-cs/Campus")
    if MOBILE:
        headline(s, X0 - 3, 120, "Campus", 72, t["ink"], -2, 0.1, glint=t["khaki"])
        para(s, X0, 158, CAMPUS_TEXT, 18, t["ink"], X1 - X0, 1.5, delay=0.4)
    else:
        headline(s, X0 - 3, 134, "Campus", 80, t["ink"], -2.5, 0.1, glint=t["khaki"])
        para(s, X0, 180, CAMPUS_TEXT, 18, t["ink"], 410, 1.5, delay=0.4)
        s.line(X0, diagram_top - 30, X1, diagram_top - 30, t["rule"], 1.2)
    sync_diagram(s, t, diagram_top)

    # git log --graph of the latest Campus commits, typed out line by line
    caps(s, log_x, log_y, "$ git log --graph --oneline", t["grey"])
    delay = 1.2
    for k, c in enumerate(log):
        _, m, d = c["ts"][:10].split("-")
        graph = "* "
        stamp = f"{int(d):>2} {MONTHS[int(m) - 1]}  "
        room = log_room - len(graph) - len(stamp)
        msg = c["msg"] if len(c["msg"]) <= room else c["msg"][:room - 1] + "…"
        delay = mono_text(s, log_x, log_y + 26 + k * 22,
                          [(graph, t["suede"]), (stamp, t["grey"]), (msg, t["ink"])],
                          12.5, delay, steps_per_s=90, mask=t["bg"]) + 0.08
    s.line(X0, rule, X1, rule, t["rule"], 1.2)
    figures(s, t, fig_y, items, accent_last=True, delay=0.3, cols=3 if MOBILE else None)
    s.line(X0, end, X1, end, t["rule"], 1.2)
    caps(s, X0, end + 26, f"{r['commits']} commits · AGPL-3.0", t["grey"])
    if MOBILE:
        caps(s, X0, end + 50, "Windows · macOS · iPhone · Android", t["grey"])
    else:
        caps(s, X1, end + 26, "Windows · macOS · iPhone · Android", t["grey"], "end")
    return s


# ------------------------------------------------------------------ 02 About: neofetch for a person
def logo_rows(rows=14, cols=26, word="mitaro", stem=5.5, thick=2.6, meet=9):
    """A big M filled with my name, the way neofetch draws a system's logo."""
    out, k = [], 0
    for r in range(rows):
        line = ""
        for c in range(cols):
            x = c + 0.5
            xl = stem - 1.5 + min(r, meet) / meet * (cols / 2 - stem + 1.5)   # the left diagonal, mirrored on the right
            if x < stem or x > cols - stem or (r <= meet + 1 and min(abs(x - xl), abs(x - (cols - xl))) < thick):
                line += word[k % len(word)]
                k += 1
            else:
                line += " "
        out.append(line)
    return out


def about_rows():
    f = facts()
    repos = DATA["repos"]
    since = dt.date.fromisoformat(DATA["created"][:10])
    years = (f["last"].date() - since).days // 365 if f["last"] else 0
    langs = [k for k, _ in all_langs() if k != "Other"][:3]
    release = core_repo().get("release")
    rows = [("Name", "Omar · Mitaro"),
            ("Study", "computer science, MTUCI"),
            ("Location", "Moscow, UTC+3"),
            ("Uptime", f"{years} years on GitHub, since {MONTHS[since.month - 1]} {since.year}"),
            ("Repos", f"{len(repos)} public · {sum(r.get('stars', 0) for r in repos)} stars"),
            ("Commits", f"{sum(r['commits'] for r in repos)} · {len(f['per_day'])} active days"),
            ("Night", f"{f['night']}% after 22:00 · peak {f['peak']:02d}:00"),
            ("Streak", f"{f['streak']} days · busiest on {f['weekday']}s"),
            ("Langs", " · ".join(langs)),
            ("Core", "Campus" + (f" {release}" if release else "")),
            ("Editor", "Zed")]
    return rows


def about(t):
    rows = about_rows()
    logo = logo_rows()
    if MOBILE:
        lsize, isize = 14, 13.5
        lx, ly = (W - mono_width(lsize, logo[0])) / 2, 134
        ix, iy = X0, ly + len(logo) * lsize * 1.2 + 26
    else:
        lsize, isize = 16, 15
        lx, ly = X0, 146
        ix, iy = X0 + 330, 128
    llh, ilh = lsize * 1.2, isize * 1.62
    H = iy + (len(rows) + 4.3) * ilh + 30
    s = page(t, H, "02 About: " + "; ".join(f"{a} {b}" for a, b in rows) + ".",
             "neofetch for a person: a big M made of my name, shimmering in the colours of the avatar, and the facts "
             "typed out next to it.")
    head(s, t, "02", "About", "$ neofetch --user mitaro")
    mono_text(s, X0, 92, [("$ ", t["second"]), ("neofetch", t["ink"])], isize, delay=0.2)
    # the logo: rows fade in from the top, then a band of light runs down them again and again
    s.add(f'<g font-family="{MONO}" font-size="{lsize}" font-weight="700">')
    for r, ln in enumerate(logo):
        tok = PALETTE[min(len(PALETTE) - 1, r * len(PALETTE) // len(logo))]
        s.g("fade", f"--t:{0.5 + r * 0.06:.2f}s")
        s.add(f'<text x="{lx:.1f}" y="{ly + r * llh:.1f}" fill="{t[tok]}" xml:space="preserve" style="white-space:pre;'
              f'animation:shimmer 4.2s ease-in-out infinite;animation-delay:{r * 0.12:.2f}s">{ln}</text>')
        s.end()
    s.add("</g>")
    s.css["shimmer"] = ("@keyframes shimmer{0%,60%,100%{opacity:1}30%{opacity:.35}}"
                        "@media (prefers-reduced-motion:reduce){text{animation:none!important}}")
    # the facts, typed out one after another
    delay = 0.9
    delay = mono_text(s, ix, iy, [("mitaro", t["accent"]), ("@", t["grey"]), ("github", t["accent"])], isize,
                      delay=delay, steps_per_s=40) + 0.05
    mono_text(s, ix, iy + ilh, [("─" * 15, t["rule"])], isize)
    key_w = max(len(a) for a, _ in rows) + 2
    room = int((X1 - ix) / (isize * MONO_EM)) - key_w
    for k, (a, b) in enumerate(rows):
        b = b if len(b) <= room else b[:room - 1] + "…"
        delay = mono_text(s, ix, iy + (k + 2) * ilh, [(f"{a}:".ljust(key_w), t["second"]), (b, t["ink"])], isize,
                          delay=delay, steps_per_s=95) + 0.03
    y = iy + (len(rows) + 2.4) * ilh
    bw = 3 * isize * MONO_EM
    for k, tok in enumerate(PALETTE + ["ink", "grey"]):
        s.g("grow", f"transform-origin:{ix + (k + 0.5) * bw:.0f}px {y - isize * 0.4:.0f}px;--t:{delay + 0.1 + k * 0.08:.2f}s")
        s.rect(ix + k * bw, y - isize * 0.9, bw, isize * 1.15, t[tok],
               extra=f'class="wave" style="--t:{3 + k * 0.25:.2f}s"')
        s.end()
    y += ilh * 1.3
    mono_text(s, ix, y, [("$ ", t["second"])], isize)
    s.rect(ix + mono_width(isize, "$ "), y - isize + 2, isize * MONO_EM, isize, t["ink"], extra='class="blink"')
    return s


# ------------------------------------------------------------------ 03 Map: repositories as a constellation
def sky_theme():
    return dict(THEMES["dark"], rule="#262626")


def star_map(_t):
    t = sky_theme()
    BG_HOLDER[0] = t["bg"]
    repos = sorted(DATA["repos"], key=lambda r: r["created"])
    H = 470 if MOBILE else 430
    s = page(t, H, "03 Map: my repositories as a constellation, in the order I made them; the higher and larger "
             "the star, the more commits. " + ", ".join(f"{REPO_NAMES.get(r['name'].lower(), r['name'])} "
                                                       f"{r['commits']}" for r in repos) + ".",
             "Stars twinkle, shooting stars cross the sky, and a line draws itself through the repositories from the "
             "first to the newest, with a light running along it.")
    rnd = random.Random(42)
    for k in range(90 if MOBILE else 160):
        x, y, r, o = rnd.uniform(0, W), rnd.uniform(56, H - 40), rnd.choice((0.6, 0.8, 1.1)), round(rnd.uniform(0.15, 0.6), 2)
        if k % 3:
            s.circle(x, y, r, t["grey"], o)
        else:
            s.circle(x, y, r + 0.3, t["grey"], extra=f'class="twinkle" style="--o:{o + 0.2:.2f};'
                                                      f'--d:{rnd.uniform(2.2, 5):.1f}s;--t:-{rnd.uniform(0, 5):.1f}s"')
    # shooting stars, now and then
    trail = s.uid("tr")
    s.defs.append(f'<linearGradient id="{trail}"><stop offset="0" stop-color="{t["ink"]}" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="{t["ink"]}"/></linearGradient>')
    s.css["shoot"] = ("@keyframes shoot{0%{transform:translate(0,0);opacity:0}1%{opacity:1}"
                      "7%,100%{transform:translate(260px,110px);opacity:0}}"
                      ".shoot{opacity:0;animation:shoot var(--d) cubic-bezier(.3,0,.7,1) infinite;animation-delay:var(--t)}")
    for k, (sx, sy, dur, lag) in enumerate([(W * 0.18, 70, 11, 2.5), (W * 0.55, 60, 14, 8.0), (W * 0.05, 140, 17, 13.0)]):
        s.add(f'<g class="shoot" style="--d:{dur}s;--t:{lag}s"><g transform="rotate(23 {sx:.0f} {sy})">'
              f'<rect x="{sx - 70:.0f}" y="{sy - 0.75}" width="70" height="1.5" rx=".75" fill="url(#{trail})"/>'
              f'<circle cx="{sx:.0f}" cy="{sy}" r="1.6" fill="{t["ink"]}"/></g></g>')
    head(s, t, "03", "Map", "in the order I made them")
    left, right, top, bottom = X0 + 30, X1 - 30, 110, H - 92
    top_c = max(r["commits"] for r in repos) or 1
    pts = []
    for i, r in enumerate(repos):
        x = left + (right - left) * i / max(1, len(repos) - 1)
        y = bottom - (bottom - top) * math.log1p(r["commits"]) / math.log1p(top_c)
        pts.append((x, y, r))
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y, _ in pts)
    length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    s.path(line, "none", t["leaf"], 1.4, opacity=0.8,
           extra=f'class="draw" stroke-dasharray="{length:.0f}" style="--len:{length:.0f};--t:.4s"')
    s.path(line, "none", t["khaki"], 2.6, extra=f'class="packet" stroke-dasharray="26 {length + 60:.0f}" '
                                              f'style="--start:26;--end:-{length:.0f};--t:3s;animation-duration:7s"')
    for i, (x, y, r) in enumerate(pts):
        langs = {k: v for k, v in r["langs"].items() if k != "Rich Text Format"}
        main = max(langs, key=langs.get) if langs else "Other"
        tone = t[LANG_TOKEN.get(main if main in CODE_LANGS else "Other", "grey")]
        rad = 3 + math.sqrt(r["commits"]) * (0.9 if MOBILE else 1.2)
        s.circle(x, y, rad * 2.6, tone, 0.18, extra=f'class="pulse" style="--t:{i * 0.37:.2f}s"')
        s.circle(x, y, rad, tone)
        name = REPO_NAMES.get(r["name"].lower(), r["name"])
        limit = 9 if MOBILE else 14
        if len(name) > limit:
            name = name[:limit - 1] + "…"
        up = i % 2 == 0
        ly = y - rad - 10 if up else y + rad + 20
        s.g("fade", f"--t:{0.6 + i * 0.12:.2f}s")
        s.text(x, ly, name, 12.5 if MOBILE else 13.5, t["ink"], 600, "middle")
        s.end()
        _, m = r["created"].split("-")[:2]
        s.text(x, H - 52, f"{MONTHS[int(m) - 1]}", 11.5, t["grey"], anchor="middle")
        s.text(x, H - 36, f"{r['commits']}", 11.5, tone, 700, "middle")
    s.line(X0, H - 70, X1, H - 70, t["rule"], 1)
    return s


# ------------------------------------------------------------------ 04 Toolkit
TOOLKIT = [("Languages", ["Java", "Python", "TypeScript", "JavaScript", "Rust", "SQL"]),
           ("Frameworks", ["Spring Boot", "Svelte", "Flask", "Tauri"]),
           ("Tools", ["SQLite", "Docker", "Git and Actions", "Linux", "Figma", "Zed"])]


def toolkit(t):
    langs = all_langs()
    total = sum(v for _, v in langs) or 1
    size, cells, step = (13.5, 28, 26) if MOBILE else (15, 50, 28)
    y0 = 104 + len(langs) * step
    if MOBILE:
        blocks = [wrap(" · ".join(items), 17, X1 - X0) for _, items in TOOLKIT]
        H = y0 + sum(40 + 26 * len(b) + 14 for b in blocks) + 20
    else:
        H = y0 + 260
    s = page(t, H, "04 Toolkit. Code by language: " + ", ".join(f"{k} {round(100 * v / total)}%" for k, v in langs)
             + ". " + " ".join(f"{a}: {', '.join(b)}." for a, b in TOOLKIT),
             "Language shares drawn as ASCII bars of block glyphs that fill in, then what I use.")
    head(s, t, "04", "Toolkit", f"{code_size()} of code in {len(CODE_REPOS)} repositories")
    for i, (k, v) in enumerate(langs):
        n = round(cells * v / total)
        pct = f"{round(100 * v / total):>3}%"
        parts = [(f"{k:<11} ", t["ink"]), ("█" * n, t[LANG_TOKEN.get(k, "grey")]),
                 ("░" * (cells - n), t["rule"]), (f" {pct}", t["grey"])]
        mono_text(s, X0, 92 + i * step, parts, size, delay=0.2 + i * 0.25, steps_per_s=50)
    glint = s.uid("gl")
    s.defs.append(f'<linearGradient id="{glint}"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="#fff" stop-opacity=".38"/><stop offset="1" stop-color="#fff" '
                  f'stop-opacity="0"/></linearGradient>')
    s.rect(X0 - 90, 92 - size - 4, 90, len(langs) * step + 4, f"url(#{glint})",
           extra=f'class="glide" style="--w:{X1 - X0 + 90}px;--t:3s;animation-duration:6s"')
    s.line(X0, y0, X1, y0, t["rule"], 1.2)
    if MOBILE:
        y = y0 + 34
        for i, ((title, _), lines) in enumerate(zip(TOOLKIT, blocks)):
            caps(s, X0, y, title, t[("accent", "suede", "leaf")[i]], weight=700)
            s.g("fade", f"--t:{0.6 + i * 0.15:.2f}s")
            for j, ln in enumerate(lines):
                s.text(X0, y + 30 + j * 26, ln, 17, t["ink"])
            s.end()
            y += 40 + 26 * len(lines) + 14
        return s
    cw = (X1 - X0) / len(TOOLKIT)
    for i, (title, items) in enumerate(TOOLKIT):
        x = X0 + i * cw + (16 if i else 0)
        caps(s, x, y0 + 34, title, t[("accent", "suede", "leaf")[i]], weight=700)
        for j, item in enumerate(items):
            s.g("fade", f"--t:{0.6 + i * 0.15 + j * 0.06:.2f}s")
            s.text(x, y0 + 68 + j * 27, item, 17, t["ink"])
            s.end()
        if i:
            s.line(X0 + i * cw, y0 + 18, X0 + i * cw, H - 22, t["rule"], 1.2)
    return s


# ------------------------------------------------------------------ 05 Now
NOW = [("building", "accent", "Java and Flask backends with a cleaner structure"),
       ("studying", "suede", "security: encryption, hashing, local-first design"),
       ("prototype", "leaf", "a personal AI assistant, Jarvis-style"),
       ("student", "khaki", "computer science at MTUCI")]


def now(t):
    size = 13 if MOBILE else 15
    cw = size * MONO_EM
    tag_w = 12
    room = int((X1 - X0 - 36) / cw) - tag_w
    lines = []
    for tag, tok, txt in NOW:
        parts = [txt] if len(txt) <= room else wrap_mono(txt, room)
        lines.append((tag, tok, parts))
    rows = 1 + sum(len(p) for _, _, p in lines) + 2
    box_top = 66
    H = box_top + 30 + rows * (size + 11) + 30
    s = page(t, H, "05 Now: " + "; ".join(f"{tag} {txt}" for tag, _, txt in NOW) + ".",
             "A terminal that types out what I am working on now, with a spinner on the current work and the next Campus "
             "build filling an ASCII progress bar.")
    head(s, t, "05", "Now", "updated by hand")
    s.rect(X0, box_top, X1 - X0, H - box_top - 22, t["panel"], rx=8)
    x, y = X0 + 18, box_top + 32
    lh = size + 11
    delay = mono_text(s, x, y, [("$ ", t["second"]), ("now --verbose", t["ink"])], size, 0.4,
                      mask=t["panel"]) + 0.2
    y += lh
    for k, (tag, tok, parts) in enumerate(lines):
        for j, part in enumerate(parts):
            label = f"[{tag:<9}] " if j == 0 else " " * tag_w
            delay = mono_text(s, x, y, [(label, t[tok]), (part, t["ink"])], size, delay, steps_per_s=70,
                              mask=t["panel"]) + 0.05
            if k == 0 and j == 0:
                sx = x + mono_width(size, label + part) + cw
                s.add(f'<g font-family="{MONO}" font-size="{size}" font-weight="700" fill="{t[tok]}">')
                s.frames(4, 0.6, lambda q, sx=sx, y=y: s.add(f'<text x="{sx:.1f}" y="{y:.1f}">{esc(SPINNER[q])}</text>'))
                s.add("</g>")
            y += lh
    # the next Campus build: an ASCII bar that fills smoothly, its stage changing as it goes
    cells = min(24, room - 11)
    label = "[campus   ] "
    bx = x + mono_width(size, label)
    s.g("fade", f"--t:{delay:.2f}s")
    mono_text(s, x, y, [(label, t["accent"]), ("░" * cells, t["rule"])], size)
    clip = s.uid("bar")
    s.defs.append(f'<clipPath id="{clip}"><rect x="{bx:.1f}" y="{y - size:.1f}" width="{cells * cw:.1f}" '
                  f'height="{size * 1.4:.1f}" class="fillbar"/></clipPath>')
    s.css["fillbar"] = ("@keyframes fillbar{0%,25%{transform:scaleX(1)}25.01%{transform:scaleX(0)}"
                        "100%{transform:scaleX(1)}}.fillbar{transform-box:fill-box;transform-origin:0 0;"
                        "animation:fillbar 8s cubic-bezier(.3,0,.6,1) infinite}")
    s.add(f'<g clip-path="url(#{clip})">')
    mono_text(s, bx, y, [("█" * cells, t["accent"])], size)
    s.add("</g>")
    sx = bx + (cells + 1) * cw
    stages = [("ready ✓", t["leaf"]), ("compiling", t["grey"]), ("testing", t["grey"]), ("packaging", t["grey"])]
    s.add(f'<g font-family="{MONO}" font-size="{size}">')
    s.frames(4, 8, lambda q: s.add(f'<text x="{sx:.1f}" y="{y:.1f}" fill="{stages[q][1]}">{stages[q][0]}</text>'))
    s.add("</g>")
    s.end()
    y += lh
    mono_text(s, x, y, [("$ ", t["second"])], size)
    s.rect(x + mono_width(size, "$ "), y - size + 2, cw, size, t["ink"], extra='class="blink"')
    return s


def wrap_mono(txt, room):
    lines, cur = [], ""
    for wd in txt.split():
        t = (cur + " " + wd).strip()
        if len(t) <= room or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    return lines + [cur]


if __name__ == "__main__":
    both(cover, "cover")
    both(campus, "campus")
    both(about, "about")
    both(star_map, "map")
    both(toolkit, "toolkit")
    both(now, "now")
