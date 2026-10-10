#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Concept: an editorial profile in the colours of the avatar where every page has its own character and the real
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
# the avatar: a man on a park bench in a pale blue shirt, khaki trousers and suede boots, the trees and
# bark behind. Every text colour keeps 4.5:1 contrast or more on its background.
THEMES = {
    "light": dict(bg="#f2ede5", ink="#1d1a17", grey="#5e554d", rule="#ddd3c6", panel="#e8e1d6",
                  accent="#3d6680",   # the shirt
                  second="#b0603a",   # sunlit skin
                  khaki="#8a7350",    # the trousers
                  suede="#7d5538",    # the boots
                  leaf="#4f6e40",     # the trees
                  bark="#6f665b"),    # the bench and the bark
    "dark": dict(bg="#151413", ink="#f0eee9", grey="#c2b8ab", rule="#2f2b28", panel="#1f1d1b",
                 accent="#a9c4d4", second="#e8a882", khaki="#d6c6a6", suede="#c9976f", leaf="#9fbb88",
                 bark="#ada294"),
}
PALETTE = ["leaf", "bark", "suede", "second", "khaki", "accent"]   # the avatar, trees to shirt
LANG_TOKEN = {"Java": "accent", "Svelte": "suede", "Python": "khaki", "TypeScript": "leaf", "JavaScript": "bark",
              "CSS": "second", "HTML": "grey", "Other": "grey"}
DAY_PARTS = [("morning", range(4, 12), "khaki"), ("day", range(12, 18), "accent"), ("evening", range(18, 22), "second"),
             ("night", NIGHT_HOURS, "leaf")]


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


