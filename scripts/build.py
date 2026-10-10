#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Concept: an editorial profile in sunset colours where every page has its own character and the real
data is always the object. The cover is a poster with an ASCII sun rising over an ASCII sea; Campus
is a dark terminal with its architecture in box-drawing characters and its git log typing itself
out; Rhythm is a data page with a 24-hour dial and a streamgraph; Map is a night sky where the
repositories are a constellation; Toolkit fills ASCII bars; Now types out what I am working on.
All motion is CSS and stops under prefers-reduced-motion; every element rests in its final state.
Each page is rendered for light and dark themes and as a single-column version for phones.
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

# the avatar's colours (a park bench, khaki trousers, a pale blue shirt, sunlit skin), tuned so every text
# colour keeps at least 4.5:1 contrast on its background
NIGHT_HOURS = (22, 23, 0, 1, 2, 3)
# a warm sunset: plum night, orange sun, coral, gold, magenta and violet sky; light theme on cream paper.
# Every text colour keeps 4.5:1 contrast or more on its background.
THEMES = {
    "light": dict(bg="#fff5ec", ink="#2a1430", grey="#6b5263", rule="#f0d9cb", panel="#fde6d6",
                  accent="#d4501a", second="#c8304a", gold="#9a6400", magenta="#b0307a", violet="#6a3fd0",
                  peach="#b8612f"),
    "dark": dict(bg="#170d1f", ink="#fff1e8", grey="#d4b9c6", rule="#36223f", panel="#22142c",
                 accent="#ff8a3d", second="#ff5e6c", gold="#ffc65c", magenta="#ff5fae", violet="#a98bff",
                 peach="#ffb38a"),
}
PALETTE = ["violet", "magenta", "second", "accent", "peach", "gold"]   # the sunset, sky to sun
LANG_TOKEN = {"Java": "accent", "Svelte": "magenta", "Python": "gold", "TypeScript": "violet", "JavaScript": "peach",
              "CSS": "second", "HTML": "grey", "Other": "grey"}
DAY_PARTS = [("morning", range(4, 12), "gold"), ("day", range(12, 18), "accent"), ("evening", range(18, 22), "magenta"),
             ("night", NIGHT_HOURS, "violet")]


def hour_token(h):
    return next(tok for _, hours, tok in DAY_PARTS if h in hours)


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


# ------------------------------------------------------------------ cover: a poster with an ASCII sunset
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
    caps(s, X0, y, "Latest", t["magenta"], weight=700)
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


SUN_ROWS = ["gold", "gold", "gold", "peach", "peach", "accent", "accent", "second", "second", "magenta", "magenta",
            "violet"]
WAVES = "~ ~~  ~   ~~~ ~  ~~ ~    ~ ~~~  ~ ~   ~~ ~ ~~~   ~  ~ ~~"


