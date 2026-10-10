#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Concept: the profile as an editorial spread with a terminal running inside it. Big type, a strict
grid, hairline rules, a cobalt accent with a coral second, and on every page the real data is the
object. ASCII is the second voice: a rotating ASCII globe on the cover, sync spinners in the Campus
diagram, commands that type themselves on the Rhythm page, and language bars made of block glyphs.
Motion carries the data: headlines lift out of their rules, numbers roll in like a split-flap
board, sync packets run, a radar hand sweeps the 24-hour dial, and the cover runs a ticker of my
latest commits. All motion is CSS and stops under prefers-reduced-motion; every element rests in
its final state. Each page is rendered twice, -light.svg and -dark.svg, picked with <picture>.
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

# the avatar's colours (a park bench, khaki trousers, a pale blue shirt, sunlit skin), tuned so every text
# colour keeps at least 4.5:1 contrast on its background
THEMES = {
    "light": dict(bg="#efebe3", ink="#1b1716", grey="#5a524b", rule="#d6cdbf", accent="#3f6273",
                  second="#a5552f", panel="#e5dfd4"),
    "dark": dict(bg="#141112", ink="#eef1ee", grey="#bdaea3", rule="#302a27", accent="#a2bbc5",
                 second="#e6a986", panel="#1e1a19"),
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MSK = dt.timezone(dt.timedelta(hours=3))
NIGHT_HOURS = (22, 23, 0, 1, 2, 3)
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
    return dict(per_day=per_day, hours=hours, streak=best, last=times[-1] if times else None,
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


def headline(s, x, baseline, txt, size, fill, ls, delay=0.0):
    """A big word that lifts out of the line it stands on."""
    cid = s.uid("hl")
    s.defs.append(f'<clipPath id="{cid}"><rect x="0" y="{baseline - size}" width="{W}" height="{size * 1.12:.0f}"/>'
                  "</clipPath>")
    s.add(f'<g clip-path="url(#{cid})">')
    s.g("lift", f"--dy:{size:.0f}px;--t:{delay}s")
    s.text(x, baseline, txt, size, fill, 700, ls=ls)
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


# ------------------------------------------------------------------ ASCII globe
RAMP = " .:-=+*"


def globe_rows(phase, cols, rows, cw, lh):
    """One frame of an ASCII globe: (grid, shade) strings per row; meridians every 30 degrees."""
    radius = min(cols * cw, rows * lh) / 2 - 2
    light = (-0.45, 0.5, 0.74)
    out = []
    for r in range(rows):
        grid_row, shade_row = [], []
        for c in range(cols):
            px = (c + 0.5 - cols / 2) * cw / radius
            py = (r + 0.5 - rows / 2) * lh / radius
            if px * px + py * py > 1:
                grid_row.append(" ")
                shade_row.append(" ")
                continue

            def lonlat(dx, dy):
                x, y = px + dx * cw / radius, py + dy * lh / radius
                rr = min(1.0, x * x + y * y)
                z = math.sqrt(1 - rr)
                return math.degrees(math.atan2(x, z)) + phase, math.degrees(math.asin(max(-1, min(1, -y))))

            (lon_l, _), (lon_r, _) = lonlat(-0.5, 0), lonlat(0.5, 0)
            (_, lat_t), (_, lat_b) = lonlat(0, -0.5), lonlat(0, 0.5)
            on_m = math.floor(lon_l / 30) != math.floor(lon_r / 30)
            on_p = math.floor(lat_b / 30) != math.floor(lat_t / 30)
            z = math.sqrt(max(0.0, 1 - px * px - py * py))
            lum = max(0.0, px * light[0] + -py * light[1] + z * light[2])
            if on_m and on_p:
                grid_row.append("+")
            elif on_m:
                grid_row.append("|")
            elif on_p:
                grid_row.append("=" if abs(lat_t + lat_b) < 20 else "-")
            else:
                grid_row.append(" ")
            shade_row.append(" " if grid_row[-1] != " " else RAMP[min(len(RAMP) - 1, int(lum * (len(RAMP) - 0.01)))])
        out.append(("".join(grid_row), "".join(shade_row)))
    return out


def ascii_globe(s, t, x, y, cols=44, rows=20, size=12, n=16, dur=4.8):
    cw, lh = size * MONO_EM, size * 1.12

    def draw(i):
        for r, (grid, shade) in enumerate(globe_rows(i / n * 30, cols, rows, cw, lh)):
            yy = y + r * lh
            s.add(f'<text x="{x}" y="{yy:.1f}" fill="{t["grey"]}" fill-opacity=".55" xml:space="preserve">{shade}</text>'
                  f'<text x="{x}" y="{yy:.1f}" fill="{t["accent"]}" xml:space="preserve">{grid}</text>')

    s.add(f'<g font-family="{MONO}" font-size="{size}" style="white-space:pre">')
    s.frames(n, dur, draw)
    s.add("</g>")


# ------------------------------------------------------------------ cover
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
    caps(s, X0, y, "Latest", t["second"], weight=700)
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


def cover(t):
    f = facts()
    repos = DATA["repos"]
    last = f["last"]
    deck = "I build local-first software: the data stays on a machine you control, not on someone else's server."
    if MOBILE:
        head_y, head_size, name_y, para_y, para_w = 150, 100, 202, 236, X1 - X0
        para_end = para_y + 18.5 * 1.45 * len(wrap(deck, 18.5, para_w))
        globe_x, globe_y = (W - 44 * 12 * MONO_EM) / 2, para_end + 30
        y_rule = globe_y + 19 * 12 * 1.12 + 26
    else:
        head_y, head_size, name_y, para_y, para_w = 184, 124, 240, 274, 420
        globe_x, globe_y, y_rule = 512, 84, 376
    fig_y = y_rule + 56
    fig_end = fig_y + (86 if MOBILE else 0) + 54
    H = fig_end + (52 if MOBILE else 80)
    s = page(t, H, "Mitaro. Omar, computer science student at MTUCI. I build local-first software: the data stays "
             "on a machine you control. Core project: Campus.",
             "A rotating ASCII globe, the key figures and a ticker of my latest commits.")
    caps(s, X0, 42, "mitaro-cs" if MOBILE else "mitaro-cs · GitHub profile", t["grey"])
    if last:
        caps(s, X1, 42, f"last commit {last.day} {MONTHS[last.month - 1]} {last.year}", t["grey"], "end")
    s.g("wide")
    s.line(X0, 56, X1, 56, t["ink"], 1.5)
    s.end()
    headline(s, X0 - 5, head_y, "Mitaro", head_size, t["ink"], -4, 0.15)
    s.g("fade", "--t:.6s")
    s.text(X0, name_y, "Omar, CS student at MTUCI.", 21, t["ink"], 700)
    s.end()
    para(s, X0, para_y, deck, 18.5, t["grey"], para_w, 1.45, delay=0.75)
    ascii_globe(s, t, globe_x, globe_y)
    s.line(X0, y_rule, X1, y_rule, t["rule"], 1.2)
    figures(s, t, fig_y, [(sum(r["commits"] for r in repos), "commits"), (len(repos), "public repositories"),
                          (code_size(), "of code"), ("Campus", "core project")], accent_last=True, delay=0.5,
            cols=2 if MOBILE else None)
    s.line(X0, fig_end, X1, fig_end, t["ink"], 1.5)
    if MOBILE:
        ticker(s, t, fig_end + 32)
        return s
    caps(s, X0, fig_end + 26, "Contents", t["grey"])
    x = X0 + 114
    for num, name in (("01", "Campus"), ("02", "Rhythm"), ("03", "Toolkit")):
        caps(s, x, fig_end + 26, num, t["accent"], weight=700)
        caps(s, x + 28, fig_end + 26, name, t["ink"], weight=700)
        x += 28 + text_width(12.5, name.upper(), 700, 1.5) + 30
    caps(s, X1, fig_end + 26, f"online since {DATA['created'][:4]}", t["grey"], "end")
    s.line(X0, fig_end + 40, X1, fig_end + 40, t["rule"], 1.2)
    ticker(s, t, fig_end + 66)
    return s


# ------------------------------------------------------------------ 01 Campus
SPINNER = "|/-\\"
CAMPUS_TEXT = ("A site and an app for one study group: homework, a schedule from an .ics file, news and files. It "
               "lives on the group leader's own computer, and every phone keeps a copy that syncs when the host is "
               "back on.")


def diagram(s, t, bx, bw, top):
    """How Campus works, drawn as the system it is; sync packets run from the host to every device."""
    caps(s, bx, top, "How it works", t["grey"])
    s.rect(bx, top + 12, bw, 84, t["panel"], t["ink"], 1.2)
    caps(s, bx + 14, top + 36, "Host · group leader's computer", t["accent"], size=12, weight=700)
    s.text(bx + 14, top + 62, "Spring Boot · SQLite · AES-256-GCM", 16, t["ink"], 600)
    s.text(bx + 14, top + 84, "Windows or macOS app, one-click updates", 14, t["grey"])
    gap = 10
    cw = (bw - gap * 2) / 3
    centers = [bx + cw / 2 + i * (cw + gap) for i in range(3)]
    hb, hl, dv = top + 96, top + 122, top + 138
    s.line(centers[1], hb, centers[1], hl, t["rule"], 1.5)
    s.line(centers[0], hl, centers[-1], hl, t["rule"], 1.5)
    if MOBILE:
        s.text(centers[1] + 10, hl - 8, "HTTPS tunnel", 13.5, t["grey"])
    else:
        s.text(centers[1] - 10, hl - 8, "HTTPS tunnel · one link, one QR", 13.5, t["grey"], anchor="end")
    for i, (name, note) in enumerate((("Phone", "own copy"), ("Phone", "works offline"), ("Laptop", "syncs later"))):
        x = bx + i * (cw + gap)
        s.line(centers[i], hl, centers[i], dv, t["rule"], 1.5)
        length = (hl - hb) + abs(centers[i] - centers[1]) + (dv - hl)
        s.path(f"M{centers[1]:.1f} {hb}V{hl}H{centers[i]:.1f}V{dv}", "none", t["second"], 3,
               extra=f'class="packet" stroke-dasharray="16 {length + 40:.0f}" '
                     f'style="--start:16;--end:-{length:.0f};--t:{i * 0.85:.2f}s"')
        s.rect(x, dv, cw, 66, t["panel"], t["ink"], 1.2)
        s.text(x + 12, dv + 28, name, 16, t["ink"], 600)
        s.text(x + 12, dv + 51, note, 14, t["grey"])
        s.add(f'<g font-family="{MONO}" font-size="17" font-weight="700" fill="{t["second"]}">')
        s.frames(4, 0.6 + i * 0.1,
                 lambda k, x=x: s.add(f'<text x="{x + cw - 22:.1f}" y="{dv + 29}">{esc(SPINNER[k])}</text>'))
        s.add("</g>")
    return dv + 66


def campus(t):
    r = core_repo()
    pin = DATA.get("pin") or {}
    items = [(pin.get(k), lab) for k, lab in (("java", "Java classes"), ("svelte", "UI components"),
                                              ("tests", "test files"), ("migrations", "migrations"),
                                              ("versions", "versions"))]
    items = [(v, lab) for v, lab in items if v] + [(r.get("release") or "—", "release")]
    if MOBILE:
        text_end = 158 + 18 * 1.5 * len(wrap(CAMPUS_TEXT, 18, X1 - X0))
        top = text_end + 18
        rule = top + 204 + 30
        fig_y = rule + 58
        rows = (len(items) + 2) // 3
        end = fig_y + (rows - 1) * 86 + 48
        H = end + 74
    else:
        top, rule, fig_y, end, H = 88, 334, 394, 444, 492
    s = page(t, H, "01 Campus, my core project: a site and an app for one study group that lives on the group "
             "leader's own computer. " + ", ".join(f"{v} {lab}" for v, lab in items) + ".",
             "How it works: the host computer runs the server with SQLite and encrypted files; a free HTTPS "
             "tunnel gives the group a link; every phone and laptop keeps its own copy and works offline. "
             "Sync packets run from the host to each device, where an ASCII spinner turns.")
    head(s, t, "01", "Core project", "github.com/mitaro-cs/Campus")
    if MOBILE:
        headline(s, X0 - 3, 120, "Campus", 72, t["ink"], -2, 0.1)
        para(s, X0, 158, CAMPUS_TEXT, 18, t["ink"], X1 - X0, 1.5, delay=0.4)
        diagram(s, t, X0, X1 - X0, top)
    else:
        headline(s, X0 - 3, 134, "Campus", 80, t["ink"], -2.5, 0.1)
        para(s, X0, 180, CAMPUS_TEXT, 18, t["ink"], 392, 1.5, delay=0.4)
        diagram(s, t, 476, X1 - 476, top)
    s.line(X0, rule, X1, rule, t["rule"], 1.2)
    figures(s, t, fig_y, items, accent_last=True, delay=0.3, cols=3 if MOBILE else None)
    s.line(X0, end, X1, end, t["rule"], 1.2)
    caps(s, X0, end + 26, f"{r['commits']} commits · AGPL-3.0", t["grey"])
    if MOBILE:
        caps(s, X0, end + 50, "Windows · macOS · iPhone · Android", t["grey"])
    else:
        caps(s, X1, end + 26, "Windows · macOS · iPhone · Android", t["grey"], "end")
    return s


# ------------------------------------------------------------------ 02 Rhythm
def sector(cx, cy, r0, r1, a0, a1):
    """Path of a ring sector between radii r0..r1 and angles a0..a1 (degrees, 0 at the top, clockwise)."""
    def pt(r, a):
        rad = math.radians(a - 90)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pt(r0, a0), pt(r1, a0), pt(r1, a1), pt(r0, a1)
    return (f"M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}A{r1} {r1} 0 0 1 {x2:.1f} {y2:.1f}"
            f"L{x3:.1f} {y3:.1f}A{r0} {r0} 0 0 0 {x0:.1f} {y0:.1f}Z")


def dial(s, t, f, cx, cy, caption_x, caption_y, r0=44, r1=126):
    """Commits by hour on a 24-hour dial, night hours in the second colour, a radar hand sweeping round."""
    caps(s, caption_x, caption_y, "Commits by hour", t["grey"])
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r1 + 4}" fill="none" stroke="{t["rule"]}" stroke-width="1.2"/>')
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r0 - 6}" fill="none" stroke="{t["rule"]}" stroke-width="1.2"/>')
    top = max(f["hours"]) or 1
    for h, n in enumerate(f["hours"]):
        a0, a1 = h * 15 + 1.5, h * 15 + 13.5
        if n:
            s.path(sector(cx, cy, r0, max(r0 + (r1 - r0) * n / top, r0 + 2), a0, a1),
                   t["second"] if h in NIGHT_HOURS else t["accent"],
                   extra=f'class="grow" style="transform-origin:{cx}px {cy}px;--t:{0.3 + h * 0.03:.2f}s"')
        else:
            s.path(sector(cx, cy, r0, r0 + 2, a0, a1), t["rule"])
    for h in (0, 6, 12, 18):
        rad = math.radians(h * 15 - 90)
        s.text(cx + (r1 + 20) * math.cos(rad), cy + (r1 + 20) * math.sin(rad) + 5, f"{h:02d}", 13, t["grey"],
               600, "middle")
    s.text(cx, cy, f"{f['peak']:02d}:00", 17, t["ink"], 700, "middle")
    s.text(cx, cy + 17, "peak", 12, t["grey"], anchor="middle")
    gid = s.uid("sw")
    s.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["second"]}" '
                  f'stop-opacity="0"/><stop offset="1" stop-color="{t["second"]}" stop-opacity=".25"/></linearGradient>')
    s.add(f'<g class="sweep" style="transform-origin:{cx}px {cy}px">'
          f'<path d="{sector(cx, cy, r0 - 6, r1 + 4, -40, 0)}" fill="url(#{gid})"/>'
          f'<line x1="{cx}" y1="{cy - r0 + 6}" x2="{cx}" y2="{cy - r1 - 4}" stroke="{t["second"]}" stroke-width="2"/>'
          "</g>")