SUN_ROWS = ["khaki", "khaki", "khaki", "second", "second", "second", "suede", "suede", "suede", "bark", "bark",
            "leaf"]
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
    s.line(cx - cols_w / 2, horizon, cx + cols_w / 2, horizon, t["khaki"], 1.5)

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
            s.add(f'<text x="{start + k * width:.1f}" y="{y:.1f}" fill="{t["accent"]}" '
                  f'fill-opacity="{0.85 - r * 0.1:.2f}">{WAVES}</text>')
        s.end()

    def glitter(i):
        for r in range(5):
            y = horizon + (r + 1) * lh
            n = max(2, int((radius * 1.6 - r * 18) / cw))
            pattern = "".join("=-" [(k + i + r) % 2] if (k * 7 + i * 3 + r) % 5 else " " for k in range(n))
            s.add(f'<text x="{cx - n * cw / 2:.1f}" y="{y:.1f}" fill="{t[("khaki", "second", "second", "suede", "bark")[r]]}"'
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
    return dict(THEMES["dark"], bg="#1b1917", panel="#25221f", rule="#38332e")


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
        headline(s, X0 - 3, 120, "Campus", 72, t["ink"], -2, 0.1, glint=t["khaki"])
        para(s, X0, 158, CAMPUS_TEXT, 18, t["ink"], X1 - X0, 1.5, delay=0.4)
    else:
        headline(s, X0 - 3, 134, "Campus", 80, t["ink"], -2.5, 0.1, glint=t["khaki"])
        para(s, X0, 180, CAMPUS_TEXT, 18, t["ink"], 410, 1.5, delay=0.4)

    # the diagram, then packets riding its lines from the host to every device
    s.add(f'<g font-family="{MONO}" font-size="{size}" style="white-space:pre">')
    for k, ln in enumerate(rows):
        fill = t["khaki"] if k in (1,) else t["bark"] if k in (7, 8) else t["grey"]
        if k == 4:
            s.add(f'<text x="{dx:.1f}" y="{dy + k * lh:.1f}" xml:space="preserve"><tspan fill="{t["grey"]}">'
                  f'{esc(ln[:17])}</tspan><tspan fill="{t["leaf"]}">{esc(ln[17:])}</tspan></text>')
        else:
            s.add(f'<text x="{dx:.1f}" y="{dy + k * lh:.1f}" fill="{fill}" xml:space="preserve">{esc(ln)}</text>')
    s.add("</g>")

    def at(col, row):
        return dx + (col + 0.5) * cw, dy + row * lh - size * 0.33

    for i, c in enumerate(centres):
        (x0, y0), (_, y1), (x2, _), (_, y3) = at(16, 3), at(16, 5), at(c, 5), at(c, 6)
        route = f"M{x0:.1f} {y0:.1f}V{y1:.1f}H{x2:.1f}V{y3:.1f}"
        length = (y1 - y0) + abs(x2 - x0) + (y3 - y1)
        tone = t[("accent", "suede", "khaki")[i]]
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
                          [(graph, t["suede"]), (stamp, t["grey"]), (msg, t["ink"])],
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
def weekday_bars(s, t, f, x, y, width, size):
    """Commits by weekday as ASCII bars that type themselves out; the busiest day in the accent."""
    caps(s, x, y - 26, "Commits by weekday", t["grey"])
    cells = int(width / (size * MONO_EM)) - 9
    top = max(f["by_wd"]) or 1
    best = max(range(7), key=lambda d: f["by_wd"][d])
    for d, name in enumerate(WEEKDAYS):
        n = f["by_wd"][d]
        k = round(cells * n / top)
        parts = [(f"{name[:3]} ", t["ink"] if d == best else t["grey"]),
                 ("█" * k, t["accent"] if d == best else t["bark"]), ("░" * (cells - k), t["rule"]),
                 (f" {n:>3}", t["ink"] if d == best else t["grey"])]
        mono_text(s, x, y + d * (size + 12), parts, size, delay=0.5 + d * 0.18, steps_per_s=60)
    return y + 7 * (size + 12)


def day_chart(s, t, f, top, height=150, period=12.0):
    """Twenty-four hours of commits under a sky that changes with the time of day. A cursor walks the day
    with the sun on it by day and the moon by night, and each hour's bar lights up as it passes."""
    caps(s, X0, top - 16, "A day of commits · Moscow time", t["grey"])
    bottom = top + height
    slot = (X1 - X0) / 24
    sky = s.uid("sky")
    stops = "".join(f'<stop offset="{(h + 0.5) / 24:.3f}" stop-color="{t[hour_token(h)]}"/>' for h in range(24))
    s.defs.append(f'<linearGradient id="{sky}">{stops}</linearGradient>')
    s.rect(X0, top, X1 - X0, height, f"url(#{sky})", opacity=0.13, rx=6)
    hours = f["hours"]
    peak = max(range(24), key=lambda h: hours[h]) if any(hours) else 0
    tall = max(hours) or 1
    for h, n in enumerate(hours):
        bh = max(2.0, (height - 34) * n / tall)
        x = X0 + h * slot + 3
        lit = f"--t:{h / 24 * period:.2f}s;animation:light {period}s linear infinite;animation-delay:{h / 24 * period:.2f}s"
        s.rect(x, bottom - bh, slot - 6, bh, t[hour_token(h)], rx=2, extra=f'class="hour" style="{lit}"')
    s.css["light"] = ("@keyframes light{0%,6%{opacity:1}14%,100%{opacity:.45}}"
                      "@media (prefers-reduced-motion:reduce){.hour{animation:none!important}}")
    s.line(X0, bottom, X1, bottom, t["ink"], 1.2)
    for h in range(0, 24, 3):
        s.text(X0 + h * slot + slot / 2, bottom + 18, f"{h:02d}", 12, t["grey"], anchor="middle")
    px = X0 + peak * slot + slot / 2
    peak_h = (height - 34) * hours[peak] / tall
    s.text(px, bottom - peak_h - 8, f"{hours[peak]} at {peak:02d}:00", 13, t["ink"], 700, "middle")
    # the late hours are bracketed at both ends of the day, since they wrap past midnight
    yb = top + 12
    for h0, h1 in ((22, 24), (0, 4)):
        xa, xb = X0 + h0 * slot + 2, X0 + h1 * slot - 2
        s.path(f"M{xa:.1f} {yb + 6}V{yb}H{xb:.1f}V{yb + 6}", "none", t["leaf"], 1.4)
    s.text(X0 + 4 * slot + 8, yb + 6, f"{f['night']}% after 22:00", 13, t["leaf"], 700)
    # the time cursor: a line walking the day, the sun on it by day and the moon by night
    cx = X0
    s.add(f'<g class="cursor" style="animation:walk {period}s linear infinite">')
    s.line(cx, top + 4, cx, bottom, t["ink"], 1, 0.35)
    s.add(f'<g style="animation:sunup {period}s linear infinite">'
          f'<circle cx="{cx}" cy="{top - 2}" r="7" fill="{t["second"]}"/>'
          + "".join(f'<line x1="{cx + math.cos(a) * 10:.1f}" y1="{top - 2 + math.sin(a) * 10:.1f}" '
                    f'x2="{cx + math.cos(a) * 13:.1f}" y2="{top - 2 + math.sin(a) * 13:.1f}" stroke="{t["second"]}" '
                    f'stroke-width="1.6" stroke-linecap="round"/>' for a in [k * math.pi / 4 for k in range(8)])
          + "</g>")
    moon = s.uid("mn")
    s.defs.append(f'<mask id="{moon}"><rect x="{cx - 10}" y="{top - 12}" width="20" height="20" fill="#fff"/>'
                  f'<circle cx="{cx + 3.5}" cy="{top - 4.5}" r="6.5" fill="#000"/></mask>')
    s.add(f'<g style="animation:moonup {period}s linear infinite;opacity:0">'
          f'<circle cx="{cx}" cy="{top - 2}" r="7" fill="{t["accent"]}" mask="url(#{moon})"/></g>')
    s.add("</g>")
    s.css["walk"] = (f"@keyframes walk{{from{{transform:translateX(0)}}to{{transform:translateX({X1 - X0:.0f}px)}}}}"
                     "@keyframes sunup{0%,24%{opacity:0}26%,74%{opacity:1}76%,100%{opacity:0}}"
                     "@keyframes moonup{0%,24%{opacity:1}26%,74%{opacity:0}76%,100%{opacity:1}}"
                     "@media (prefers-reduced-motion:reduce){.cursor{display:none}}")
    return bottom + 18


def rhythm(t):
    f = facts()
    size = 13 if MOBILE else 14
    if MOBILE:
        table_y, wd_x, wd_y, wd_w = 270, X0, 470, X1 - X0
        day_top = wd_y + 7 * (size + 12) + 50
    else:
        table_y, wd_x, wd_y, wd_w = 300, 476, 126, X1 - 476
        day_top = 476
    H = day_top + 150 + 52
    s = page(t, H, f"02 Rhythm: {f['night']}% of my commits land after 22:00 Moscow time. Peak hour "
             f"{f['peak']:02d}:00, longest streak {f['streak']} days, busiest day {f['weekday']}.",
             "Commits by weekday as ASCII bars, and a day of commits hour by hour under a sky that changes from "
             "night to morning, day and evening, with a cursor carrying the sun by day and the moon by night.")
    head(s, t, "02", "Rhythm", "Moscow time · all my commits")
    tw = X1 - X0 if MOBILE else 360
    headline(s, X0 - 6, 166 if MOBILE else 184, f"{f['night']}%", 112 if MOBILE else 124, t["leaf"], -5, 0.1,
             glint=t["accent"])
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
    weekday_bars(s, t, f, wd_x, wd_y, wd_w, size)
    day_chart(s, t, f, day_top)
    return s


# ------------------------------------------------------------------ 03 Map: repositories as a constellation
def sky_theme():
    return dict(THEMES["dark"], bg="#11110f", rule="#2c2925")


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
    s.path(line, "none", t["leaf"], 1.4, opacity=0.8,
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