def ascii_sunset(s, t, cx, horizon, cols_w, size=12):
    """A striped ASCII sun rising over an ASCII sea: the waves drift, the reflection shimmers."""
    cw, lh = size * MONO_EM, size * 1.05
    rows = len(SUN_ROWS)
    radius = rows * lh
    cid = s.uid("sun")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{cx - cols_w / 2 - 10:.1f}" y="{horizon - radius - 30:.1f}" '
                  f'width="{cols_w + 20:.1f}" height="{radius + 30 - 2:.1f}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})" font-family="{MONO}" font-size="{size}" font-weight="700" style="white-space:pre">')
    s.g("lift", "--dy:70px;--t:.2s;animation-duration:3.2s")
    for r, tok in enumerate(SUN_ROWS):
        y = horizon - radius + (r + 0.8) * lh
        dy = horizon - y
        half = math.sqrt(max(0.0, radius * radius - dy * dy))
        n = int(half * 2 / cw)
        if r >= 7 and r % 2:          # the classic stripes cut into the lower half
            continue
        ch = "@" if r < 3 else "#" if r < 6 else "="
        s.add(f'<text x="{cx - n * cw / 2:.1f}" y="{y:.1f}" fill="{t[tok]}">{ch * n}</text>')
    s.end()
    s.add("</g>")
    s.line(cx - cols_w / 2, horizon, cx + cols_w / 2, horizon, t["gold"], 1.5)

    # the sea: rows of waves drifting at different speeds, and the sun's broken reflection
    sea = s.uid("sea")
    s.defs.append(f'<clipPath id="{sea}"><rect x="{cx - cols_w / 2:.1f}" y="{horizon + 2}" width="{cols_w:.1f}" '
                  f'height="{6 * lh + 6:.1f}"/></clipPath>')
    s.add(f'<g clip-path="url(#{sea})" font-family="{MONO}" font-size="{size}" style="white-space:pre">')
    width = mono_width(size, WAVES)
    for r in range(6):
        y = horizon + (r + 1) * lh
        shift = width if r % 2 else -width
        start = cx - cols_w / 2 - (width if r % 2 else 0)
        s.g("ticker", f"--shift:{shift:.0f}px;--d:{14 + r * 5}s")
        for k in range(3):
            s.add(f'<text x="{start + k * width:.1f}" y="{y:.1f}" fill="{t["violet"]}" '
                  f'fill-opacity="{0.85 - r * 0.1:.2f}">{WAVES}</text>')
        s.end()

    def glitter(i):
        for r in range(5):
            y = horizon + (r + 1) * lh
            n = max(2, int((radius * 1.6 - r * 18) / cw))
            pattern = "".join("=-" [(k + i + r) % 2] if (k * 7 + i * 3 + r) % 5 else " " for k in range(n))
            s.add(f'<text x="{cx - n * cw / 2:.1f}" y="{y:.1f}" fill="{t[("gold", "peach", "accent", "second", "magenta")[r]]}"'
                  f' font-weight="700">{pattern}</text>')

    s.frames(6, 1.2, glitter, blend=True)
    s.add("</g>")
    return horizon + 6 * lh


def cover(t):
    f = facts()
    repos = DATA["repos"]
    last = f["last"]
    deck = "I build local-first software: the data stays on a machine you control, not on someone else's server."
    if MOBILE:
        head_y, head_size, name_y, para_y, para_w = 150, 100, 202, 236, X1 - X0
        para_end = para_y + 18.5 * 1.45 * len(wrap(deck, 18.5, para_w))
        sun_cx, horizon, sun_w = W / 2, para_end + 170, X1 - X0
        y_rule = horizon + 6 * 12 * 1.05 + 30
    else:
        head_y, head_size, name_y, para_y, para_w = 184, 124, 240, 274, 420
        sun_cx, horizon, sun_w, y_rule = 680, 262, 336, 372
    fig_y = y_rule + 56
    fig_end = fig_y + (86 if MOBILE else 0) + 54
    H = fig_end + (52 if MOBILE else 80)
    s = page(t, H, "Mitaro. Omar, computer science student at MTUCI. I build local-first software: the data stays "
             "on a machine you control. Core project: Campus.",
             "A poster: an ASCII sun rising over an ASCII sea, the key figures and a ticker of my latest commits.")
    caps(s, X0, 42, "mitaro-cs" if MOBILE else "mitaro-cs · GitHub profile", t["grey"])
    if last:
        caps(s, X1, 42, f"last commit {last.day} {MONTHS[last.month - 1]} {last.year}", t["grey"], "end")
    seg = (X1 - X0) / len(PALETTE)
    for i, tok in enumerate(PALETTE):
        s.g("wide", f"--t:{i * 0.07:.2f}s")
        s.rect(X0 + i * seg, 53, seg, 4, t[tok])
        s.end()
    headline(s, X0 - 5, head_y, "Mitaro", head_size, t["ink"], -4, 0.15, glint=t["accent"])
    s.g("fade", "--t:.6s")
    s.text(X0, name_y, "Omar, CS student at MTUCI.", 21, t["ink"], 700)
    s.end()
    para(s, X0, para_y, deck, 18.5, t["grey"], para_w, 1.45, delay=0.75)
    ascii_sunset(s, t, sun_cx, horizon, sun_w)
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


