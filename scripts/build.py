#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

The README follows the classic GitHub profile: a greeting, the tech stack, socials, the core project,
trophies and a stats card. The pictures are drawn here rather than borrowed from badge and stats services,
so they load fast, never break when a service is down and share one look: black and white, like the avatar
(a man in a white robe on a snowy driveway). The Earth beside the greeting turns in ASCII characters
(Natural Earth coastlines in land.txt); Campus is a terminal page with a live diagram of how it syncs.
All motion is CSS and stops under prefers-reduced-motion; every element rests in its final state. Black works
in both GitHub themes, so each picture is built once, plus a narrow version for phones where it helps.
"""
import datetime as dt
import json
import math
import os
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
# the avatar is a black and white photo: snow and a white robe, grey asphalt, dark hedges, a black night.
# Every text shade keeps 4.5:1 contrast or more on black.
MONO_T = dict(bg="#000000", ink="#f5f5f5", grey="#a8a8a8", rule="#262626", panel="#0d0d0d", dim="#4d4d4d",
              accent="#ffffff", second="#dcdcdc", khaki="#c4c4c4", suede="#adadad", leaf="#969696", bark="#808080")
LANG_SHADES = ["#ffffff", "#c9c9c9", "#999999", "#707070", "#4f4f4f", "#383838", "#262626"]
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
    """A black card with a hairline edge, so it reads as a card on GitHub's light and dark pages alike."""
    s = Svg(W, h, title, desc)
    s.rect(0.5, 0.5, W - 1, h - 1, t["bg"], t["rule"], 1, rx=12)
    return s


def caps(s, x, y, txt, fill, anchor="start", size=12.5, weight=600):
    s.text(x, y, txt.upper(), size, fill, weight, anchor, ls=1.5)


def head(s, t, num, label, right=""):
    """Section line: number in the accent, label in caps, a hairline that draws itself, a note on the right."""
    right = "" if MOBILE else right
    lx = X0 + 34 if num else X0
    if num:
        caps(s, X0, 42, num, t["accent"], size=13.5, weight=700)
    caps(s, lx, 42, label, t["ink"], size=13.5, weight=700)
    start = lx + text_width(13.5, label.upper(), 700, 1.5) + 14
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


def both(fn, name, layouts=LAYOUTS):
    """Builds a picture for each layout: name.svg for wide screens and name-mobile.svg for phones."""
    global W, X0, X1, MOBILE
    for suffix, (w, x0, x1, mobile) in layouts.items():
        W, X0, X1, MOBILE = w, x0, x1, mobile
        BG_HOLDER[0] = MONO_T["bg"]
        fn(MONO_T).save(OUT, f"{name}{suffix}.svg")


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
    tones = dict(down=t["accent"], up=t["bark"])
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
        s.circle(x + 16, y + 19.5, 4, t["dim"], extra=f'class="cyc" style="opacity:0;'
                                                         f'{cycle(s, "dotoff", [(36, 76)], period)}"')
    # what the colours mean
    ly = bottom + 30
    lx = X0
    for lane, label in (("down", "changes to devices"), ("up", "edits back to the host")):
        s.line(lx, ly - 4, lx + 22, ly - 4, tones[lane], 3)
        s.add(f'<text x="{lx + 30}" y="{ly:.1f}" font-size="12" font-family="{MONO}" fill="{t["grey"]}">{label}</text>')
        lx += 30 + mono_width(12, label) + 28
    return ly


def campus(_t):
    t = _t
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
    s = page(t, H, "Campus, my core project: a site and an app for one study group that lives on the group "
             "leader's own computer. " + ", ".join(f"{v} {lab}" for v, lab in items) + ".",
             "A dark terminal page: how Campus syncs, from the host computer through an HTTPS tunnel to phones that "
             "keep working offline, and git log --graph of the latest Campus commits typing itself out.")
    head(s, t, "", "Core project", "github.com/mitaro-cs/Campus")
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


# ------------------------------------------------------------------ the Earth beside the greeting
def globe_header(t):
    s = Svg(W, 272, "The Earth turning in ASCII characters with Moscow marked and a satellite circling it.",
            "Real coastlines as ASCII glyphs wrapped onto a sphere, in black and white like the avatar.")
    globe(s, t, W / 2, 10, 11)
    return s


# ------------------------------------------------------------------ badges: the tech stack and socials
ICONS = json.load(open(os.path.join(HERE, "icons.json"), encoding="utf-8"))   # Simple Icons, CC0
ICON_NAMES = {"openjdk": "Java", "zedindustries": "Zed", "gnubash": "Bash", "apachemaven": "Maven",
              "nodedotjs": "Node.js", "html5": "HTML", "maildotru": "Email"}