def rhythm(t):
    f = facts()
    today = dt.datetime.now(MSK).date()
    weeks = 26
    start = today - dt.timedelta(days=today.weekday() + 7 * (weeks - 1))
    shown = {d: n for d, n in f["per_day"].items() if d >= start}
    size = 12.5 if MOBILE else 14
    hour_cmd = (["git log --date=format:%H --format=%ad \\", "  | sort | uniq -c | sort -rn | head -1"] if MOBILE
                else ["git log --date=format:%H --format=%ad | sort | uniq -c | sort -rn | head -1"])
    commands = [(["git log --since='26 weeks' --oneline | wc -l"], f"{sum(shown.values())}"),
                (hour_cmd, f"{f['hours'][f['peak']]:>4} {f['peak']:02d}")]
    term_h = 30 + sum(22 * len(c) + 28 for c, _ in commands) + 26
    if MOBILE:
        table_y, dial_cy, f_y = 270, 606, 806
    else:
        table_y, dial_cy, f_y = 300, 236, 476
    ty = f_y + 128
    H = ty + term_h + 24
    s = page(t, H, f"02 Rhythm: {f['night']}% of my commits land after 22:00 Moscow time. Peak hour "
             f"{f['peak']:02d}:00, longest streak {f['streak']} days, busiest day {f['weekday']}.",
             "A 24-hour dial of commits by hour with a sweeping hand, a strip of commits per day over the last "
             "26 weeks, and two git commands that type themselves out with their real answers.")
    head(s, t, "02", "Rhythm", "Moscow time · last 26 weeks")
    tw = X1 - X0 if MOBILE else 360
    headline(s, X0 - 6, 166 if MOBILE else 184, f"{f['night']}%", 112 if MOBILE else 124, t["second"], -5, 0.1)
    para(s, X0, 210 if MOBILE else 232, "of my commits land after 22:00.", 21, t["ink"], tw, 1.4, 700, delay=0.5)
    rows = [("Peak hour", f"{f['peak']:02d}:00"), ("Longest streak", f"{f['streak']} days"),
            ("Busiest day", f["weekday"]), ("Active days", str(len(f["per_day"])))]
    for i, (a, b) in enumerate(rows):
        y = table_y + i * 38
        s.line(X0, y - 24, X0 + tw, y - 24, t["rule"], 1.2)
        s.g("fade", f"--t:{0.7 + i * 0.1:.2f}s")
        s.text(X0, y, a, 16, t["grey"])
        s.text(X0 + tw, y, b, 16, t["ink"], 700, "end")
        s.end()
    s.line(X0, table_y + len(rows) * 38 - 24, X0 + tw, table_y + len(rows) * 38 - 24, t["rule"], 1.2)
    if MOBILE:
        dial(s, t, f, W / 2, dial_cy, X0, dial_cy - 166)
    else:
        dial(s, t, f, 680, dial_cy, 476, 96)

    caps(s, X0, f_y - 16, "Commits per day", t["grey"])
    gap = 4
    cell = (X1 - X0 - gap * (weeks - 1)) / weeks
    peak_day = max(shown, key=shown.get) if shown else None
    for w in range(weeks):
        s.g("fade", f"--t:{0.4 + w * 0.035:.2f}s")
        for d in range(7):
            day = start + dt.timedelta(days=7 * w + d)
            if day > today:
                continue
            n = f["per_day"].get(day, 0)
            x, y = X0 + w * (cell + gap), f_y + d * 11
            if day == peak_day:
                s.rect(x, y, cell, 8, t["second"])
            elif n:
                s.rect(x, y, cell, 8, t["accent"], opacity=(0.35, 0.6, 0.8, 1)[(n >= 3) + (n >= 6) + (n >= 10)])
            else:
                s.rect(x, y, cell, 8, t["rule"])
        s.end()
    if peak_day:
        caps(s, X1, f_y - 16, f"busiest: {shown[peak_day]} on {peak_day.day} {MONTHS[peak_day.month - 1]}",
             t["second"], "end")
    caps(s, X0, f_y + 98, MONTHS[start.month - 1], t["grey"], size=11.5)
    caps(s, X1, f_y + 98, MONTHS[today.month - 1], t["grey"], "end", size=11.5)

    # a terminal: two real questions, typed out, with their answers
    s.rect(X0, ty, X1 - X0, term_h, t["panel"], rx=6)
    y, delay = ty + 30, 1.0
    for cmd, answer in commands:
        for k, ln in enumerate(cmd):
            prompt = "$ " if k == 0 else "  "
            delay = mono_text(s, X0 + 16, y, [(prompt, t["second"]), (ln, t["ink"])], size, delay, mask=t["panel"])
            y += 22
        s.g("fade", f"--t:{delay + 0.25:.2f}s")
        mono_text(s, X0 + 16, y, [(answer, t["accent"])], size)
        s.end()
        y += 28
        delay += 0.6
    mono_text(s, X0 + 16, y, [("$ ", t["second"])], size)
    s.rect(X0 + 16 + mono_width(size, "$ "), y - size + 2, size * MONO_EM, size, t["ink"], extra='class="blink"')
    return s