SECTIONS = [("01", "Campus"), ("02", "Rhythm"), ("03", "Map"), ("04", "Toolkit"), ("05", "Now")]


# ------------------------------------------------------------------ 01 Campus: a dark terminal page
SPINNER = "|/-\\"
CAMPUS_TEXT = ("A site and an app for one study group: homework, a schedule from an .ics file, news and files. It "
               "lives on the group leader's own computer, and every phone keeps a copy that syncs when the host is "
               "back on.")


def box_diagram():
    """Campus's architecture in box-drawing characters; returns the lines and the device centre columns."""
    w = 34
    rows = ["┌" + "─" * (w - 2) + "┐",
            "│" + " HOST · group leader's computer".ljust(w - 2) + "│",
            "│" + " Spring Boot · SQLite · AES-GCM".ljust(w - 2) + "│",
            "└" + "─" * 15 + "┬" + "─" * (w - 18) + "┘",
            " " * 16 + "│  https tunnel",
            " " * 5 + "┌" + "─" * 10 + "┼" + "─" * 10 + "┐"]
    centres = [5, 16, 27]
    names = [("phone ", " copy "), ("phone ", "local "), ("laptop", "later ")]

    def line(parts):
        out = [" "] * w
        for col, txt in parts:
            for k, ch in enumerate(txt):
                out[col + k] = ch
        return "".join(out).rstrip()

    rows.append(line([(c - 3, "┌──┴───┐") for c in centres]))
    rows.append(line([(c - 3, f"│{n}│") for c, (n, _) in zip(centres, names)]))
    rows.append(line([(c - 3, f"│{m}│") for c, (_, m) in zip(centres, names)]))
    rows.append(line([(c - 3, "└──────┘") for c in centres]))
    return rows, centres