STACK = [("Languages", ["openjdk", "python", "typescript", "javascript", "rust", "html5", "css", "gnubash"]),
         ("Frameworks", ["springboot", "svelte", "flask", "tauri", "nodedotjs", "vite", "apachemaven"]),
         ("Tools", ["sqlite", "docker", "git", "githubactions", "linux", "macos", "figma", "zedindustries"])]
BADGE_H = 30


def badge_label(slug):
    return (ICON_NAMES.get(slug) or ICONS[slug]["title"]).upper()


def badge_width(slug):
    return 14 + 15 + 9 + text_width(11.5, badge_label(slug), 700, 1.4) + 13


def badge(s, t, x, y, slug, delay=0.0):
    """A for-the-badge style badge: the logo and the name in white on black."""
    w = badge_width(slug)
    s.g("pop", f"--t:{delay:.2f}s")
    s.rect(x + 0.5, y + 0.5, w - 1, BADGE_H - 1, "#0b0b0b", "#333333", 1, rx=5)
    s.path(ICONS[slug]["path"], t["accent"], extra=f'transform="translate({x + 14:.1f} {y + 7.5:.1f}) scale(.625)"')
    s.text(x + 38, y + BADGE_H / 2 + 4.2, badge_label(slug), 11.5, t["ink"], 700, ls=1.4)
    s.end()
    return w