# ------------------------------------------------------------------ 03 Toolkit
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
    s = page(t, H, "03 Toolkit. Code by language: " + ", ".join(f"{k} {round(100 * v / total)}%" for k, v in langs)
             + ". " + " ".join(f"{a}: {', '.join(b)}." for a, b in TOOLKIT),
             "Language shares drawn as ASCII bars of block glyphs that fill in, then what I use.")
    head(s, t, "03", "Toolkit", f"{code_size()} of code in {len(CODE_REPOS)} repositories")
    # ASCII bars: a full block for the share, a light shade for the rest; each line fills left to right
    for i, (k, v) in enumerate(langs):
        n = round(cells * v / total)
        pct = f"{round(100 * v / total):>3}%"
        parts = [(f"{k:<11} ", t["ink"]), ("█" * n, t["accent"] if i == 0 else t["ink"]),
                 ("░" * (cells - n), t["rule"]), (f" {pct}", t["grey"])]
        mono_text(s, X0, 92 + i * step, parts, size, delay=0.2 + i * 0.25, steps_per_s=50)
    s.line(X0, y0, X1, y0, t["rule"], 1.2)
    if MOBILE:
        y = y0 + 34
        for i, ((title, _), lines) in enumerate(zip(TOOLKIT, blocks)):
            caps(s, X0, y, title, t["grey"])
            s.g("fade", f"--t:{0.6 + i * 0.15:.2f}s")
            for j, ln in enumerate(lines):
                s.text(X0, y + 30 + j * 26, ln, 17, t["ink"])
            s.end()
            y += 40 + 26 * len(lines) + 14
        return s
    cw = (X1 - X0) / len(TOOLKIT)
    for i, (title, items) in enumerate(TOOLKIT):
        x = X0 + i * cw + (16 if i else 0)
        caps(s, x, y0 + 34, title, t["grey"])
        for j, item in enumerate(items):
            s.g("fade", f"--t:{0.6 + i * 0.15 + j * 0.06:.2f}s")
            s.text(x, y0 + 68 + j * 27, item, 17, t["ink"])
            s.end()
        if i:
            s.line(X0 + i * cw, y0 + 18, X0 + i * cw, H - 22, t["rule"], 1.2)
    return s


if __name__ == "__main__":
    both(cover, "cover")
    both(campus, "campus")
    both(rhythm, "rhythm")
    both(toolkit, "toolkit")