def terminal_theme():
    """The Campus page is a dark terminal in both themes, so it reads as its own place."""
    return dict(THEMES["dark"], bg="#1d1026", panel="#271532", rule="#3b2546")


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
    size = 12 if MOBILE else 14
    cw, lh = size * MONO_EM, size * 1.22
    rows, centres = box_diagram()
    if MOBILE:
        text_end = 158 + 18 * 1.5 * len(wrap(CAMPUS_TEXT, 18, X1 - X0))
        dx, dy = X0, text_end + 22
        log_y = dy + len(rows) * lh + 40
    else:
        dx, dy = 486, 100
        log_y = 372
    max_chars = int((X1 - X0) / (13 * MONO_EM)) - 2
    log_end = log_y + 26 + len(log) * 22
    rule = log_end + 18
    fig_y = rule + 58
    fig_rows = (len(items) + 2) // 3 if MOBILE else 1
    end = fig_y + (fig_rows - 1) * 86 + 48
    H = end + (74 if MOBILE else 48)
    s = page(t, H, "01 Campus, my core project: a site and an app for one study group that lives on the group "
             "leader's own computer. " + ", ".join(f"{v} {lab}" for v, lab in items) + ".",
             "A dark terminal page: the architecture drawn in box characters with sync packets running from the "
             "host to each device, and git log --graph of the latest Campus commits typing itself out.")
    head(s, t, "01", "Core project", "github.com/mitaro-cs/Campus")
    if MOBILE:
        headline(s, X0 - 3, 120, "Campus", 72, t["ink"], -2, 0.1, glint=t["gold"])
        para(s, X0, 158, CAMPUS_TEXT, 18, t["ink"], X1 - X0, 1.5, delay=0.4)
    else:
        headline(s, X0 - 3, 134, "Campus", 80, t["ink"], -2.5, 0.1, glint=t["gold"])
        para(s, X0, 180, CAMPUS_TEXT, 18, t["ink"], 410, 1.5, delay=0.4)

    # the diagram, then packets riding its lines from the host to every device
    s.add(f'<g font-family="{MONO}" font-size="{size}" style="white-space:pre">')
    for k, ln in enumerate(rows):
        fill = t["gold"] if k in (1,) else t["peach"] if k in (7, 8) else t["grey"]
        if k == 4:
            s.add(f'<text x="{dx:.1f}" y="{dy + k * lh:.1f}" xml:space="preserve"><tspan fill="{t["grey"]}">'
                  f'{esc(ln[:17])}</tspan><tspan fill="{t["violet"]}">{esc(ln[17:])}</tspan></text>')
        else:
            s.add(f'<text x="{dx:.1f}" y="{dy + k * lh:.1f}" fill="{fill}" xml:space="preserve">{esc(ln)}</text>')
    s.add("</g>")

    def at(col, row):
        return dx + (col + 0.5) * cw, dy + row * lh - size * 0.33

    for i, c in enumerate(centres):
        (x0, y0), (_, y1), (x2, _), (_, y3) = at(16, 3), at(16, 5), at(c, 5), at(c, 6)
        route = f"M{x0:.1f} {y0:.1f}V{y1:.1f}H{x2:.1f}V{y3:.1f}"
        length = (y1 - y0) + abs(x2 - x0) + (y3 - y1)
        tone = t[("accent", "magenta", "gold")[i]]
        s.path(route, "none", tone, 3, extra=f'class="packet" stroke-dasharray="12 {length + 30:.0f}" '
                                             f'style="--start:12;--end:-{length:.0f};--t:{i * 0.85:.2f}s"')
        sx, sy = at(c + 3, 8)
        s.add(f'<g font-family="{MONO}" font-size="{size}" font-weight="700" fill="{tone}">')
        s.frames(4, 0.6 + i * 0.1, lambda k, sx=sx, sy=sy: s.add(
            f'<text x="{sx - cw / 2:.1f}" y="{sy + size * 0.33:.1f}">{esc(SPINNER[k])}</text>'))
        s.add("</g>")
    hx, hy = at(16, 3)
    s.circle(hx, hy, 12, "none", extra=f'stroke="{t["accent"]}" stroke-width="1.5" opacity="0" class="ripple"')

    # git log --graph of the latest Campus commits, typed out line by line
    caps(s, X0, log_y, "$ git log --graph --oneline", t["grey"])
    delay = 1.2
    for k, c in enumerate(log):
        _, m, d = c["ts"][:10].split("-")
        graph = "* "
        msg = c["msg"]
        stamp = f"{int(d):>2} {MONTHS[int(m) - 1]}  "
        room = max_chars - len(graph) - len(stamp)
        msg = msg if len(msg) <= room else msg[:room - 1] + "…"
        delay = mono_text(s, X0, log_y + 26 + k * 22,
                          [(graph, t["magenta"]), (stamp, t["grey"]), (msg, t["ink"])],
                          13, delay, steps_per_s=90, mask=t["bg"]) + 0.08
    s.line(X0, rule, X1, rule, t["rule"], 1.2)
    figures(s, t, fig_y, items, accent_last=True, delay=0.3, cols=3 if MOBILE else None)
    s.line(X0, end, X1, end, t["rule"], 1.2)
    caps(s, X0, end + 26, f"{r['commits']} commits · AGPL-3.0", t["grey"])
    if MOBILE:
        caps(s, X0, end + 50, "Windows · macOS · iPhone · Android", t["grey"])
    else:
        caps(s, X1, end + 26, "Windows · macOS · iPhone · Android", t["grey"], "end")
    return s


