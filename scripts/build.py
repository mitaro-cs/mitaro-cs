#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Concept: the profile as an editorial spread. No pictures: big type, a strict grid, hairline rules,
one accent colour, and on every page the real data is the object (the Campus architecture, its
numbers, when I commit, what I write in). The motion is part of the data: headlines lift out of
their rules, numbers roll into place like a split-flap board, sync packets run through the Campus
diagram, a radar sweeps a 24-hour dial, and the cover carries a ticker of my latest real commits.
Every page is rendered twice, -light.svg and -dark.svg, and the README picks one with <picture>.
"""
import datetime as dt
import json
import math
import os
import sys

from lib import Svg, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
W, X0, X1 = 888, 40, 848

THEMES = {
    "light": dict(bg="#f5f3ef", ink="#141414", grey="#6f6b64", rule="#d6d2ca", accent="#d9431f"),
    "dark": dict(bg="#121212", ink="#efece6", grey="#9a968e", rule="#2f2e2b", accent="#ff6a47"),
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


# ------------------------------------------------------------------ type, rules and motion
def page(t, h, title, desc=""):
    s = Svg(W, h, title, desc)
    s.rect(0, 0, W, h, t["bg"])
    return s


def caps(s, x, y, txt, fill, anchor="start", size=11, weight=600):
    s.text(x, y, txt.upper(), size, fill, weight, anchor, ls=1.6)


def head(s, t, num, label, right=""):
    """Section line: number in the accent, label in caps, a hairline that draws itself, a note on the right."""
    caps(s, X0, 40, num, t["accent"], size=12, weight=700)
    caps(s, X0 + 30, 40, label, t["ink"], size=12, weight=700)
    start = X0 + 30 + text_width(12, label.upper(), 700, 1.6) + 14
    end = X1 - (text_width(11, right.upper(), 600, 1.6) + 14 if right else 0)
    s.g("wide", "--t:.1s")
    s.line(start, 36, end, 36, t["rule"], 1)
    s.end()
    if right:
        caps(s, X1, 40, right, t["grey"], "end")


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
    value = str(value)
    lh = size * 1.15
    dw = size * 0.62
    for i, ch in enumerate(value):
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
    return x


def figures(s, t, y, items, accent_last=False, delay=0.2):
    """A row of big numbers with small labels, split by hairlines; numbers roll in."""
    cw = (X1 - X0) / len(items)
    for i, (v, lab) in enumerate(items):
        x = X0 + i * cw + (16 if i else 0)
        fill = t["accent"] if accent_last and i == len(items) - 1 else t["ink"]
        if any(c.isdigit() for c in str(v)):
            odometer(s, x, y, v, 34, fill, delay + i * 0.15)
        else:
            s.g("fade", f"--t:{delay + i * 0.15 + 0.6:.2f}s")
            s.text(x, y, str(v), 34, fill, 700, ls=-0.8)
            s.end()
        s.text(x, y + 22, lab, 12.5, t["grey"])
        if i:
            s.line(X0 + i * cw, y - 32, X0 + i * cw, y + 26, t["rule"], 1)


def para(s, x, y, txt, size, fill, maxw, lead=1.45, weight=400, delay=0.0):
    s.g("fade", f"--t:{delay}s")
    for ln in wrap(txt, size, maxw, weight):
        s.text(x, y, ln, size, fill, weight)
        y += size * lead
    s.end()
    return y


def both(fn, name):
    for theme, t in THEMES.items():
        fn(t).save(OUT, f"{name}-{theme}.svg")


# ------------------------------------------------------------------ cover
def ticker(s, t, y):
    """A band with my latest real commits running right to left."""
    rows = [c for c in DATA["commits"] if not c["msg"].startswith(("Initial commit", "Merge "))][:8]
    items = []
    for c in rows:
        _, m, d = c["ts"][:10].split("-")
        items.append(f"{c['msg']}  —  {REPO_NAMES.get(c['repo'].lower(), c['repo'])}, {int(d)} {MONTHS[int(m) - 1]}")
    line = "     ·     ".join(items) + "     ·     "
    width = text_width(12.5, line)
    lx = X0 + 76
    caps(s, X0, y, "Latest", t["accent"], weight=700)
    cid = s.uid("tk")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{lx}" y="{y - 16}" width="{X1 - lx}" height="24"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.g("ticker", f"--shift:-{width:.0f}px;--d:{width / 45:.0f}s")
    for k in range(2):
        s.add(f'<text x="{lx + k * width:.1f}" y="{y}" font-size="12.5" fill="{t["ink"]}" xml:space="preserve">'
              f'{line.replace("&", "&amp;").replace("<", "&lt;")}</text>')
    s.end()
    s.add("</g>")
    s.rect(X1 - 30, y - 16, 30, 24, s_gradient_fade(s, t))


def s_gradient_fade(s, t):
    gid = s.uid("fd")
    s.defs.append(f'<linearGradient id="{gid}"><stop offset="0" stop-color="{t["bg"]}" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="{t["bg"]}"/></linearGradient>')
    return f"url(#{gid})"


def cover(t):
    H = 396
    f = facts()
    repos = DATA["repos"]
    last = f["last"]
    s = page(t, H, "Mitaro. Omar, computer science student at MTUCI. I build local-first software: the data stays "
             "on a machine you control. Core project: Campus.")
    caps(s, X0, 40, "mitaro-cs · GitHub profile", t["grey"])
    if last:
        caps(s, X1, 40, f"last commit {last.day} {MONTHS[last.month - 1]} {last.year}", t["grey"], "end")
    s.g("wide")
    s.line(X0, 52, X1, 52, t["ink"], 1.5)
    s.end()
    headline(s, X0 - 6, 178, "Mitaro", 124, t["ink"], -5, 0.15)
    s.g("fade", "--t:.6s")
    s.text(476, 106, "Omar, CS student at MTUCI.", 18, t["ink"], 600)
    s.end()
    para(s, 476, 134, "I build local-first software: the data stays on a machine you control, not on someone "
         "else's server.", 17, t["grey"], X1 - 476, 1.42, delay=0.75)
    s.line(X0, 214, X1, 214, t["rule"], 1)
    figures(s, t, 270, [(sum(r["commits"] for r in repos), "commits"), (len(repos), "public repositories"),
                        (code_size(), "of code"), ("Campus", "core project")], accent_last=True, delay=0.5)
    s.line(X0, 324, X1, 324, t["ink"], 1.5)
    caps(s, X0, 346, "Contents", t["grey"])
    x = X0 + 100
    for num, name in (("01", "Campus"), ("02", "Rhythm"), ("03", "Toolkit")):
        caps(s, x, 346, num, t["accent"], weight=700)
        caps(s, x + 24, 346, name, t["ink"], weight=700)
        x += 24 + text_width(11, name.upper(), 700, 1.6) + 28
    caps(s, X1, 346, f"online since {DATA['created'][:4]}", t["grey"], "end")
    s.line(X0, 360, X1, 360, t["rule"], 1)
    ticker(s, t, 382)
    return s


# ------------------------------------------------------------------ 01 Campus
def campus(t):
    H = 470
    r = core_repo()
    pin = DATA.get("pin") or {}
    items = [(pin.get(k), lab) for k, lab in (("java", "Java classes"), ("svelte", "Svelte components"),
                                              ("tests", "test files"), ("migrations", "DB migrations"),
                                              ("versions", "versions"))]
    items = [(v, lab) for v, lab in items if v] + [(r.get("release") or "—", "latest release")]
    s = page(t, H, "01 Campus, my core project: a site and an app for one study group that lives on the group "
             "leader's own computer. " + ", ".join(f"{v} {lab}" for v, lab in items) + ".",
             "How it works: the host computer runs the server with SQLite and encrypted files; a free HTTPS "
             "tunnel gives the group a link; every phone and laptop keeps its own copy and works offline. "
             "Sync packets run from the host to each device.")
    head(s, t, "01", "Core project", "github.com/mitaro-cs/Campus")
    headline(s, X0 - 3, 128, "Campus", 76, t["ink"], -2.5, 0.1)
    para(s, X0, 170, "A site and an app for one study group: homework, a schedule from an .ics file, news and "
         "files. It lives on the group leader's own computer, and every phone keeps a copy that syncs when the "
         "host is back on.", 16.5, t["ink"], 390, 1.5, delay=0.4)

    # how it works, drawn as the system it is; packets run from the host to every device
    bx, bw = 476, X1 - 476
    caps(s, bx, 84, "How it works", t["grey"])
    s.rect(bx, 96, bw, 76, t["bg"], t["ink"], 1.2)
    caps(s, bx + 14, 118, "Host · group leader's computer", t["accent"], size=10.5, weight=700)
    s.text(bx + 14, 142, "Spring Boot · SQLite · AES-256-GCM files", 14.5, t["ink"], 600)
    s.text(bx + 14, 161, "Windows or macOS app, updates in one click", 12.5, t["grey"])
    gap = 10
    cw = (bw - gap * 2) / 3
    centers = [bx + cw / 2 + i * (cw + gap) for i in range(3)]
    s.line(centers[1], 172, centers[1], 198, t["rule"], 1.5)
    s.line(centers[0], 198, centers[-1], 198, t["rule"], 1.5)
    s.text(centers[1] + 10, 190, "HTTPS tunnel: one link, one QR code", 11.5, t["grey"])
    for i, (name, note) in enumerate((("Phone", "own copy"), ("Phone", "works offline"), ("Laptop", "syncs later"))):
        x = bx + i * (cw + gap)
        s.line(centers[i], 198, centers[i], 214, t["rule"], 1.5)
        route = f"M{centers[1]:.1f} 172V198H{centers[i]:.1f}V214"
        length = 26 + abs(centers[i] - centers[1]) + 16
        s.path(route, "none", t["accent"], 2.5,
               extra=f'class="packet" stroke-dasharray="14 {length + 40:.0f}" '
                     f'style="--start:14;--end:-{length:.0f};--t:{i * 0.85:.2f}s"')
        s.rect(x, 214, cw, 58, t["bg"], t["ink"], 1.2)
        s.text(x + 12, 238, name, 14.5, t["ink"], 600)
        s.text(x + 12, 258, note, 12.5, t["grey"])
        s.add(f'<circle cx="{x + cw - 14:.1f}" cy="{233}" r="4" fill="{t["accent"]}" class="pulse" '
              f'style="--t:{i * 0.85 + 0.9:.2f}s"/>')

    s.line(X0, 318, X1, 318, t["rule"], 1)
    figures(s, t, 376, items, accent_last=True, delay=0.3)
    s.line(X0, 422, X1, 422, t["rule"], 1)
    caps(s, X0, 446, f"{r['commits']} commits · AGPL-3.0", t["grey"])
    caps(s, X1, 446, "Windows · macOS · iPhone · Android", t["grey"], "end")
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


def rhythm(t):
    H = 556
    f = facts()
    s = page(t, H, f"02 Rhythm: {f['night']}% of my commits land after 22:00 Moscow time. Peak hour "
             f"{f['peak']:02d}:00, longest streak {f['streak']} days, busiest day {f['weekday']}.",
             "A 24-hour dial of commits by hour with a sweeping hand, and a strip of commits per day over the "
             "last 26 weeks.")
    head(s, t, "02", "Rhythm", "Moscow time · last 26 weeks")
    headline(s, X0 - 6, 178, f"{f['night']}%", 120, t["accent"], -5, 0.1)
    para(s, X0, 222, "of my commits land after 22:00.", 19, t["ink"], 330, 1.4, 600, delay=0.5)
    rows = [("Peak hour", f"{f['peak']:02d}:00"), ("Longest streak", f"{f['streak']} days"),
            ("Busiest day", f["weekday"]), ("Active days", str(len(f["per_day"])))]
    for i, (a, b) in enumerate(rows):
        y = 284 + i * 32
        s.line(X0, y - 21, X0 + 330, y - 21, t["rule"], 1)
        s.g("fade", f"--t:{0.7 + i * 0.1:.2f}s")
        s.text(X0, y, a, 14, t["grey"])
        s.text(X0 + 330, y, b, 14, t["ink"], 600, "end")
        s.end()
    s.line(X0, 284 + len(rows) * 32 - 21, X0 + 330, 284 + len(rows) * 32 - 21, t["rule"], 1)

    # the 24-hour dial: one sector per hour, night hours in the accent, a radar hand sweeping round
    cx, cy, r0, r1 = 680, 222, 40, 122
    caps(s, 476, 90, "Commits by hour", t["grey"])
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r1 + 4}" fill="none" stroke="{t["rule"]}" stroke-width="1"/>')
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{r0 - 6}" fill="none" stroke="{t["rule"]}" stroke-width="1"/>')
    top = max(f["hours"]) or 1
    for h, n in enumerate(f["hours"]):
        a0, a1 = h * 15 + 1.5, h * 15 + 13.5
        r = r0 + (r1 - r0) * n / top
        if n:
            s.path(sector(cx, cy, r0, max(r, r0 + 2), a0, a1), t["accent"] if h in NIGHT_HOURS else t["ink"],
                   extra=f'class="grow" style="transform-origin:{cx}px {cy}px;--t:{0.3 + h * 0.03:.2f}s"')
        else:
            s.path(sector(cx, cy, r0, r0 + 2, a0, a1), t["rule"])
    for h in (0, 6, 12, 18):
        rad = math.radians(h * 15 - 90)
        s.text(cx + (r1 + 17) * math.cos(rad), cy + (r1 + 17) * math.sin(rad) + 4, f"{h:02d}", 11, t["grey"],
               anchor="middle")
    s.text(cx, cy - 2, f"{f['peak']:02d}:00", 15, t["ink"], 700, "middle")
    s.text(cx, cy + 14, "peak", 10.5, t["grey"], anchor="middle")
    gid = s.uid("sw")
    s.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["accent"]}" '
                  f'stop-opacity="0"/><stop offset="1" stop-color="{t["accent"]}" stop-opacity=".22"/></linearGradient>')
    s.add(f'<g class="sweep" style="transform-origin:{cx}px {cy}px">'
          f'<path d="{sector(cx, cy, r0 - 6, r1 + 4, -40, 0)}" fill="url(#{gid})"/>'
          f'<line x1="{cx}" y1="{cy - r0 + 6}" x2="{cx}" y2="{cy - r1 - 4}" stroke="{t["accent"]}" stroke-width="1.5"/>'
          "</g>")

    # per day: one strip across the page, ink by intensity, the busiest day in the accent
    f_y = 446
    caps(s, X0, f_y - 14, "Commits per day", t["grey"])
    weeks, gap = 26, 4
    cell = (X1 - X0 - gap * (weeks - 1)) / weeks
    today = dt.datetime.now(MSK).date()
    start = today - dt.timedelta(days=today.weekday() + 7 * (weeks - 1))
    shown = {d: n for d, n in f["per_day"].items() if d >= start}
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
                s.rect(x, y, cell, 8, t["accent"])
            elif n:
                s.rect(x, y, cell, 8, t["ink"], opacity=(0.35, 0.6, 0.8, 1)[(n >= 3) + (n >= 6) + (n >= 10)])
            else:
                s.rect(x, y, cell, 8, t["rule"])
        s.end()
    if peak_day:
        caps(s, X1, f_y - 14, f"busiest: {shown[peak_day]} on {peak_day.day} {MONTHS[peak_day.month - 1]}",
             t["accent"], "end")
    caps(s, X0, f_y + 96, MONTHS[start.month - 1], t["grey"], size=10)
    caps(s, X1, f_y + 96, MONTHS[today.month - 1], t["grey"], "end", size=10)
    return s


# ------------------------------------------------------------------ 03 Toolkit
TOOLKIT = [("Languages", ["Java", "Python", "TypeScript", "JavaScript", "Rust", "SQL"]),
           ("Frameworks", ["Spring Boot", "Svelte", "Flask", "Tauri"]),
           ("Tools", ["SQLite", "Docker", "Git and Actions", "Linux", "Figma", "Zed"])]


def toolkit(t):
    H = 352
    langs = all_langs()
    total = sum(v for _, v in langs) or 1
    s = page(t, H, "03 Toolkit. Code by language: " + ", ".join(f"{k} {round(100 * v / total)}%" for k, v in langs)
             + ". " + " ".join(f"{a}: {', '.join(b)}." for a, b in TOOLKIT))
    head(s, t, "03", "Toolkit", f"{code_size()} of code in {len(CODE_REPOS)} repositories")
    # one bar, the biggest language in the accent, the rest in steps of ink; segments slide in one by one
    x, bw, y = X0, X1 - X0, 74
    shades = [1, 0.72, 0.52, 0.38, 0.26, 0.17, 0.11]
    for i, (k, v) in enumerate(langs):
        w = bw * v / total
        s.g("wide", f"--t:{0.15 + i * 0.12:.2f}s")
        s.rect(x, y, max(0.0, w - 3), 16, t["accent"] if i == 0 else t["ink"], opacity=1 if i == 0 else shades[i])
        s.end()
        if w > text_width(13, k, 600) + 8:
            s.g("fade", f"--t:{0.5 + i * 0.12:.2f}s")
            s.text(x, y + 40, k, 13, t["ink"], 600)
            s.text(x, y + 58, f"{round(100 * v / total)}%", 12.5, t["grey"])
            s.end()
        x += w
    s.line(X0, 162, X1, 162, t["rule"], 1)
    cw = (X1 - X0) / len(TOOLKIT)
    for i, (title, items) in enumerate(TOOLKIT):
        x = X0 + i * cw + (16 if i else 0)
        caps(s, x, 192, title, t["grey"])
        for j, item in enumerate(items):
            s.g("fade", f"--t:{0.4 + i * 0.15 + j * 0.06:.2f}s")
            s.text(x, 222 + j * 22, item, 15.5, t["ink"])
            s.end()
        if i:
            s.line(X0 + i * cw, 178, X0 + i * cw, 330, t["rule"], 1)
    return s


if __name__ == "__main__":
    both(cover, "cover")
    both(campus, "campus")
    both(rhythm, "rhythm")
    both(toolkit, "toolkit")