def glint_over(s, rects, delay, period=7.0):
    """A soft band of light that runs over the given rectangles now and then, and nowhere else."""
    clip, band = s.uid("gc"), s.uid("gb")
    xs = [r[0] for r in rects] + [r[0] + r[2] for r in rects]
    x0, x1 = min(xs), max(xs)
    y0 = min(r[1] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    s.defs.append(f'<clipPath id="{clip}">' + "".join(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                                                      f'rx="5"/>' for x, y, w, h in rects) + "</clipPath>"
                  f'<linearGradient id="{band}"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" '
                  f'stop-opacity="0"/></linearGradient>')
    s.add(f'<g clip-path="url(#{clip})">')
    s.rect(x0 - 120, y0, 120, y1 - y0, f"url(#{band})",
           extra=f'class="glide" style="--w:{x1 - x0 + 120:.0f}px;--t:{delay:.2f}s;animation-duration:{period}s"')
    s.add("</g>")


def stack(t):
    """The tech stack as badges, one group per line, wrapping like inline badges do."""
    gap, label_w = 8, (0 if MOBILE else 112)
    placed, y = [], 0
    for title, slugs in STACK:
        if MOBILE:
            placed.append(("label", title, 0, y + 14))
            y += 24
        else:
            placed.append(("label", title, 0, y + BADGE_H / 2 + 4.5))
        x = label_w
        row = []
        for slug in slugs:
            w = badge_width(slug)
            if x + w > W and x > label_w:
                placed.append(("row", row, 0, 0))
                row, x, y = [], label_w, y + BADGE_H + gap
            row.append((slug, x, y, w))
            x += w + gap
        placed.append(("row", row, 0, 0))
        y += BADGE_H + gap + (18 if MOBILE else 10)
    H = y - (18 if MOBILE else 10) - gap + 2
    every = [ICONS[sl]["title"] if sl not in ICON_NAMES else ICON_NAMES[sl] for _, sls in STACK for sl in sls]
    s = Svg(W, H, "Tech stack: " + ", ".join(every) + ".",
            "Badges with the logo and name of each language, framework and tool, in black and white.")
    k = 0
    for kind, what, x, y in placed:
        if kind == "label":
            caps(s, x, y, what, t["grey"], size=11.5)
            continue
        for slug, bx, by, w in what:
            badge(s, t, bx, by, slug, 0.1 + k * 0.04)
            k += 1
        glint_over(s, [(bx, by, w, BADGE_H) for _, bx, by, w in what], 2.5 + k * 0.08)
    return s


SOCIALS = [("telegram", "https://t.me/treadways"), ("maildotru", "mailto:miri.saro@bk.ru"),
           ("instagram", "https://instagram.com/stere.os")]


def social_badge(slug, delay):
    def draw(t):
        w = badge_width(slug)
        s = Svg(w, BADGE_H, ICON_NAMES.get(slug, ICONS[slug]["title"]))
        badge(s, t, 0, 0, slug)
        glint_over(s, [(0, 0, w, BADGE_H)], delay, 6.0)
        return s
    return draw


# ------------------------------------------------------------------ trophies
RANKS = ["C", "B", "A", "AA", "AAA", "S", "SS", "SSS"]
CUP = ["..XXXXXXXX..",
       "XXXXXXXXXXXX",
       "X.XXXXXXXX.X",
       "X.XXXXXXXX.X",
       ".XXXXXXXXXX.",
       "..XXXXXXXX..",
       "...XXXXXX...",
       "....XXXX....",
       ".....XX.....",
       ".....XX.....",
       "....XXXX....",
       "...XXXXXX..."]
METALS = {"top": ("#ffffff", "#c8c8c8", "#7d7d7d"), "mid": ("#cfcfcf", "#959595", "#5c5c5c"),
          "low": ("#8c8c8c", "#636363", "#404040")}


def trophy_list():
    f = facts()
    repos = DATA["repos"]
    act = DATA.get("activity") or {}
    pin = DATA.get("pin") or {}
    since = dt.date.fromisoformat(DATA["created"][:10])
    years = (f["last"].date() - since).days // 365 if f["last"] else 0
    langs = len({k for r in CODE_REPOS for k in r["langs"] if k != "Rich Text Format"})
    return [("Commits", sum(r["commits"] for r in repos), "commits", (1, 10, 50, 100, 200, 500, 1000, 2000)),
            ("Pull requests", act.get("prs", 0), "opened", (1, 5, 10, 20, 50, 100, 200, 500)),
            ("Merged", act.get("merged", 0), "merged PRs", (1, 5, 10, 20, 50, 100, 200, 500)),
            ("Repositories", len(repos), "public", (1, 3, 5, 10, 20, 30, 50, 100)),
            ("Stars", sum(r.get("stars", 0) for r in repos), "earned", (1, 5, 10, 30, 50, 100, 200, 500)),
            ("Followers", DATA.get("followers", 0), "following me", (1, 3, 5, 10, 20, 50, 100, 200)),
            ("Streak", f["streak"], "days in a row", (1, 3, 5, 7, 14, 30, 60, 100)),
            ("Releases", pin.get("versions", 0), "Campus versions", (1, 3, 5, 10, 20, 30, 50, 100)),
            ("Tests", pin.get("tests", 0), "test files", (1, 10, 25, 50, 100, 200, 500, 1000)),
            ("Languages", langs, "in my code", (1, 2, 3, 4, 6, 8, 10, 12)),
            ("Experience", years, "years on GitHub", (1, 2, 3, 4, 5, 6, 8, 10)),
            ("Night owl", f["night"], "% after 22:00", (5, 10, 15, 20, 25, 30, 40, 50))]


def trophy(s, t, x, y, w, h, title, value, unit, steps, i):
    level = sum(1 for v in steps if value >= v)
    rank = RANKS[level - 1] if level else "–"
    tier = "top" if level >= 6 else "mid" if level >= 3 else "low"
    hi, main, dark = METALS[tier]
    s.g("pop", f"--t:{0.1 + i * 0.07:.2f}s")
    s.rect(x + 0.5, y + 0.5, w - 1, h - 1, "#0b0b0b", "#2e2e2e", 1, rx=8)
    # the rank chip: solid for the S ranks, outlined below
    cw = 14 + text_width(11, rank, 700, 0.8)
    if tier == "top":
        s.rect(x + 10, y + 10, cw, 19, t["accent"], rx=4)
        s.text(x + 10 + cw / 2, y + 23.5, rank, 11, t["bg"], 700, "middle", 0.8)
    else:
        s.rect(x + 10.5, y + 10.5, cw - 1, 18, "none", main, 1, rx=4)
        s.text(x + 10 + cw / 2, y + 23.5, rank, 11, main, 700, "middle", 0.8)
    # the cup, in pixels, bobbing gently
    px = 4.2
    cx0, cy0 = x + w / 2 - 6 * px, y + 34
    s.add(f'<g class="bob" style="--t:-{i * 0.37:.2f}s"><use href="#cup-{tier}" x="{cx0:.1f}" y="{cy0:.1f}"/></g>')
    if not any(f'id="cup-{tier}"' in d for d in s.defs):   # each metal's cup is drawn once and reused
        rects = []
        for r, line in enumerate(CUP):
            cols = [c for c, ch in enumerate(line) if ch == "X"]
            body = [c for c in cols if 0 < c < 11] or cols
            for c in cols:
                fill = hi if c == body[0] or r == 0 else dark if c == body[-1] or c in (0, 11) else main
                rects.append(f'<rect x="{c * px:.1f}" y="{r * px:.1f}" width="{px + 0.2:.1f}" height="{px + 0.2:.1f}" '
                             f'fill="{fill}"/>')
        s.defs.append(f'<g id="cup-{tier}">{"".join(rects)}</g>')
    if tier != "low":
        for k, (dx, dy) in enumerate(((-9, 4), (13.5, 1), (12.5, 9))):
            s.rect(cx0 + dx * px, cy0 + dy * px, 3, 3, hi,
                   extra=f'class="twinkle" style="--o:.9;--d:{2.2 + k * 0.7:.1f}s;--t:-{i * 0.5 + k:.1f}s"')
    s.text(x + w / 2, y + 108, title, 13.5, t["ink"], 700, "middle")
    s.text(x + w / 2, y + 126, f"{value} {unit}" if not unit.startswith("%") else f"{value}{unit}", 11.5,
           t["grey"], anchor="middle")
    # progress to the next rank
    nxt = next((v for v in steps if v > value), None)
    prev = ([v for v in steps if v <= value] or [0])[-1]
    frac = 1.0 if nxt is None else (value - prev) / max(1, nxt - prev)
    bx, bw = x + 14, w - 28
    s.rect(bx, y + 140, bw, 4, t["rule"], rx=2)
    if frac > 0:
        s.g("wide", f"--t:{0.8 + i * 0.07:.2f}s")
        s.rect(bx, y + 140, bw * frac, 4, main, rx=2)
        s.end()
    s.text(x + w / 2, y + 158, "max rank" if nxt is None else f"next at {nxt}", 10.5, t["bark"], anchor="middle")
    s.end()
    return (x, y, w, h)


def trophies(t):
    items = trophy_list()
    cols = 3 if MOBILE else 6
    gap = 10
    w = (W - (cols - 1) * gap) / cols
    h = 168
    rows = (len(items) + cols - 1) // cols
    H = rows * h + (rows - 1) * gap
    s = Svg(W, H, "GitHub trophies: " + "; ".join(
        f"{a} {v} {u.lstrip('%').strip()}, rank {RANKS[sum(1 for x in st if v >= x) - 1] if v >= st[0] else 'none'}"
        for a, v, u, st in items) + ".",
        "Pixel-art cups ranked C to SSS from my GitHub numbers, each with a bar to the next rank.")
    cards = []
    for i, (title, value, unit, steps) in enumerate(items):
        x, y = (i % cols) * (w + gap), (i // cols) * (h + gap)
        cards.append(trophy(s, t, x, y, w, h, title, value, unit, steps, i))
    for r in range(rows):
        glint_over(s, cards[r * cols:(r + 1) * cols], 3 + r * 1.2, 8.0)
    return s


# ------------------------------------------------------------------ stats card
STAT_ICONS = {
    "star": "M8 1.8l1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.6l-3.8 2 .7-4.3-3.1-3 4.3-.6z",
    "commit": "M1 8h4M11 8h4M8 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
    "pr": "M4 2.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM4 5.5v5M4 10.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM12 10.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM12 10.5V6a2 2 0 0 0-2-2H8M9.5 2.5 8 4l1.5 1.5",
    "merge": "M4 2.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM4 5.5v8M12 8.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM4 5.5c0 3 3 4.5 6.5 4.5",
    "issue": "M8 2a6 6 0 1 0 0 12A6 6 0 0 0 8 2zM8 7.2v1.6",
    "repo": "M3 2.5h8.5a1 1 0 0 1 1 1v10H4.5a1.5 1.5 0 0 1-1.5-1.5zM3 12a1.5 1.5 0 0 1 1.5-1.5h8",
}


def rank_of(commits, prs, issues, stars, followers):
    """github-readme-stats' rank: weighted CDFs against medians, lower percentile is better."""
    def exp_cdf(x):
        return 1 - 2 ** -x

    def log_cdf(x):
        return x / (1 + x)
    score = (2 * exp_cdf(commits / 250) + 3 * exp_cdf(prs / 50) + exp_cdf(issues / 25) + 4 * log_cdf(stars / 50)
             + log_cdf(followers / 10)) / 12
    pct = (1 - score) * 100
    levels = [(1, "S"), (12.5, "A+"), (25, "A"), (37.5, "A-"), (50, "B+"), (62.5, "B"), (75, "B-"), (87.5, "C+"),
              (100, "C")]
    return next(lev for top, lev in levels if pct <= top), pct


def stats(t):
    repos = DATA["repos"]
    act = DATA.get("activity") or {}
    commits = sum(r["commits"] for r in repos)
    stars = sum(r.get("stars", 0) for r in repos)
    last = facts()["last"]
    year_ago = (last - dt.timedelta(days=365)) if last else None
    touched = {c["repo"] for c in DATA["commits"]
               if year_ago and dt.datetime.fromisoformat(c["ts"].replace("Z", "+00:00")) >= year_ago}
    rows = [("star", "Total Stars Earned", stars), ("commit", "Total Commits", commits),
            ("pr", "Total PRs", act.get("prs", 0)), ("merge", "Merged PRs", act.get("merged", 0)),
            ("issue", "Total Issues", act.get("issues", 0)), ("repo", "Contributed to (last year)", len(touched))]
    level, pct = rank_of(commits, act.get("prs", 0), act.get("issues", 0), stars, DATA.get("followers", 0))
    langs = all_langs()
    total = sum(v for _, v in langs) or 1
    pad = 28
    if MOBILE:
        ring = (W / 2, 84 + len(rows) * 34 + 74)
        lang_x, lang_y, lang_w = pad, ring[1] + 150, W - 2 * pad
    else:
        ring = (520, 160)
        lang_x, lang_y, lang_w = 640, 84, W - 640 - pad
    H = (lang_y + len(langs) * 36 + 30) if MOBILE else 84 + len(rows) * 34 + 40
    s = page(t, H, f"Mitaro's GitHub stats: {stars} stars, {commits} commits, {act.get('prs', 0)} pull requests, "
             f"{act.get('merged', 0)} merged, {act.get('issues', 0)} issues, contributed to {len(touched)} "
             f"repositories in the last year, rank {level}. Languages: "
             + ", ".join(f"{k} {round(100 * v / total)}%" for k, v in langs) + ".",
             "A stats card: the numbers roll in, the rank ring draws itself, the language bars fill.")
    s.g("fade", "--t:.1s")
    s.text(pad, 46, "Mitaro's GitHub Stats", 20, t["ink"], 700)
    s.end()
    for i, (icon, label, value) in enumerate(rows):
        y = 88 + i * 34
        s.g("fade", f"--t:{0.25 + i * 0.08:.2f}s")
        s.path(STAT_ICONS[icon], "none", t["grey"], 1.4, extra=f'transform="translate({pad} {y - 13})"')
        s.text(pad + 28, y, f"{label}:", 15, t["grey"], 600)
        s.end()
        odometer(s, W - pad - 60 if MOBILE else 380, y, value, 16, t["ink"], 0.3 + i * 0.1)
    # the rank ring draws itself to the share of developers this rank beats
    cx, cy = ring
    r = 56
    circ = 2 * math.pi * r
    arc = circ * max(0.02, min(1, (100 - pct) / 100))
    s.circle(cx, cy, r + 14, t["accent"], 0.06, extra='class="pulse"')
    s.circle(cx, cy, r, "none", extra=f'stroke="{t["rule"]}" stroke-width="9"')
    s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{t["accent"]}" stroke-width="9" '
          f'stroke-linecap="round" stroke-dasharray="{arc:.1f} {circ:.1f}" transform="rotate(-90 {cx:.1f} {cy:.1f})" '
          f'class="draw" style="--len:{arc:.1f};--t:.6s"/>')
    s.g("fade", "--t:1.2s")
    s.text(cx, cy + 12, level, 34, t["ink"], 700, "middle")
    s.text(cx, cy + r + 34, f"rank · top {pct:.0f}%", 11.5, t["grey"], anchor="middle")
    s.end()
    # the languages, each with a bar in its own shade
    caps(s, lang_x, lang_y - 2 if not MOBILE else lang_y - 22, "Most used languages", t["grey"], size=11.5)
    for i, (name, v) in enumerate(langs):
        y = lang_y + 22 + i * 36 if not MOBILE else lang_y + i * 36
        share = v / total
        s.g("fade", f"--t:{0.5 + i * 0.08:.2f}s")
        s.text(lang_x, y, name, 13.5, t["ink"], 600)
        s.text(lang_x + lang_w, y, f"{100 * share:.1f}%", 12.5, t["grey"], anchor="end")
        s.end()
        s.rect(lang_x, y + 8, lang_w, 5, t["rule"], rx=2.5)
        s.g("wide", f"--t:{0.7 + i * 0.1:.2f}s")
        s.rect(lang_x, y + 8, max(3, lang_w * share), 5, LANG_SHADES[min(i, len(LANG_SHADES) - 1)]
               if name != "Other" else "#5a5a5a", rx=2.5)
        s.end()
    return s


if __name__ == "__main__":
    both(globe_header, "globe", {"": (340, 0, 340, False)})
    both(stack, "stack")
    for k, (slug, _) in enumerate(SOCIALS):
        both(social_badge(slug, 2 + k * 1.3), f"badge-{slug}", {"": (0, 0, 0, False)})
    both(campus, "campus")
    both(trophies, "trophies")
    both(stats, "stats")