# ------------------------------------------------------------------ 02 Rhythm: a data page
def sector(cx, cy, r0, r1, a0, a1):
    """Path of a ring sector between radii r0..r1 and angles a0..a1 (degrees, 0 at the top, clockwise)."""
    def pt(r, a):
        rad = math.radians(a - 90)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pt(r0, a0), pt(r1, a0), pt(r1, a1), pt(r0, a1)
    return (f"M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}A{r1} {r1} 0 0 1 {x2:.1f} {y2:.1f}"
            f"L{x3:.1f} {y3:.1f}A{r0} {r0} 0 0 0 {x0:.1f} {y0:.1f}Z")


def dial(s, t, f, cx, cy, caption_x, caption_y, r0=44, r1=126):
    """Commits by hour on a 24-hour dial coloured by part of the day, a radar hand sweeping round."""
    caps(s, caption_x, caption_y, "Commits by hour", t["grey"])
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r1 + 4}" fill="none" stroke="{t["rule"]}" stroke-width="1.2"/>')
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r0 - 6}" fill="none" stroke="{t["rule"]}" stroke-width="1.2"/>')
    top = max(f["hours"]) or 1
    for h, n in enumerate(f["hours"]):
        a0, a1 = h * 15 + 1.5, h * 15 + 13.5
        if n:
            s.path(sector(cx, cy, r0, max(r0 + (r1 - r0) * n / top, r0 + 2), a0, a1), t[hour_token(h)],
                   extra=f'class="grow" style="transform-origin:{cx}px {cy}px;--t:{0.3 + h * 0.03:.2f}s"')
        else:
            s.path(sector(cx, cy, r0, r0 + 2, a0, a1), t["rule"])
    for h in (0, 6, 12, 18):
        rad = math.radians(h * 15 - 90)
        s.text(cx + (r1 + 20) * math.cos(rad), cy + (r1 + 20) * math.sin(rad) + 5, f"{h:02d}", 13, t["grey"],
               600, "middle")
    s.text(cx, cy, f"{f['peak']:02d}:00", 17, t["ink"], 700, "middle")
    s.text(cx, cy + 17, "peak", 12, t["grey"], anchor="middle")
    lx = cx - 170
    for name, _, tok in DAY_PARTS:
        s.circle(lx + 5, cy + r1 + 50, 5, t[tok])
        s.text(lx + 16, cy + r1 + 55, name, 13.5, t["grey"])
        lx += 16 + text_width(13.5, name) + 22
    gid = s.uid("sw")
    s.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["second"]}" '
                  f'stop-opacity="0"/><stop offset="1" stop-color="{t["second"]}" stop-opacity=".25"/></linearGradient>')
    s.add(f'<g class="sweep" style="transform-origin:{cx}px {cy}px">'
          f'<path d="{sector(cx, cy, r0 - 6, r1 + 4, -40, 0)}" fill="url(#{gid})"/>'
          f'<line x1="{cx}" y1="{cy - r0 + 6}" x2="{cx}" y2="{cy - r1 - 4}" stroke="{t["second"]}" stroke-width="2"/>'
          "</g>")


def smooth_path(pts):
    """A smooth curve through the points (Catmull-Rom as cubic Béziers)."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


STREAM_TOKENS = ["accent", "magenta", "violet", "gold", "peach"]


def streamgraph(s, t, top, height, days=42):
    """Commits per day over the last six weeks, by repository, as a streamgraph revealed left to right."""
    today = dt.datetime.now(MSK).date()
    start = today - dt.timedelta(days=days - 1)
    per = {}
    for c in DATA["commits"]:
        d = dt.datetime.fromisoformat(c["ts"].replace("Z", "+00:00")).astimezone(MSK).date()
        if d >= start:
            name = REPO_NAMES.get(c["repo"].lower(), c["repo"])
            per.setdefault(name, [0] * days)[(d - start).days] += 1
    ranked = sorted(per.items(), key=lambda kv: -sum(kv[1]))
    layers = ranked[:4]
    if len(ranked) > 4:
        layers.append(("other", [sum(v[i] for _, v in ranked[4:]) for i in range(days)]))
    caps(s, X0, top - 16, "Commits per day, last six weeks, by repository", t["grey"])
    if not layers:
        return top + height
    # a gentle blur over neighbouring days, so the streams flow
    kernel = (1, 2, 3, 2, 1)
    soft = [(n, [sum(kernel[j] * v[min(days - 1, max(0, i + j - 2))] for j in range(5)) / 9 for i in range(days)])
            for n, v in layers]
    totals = [sum(v[i] for _, v in soft) for i in range(days)]
    k = (height - 10) / (max(totals) or 1)
    xs = [X0 + (X1 - X0) * i / (days - 1) for i in range(days)]
    mid = top + height / 2
    base = [mid - totals[i] * k / 2 for i in range(days)]
    labels = []
    for li, (name, vals) in enumerate(soft):
        upper = [(xs[i], base[i]) for i in range(days)]
        lower = [(xs[i], base[i] + vals[i] * k) for i in range(days)]
        s.path(smooth_path(upper) + "L" + smooth_path(lower[::-1])[1:] + "Z", t[STREAM_TOKENS[li % len(STREAM_TOKENS)]],
               opacity=0.94)
        best = max(range(days), key=lambda i: vals[i])
        labels.append((name, xs[best], base[best] + vals[best] * k / 2, vals[best] * k, li))
        base = [base[i] + vals[i] * k for i in range(days)]
    for name, x, y, thick, li in labels:
        if thick >= 16:
            anchor = "end" if x > X1 - 60 else "start" if x < X0 + 60 else "middle"
            s.text(x, y + 4.5, name, 12.5, t["bg"], 700, anchor)
    legend_x, legend_y = X0, top + height + 18
    for li, (name, _) in enumerate(soft):
        name = name if len(name) <= 14 else name[:13] + "…"
        step = 16 + text_width(13, name) + 18
        if legend_x + step - 18 > (X1 if MOBILE else X1 - 170):
            legend_x, legend_y = X0, legend_y + 22
        s.circle(legend_x + 5, legend_y, 5, t[STREAM_TOKENS[li % len(STREAM_TOKENS)]])
        s.text(legend_x + 16, legend_y + 5, name, 13, t["grey"])
        legend_x += step
    s.rect(X1 + 2, top - 4, X1 - X0 + 8, height + 8, t["bg"],
           extra=f'class="type" style="--dx:-{X1 - X0 + 6}px;--t:.6s;--d:2.4s;'
                 f'animation-timing-function:cubic-bezier(.4,0,.2,1)"')
    if not MOBILE:
        caps(s, X1, top + height + 22, f"{start.day} {MONTHS[start.month - 1]} — {today.day} {MONTHS[today.month - 1]}",
             t["grey"], "end", size=11.5)
    return top + height + 22


def rhythm(t):
    f = facts()
    if MOBILE:
        table_y, dial_cy, st_top = 270, 606, 840
    else:
        table_y, dial_cy, st_top = 300, 236, 500
    st_h = 130 if MOBILE else 160
    H = st_top + st_h + (80 if MOBILE else 56)
    s = page(t, H, f"02 Rhythm: {f['night']}% of my commits land after 22:00 Moscow time. Peak hour "
             f"{f['peak']:02d}:00, longest streak {f['streak']} days, busiest day {f['weekday']}.",
             "A 24-hour dial of commits by hour coloured by morning, day, evening and night with a sweeping hand, "
             "and a streamgraph of commits per week by repository over the last 26 weeks.")
    head(s, t, "02", "Rhythm", "Moscow time · last 26 weeks")
    tw = X1 - X0 if MOBILE else 360
    headline(s, X0 - 6, 166 if MOBILE else 184, f"{f['night']}%", 112 if MOBILE else 124, t["violet"], -5, 0.1,
             glint=t["magenta"])
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
    streamgraph(s, t, st_top, st_h)
    return s


# ------------------------------------------------------------------ 03 Map: repositories as a constellation
def sky_theme():
    return dict(THEMES["dark"], bg="#120a1a", rule="#2e1d38")


def star_map(_t):
    t = sky_theme()
    BG_HOLDER[0] = t["bg"]
    repos = sorted(DATA["repos"], key=lambda r: r["created"])
    H = 470 if MOBILE else 430
    s = page(t, H, "03 Map: my repositories as a constellation, in the order I made them; the higher and larger "
             "the star, the more commits. " + ", ".join(f"{REPO_NAMES.get(r['name'].lower(), r['name'])} "
                                                       f"{r['commits']}" for r in repos) + ".",
             "Stars twinkle and a line draws itself through them from the first repository to the newest.")
    rnd = random.Random(42)
    for _ in range(90 if MOBILE else 160):
        s.circle(rnd.uniform(0, W), rnd.uniform(56, H - 40), rnd.choice((0.6, 0.8, 1.1)), t["grey"],
                 round(rnd.uniform(0.15, 0.6), 2))
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
    s.path(line, "none", t["violet"], 1.4, opacity=0.8,
           extra=f'class="draw" stroke-dasharray="{length:.0f}" style="--len:{length:.0f};--t:.4s"')
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
    s.line(X0, y0, X1, y0, t["rule"], 1.2)
    if MOBILE:
        y = y0 + 34
        for i, ((title, _), lines) in enumerate(zip(TOOLKIT, blocks)):
            caps(s, X0, y, title, t[("accent", "magenta", "violet")[i]], weight=700)
            s.g("fade", f"--t:{0.6 + i * 0.15:.2f}s")
            for j, ln in enumerate(lines):
                s.text(X0, y + 30 + j * 26, ln, 17, t["ink"])
            s.end()
            y += 40 + 26 * len(lines) + 14
        return s
    cw = (X1 - X0) / len(TOOLKIT)
    for i, (title, items) in enumerate(TOOLKIT):
        x = X0 + i * cw + (16 if i else 0)
        caps(s, x, y0 + 34, title, t[("accent", "magenta", "violet")[i]], weight=700)
        for j, item in enumerate(items):
            s.g("fade", f"--t:{0.6 + i * 0.15 + j * 0.06:.2f}s")
            s.text(x, y0 + 68 + j * 27, item, 17, t["ink"])
            s.end()
        if i:
            s.line(X0 + i * cw, y0 + 18, X0 + i * cw, H - 22, t["rule"], 1.2)
    return s


# ------------------------------------------------------------------ 05 Now
NOW = [("building", "accent", "Java and Flask backends with a cleaner structure"),
       ("studying", "magenta", "security: encryption, hashing, local-first design"),
       ("prototype", "violet", "a personal AI assistant, Jarvis-style"),
       ("student", "gold", "computer science at MTUCI")]


def now(t):
    size = 13 if MOBILE else 15
    cw = size * MONO_EM
    tag_w = 12
    room = int((X1 - X0 - 36) / cw) - tag_w
    lines = []
    for tag, tok, txt in NOW:
        parts = [txt] if len(txt) <= room else wrap_mono(txt, room)
        lines.append((tag, tok, parts))
    rows = 1 + sum(len(p) for _, _, p in lines) + 1
    box_top = 66
    H = box_top + 30 + rows * (size + 11) + 30
    s = page(t, H, "05 Now: " + "; ".join(f"{tag} {txt}" for tag, _, txt in NOW) + ".",
             "A terminal that types out what I am working on now, with a spinner on the current build.")
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
    both(rhythm, "rhythm")
    both(star_map, "map")
    both(toolkit, "toolkit")
    both(now, "now")
