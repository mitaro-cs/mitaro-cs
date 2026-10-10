#!/usr/bin/env python3
"""Builds the SVGs of the profile README into ../assets from scripts/data.json.

Concept: the profile as an editorial spread. No pictures: big type, a strict grid, hairline rules,
one accent colour, and on every page the real data is the object (the Campus architecture, its
numbers, when I commit, what I write in). Every page is rendered twice, -light.svg and -dark.svg,
and the README picks one with <picture> so it follows GitHub's theme.
"""
import datetime as dt
import json
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
PIN_NAMES = ("campus", "storagesystem")   # Campus was called StorageSystem before the rename
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]


# ------------------------------------------------------------------ data
def pinned_repo():
    return next(r for r in DATA["repos"] if r["name"].lower() in PIN_NAMES)


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


# ------------------------------------------------------------------ type and rules
def page(t, h, title, desc=""):
    s = Svg(W, h, title, desc)
    s.rect(0, 0, W, h, t["bg"])
    return s


def caps(s, x, y, txt, fill, anchor="start", size=11, weight=600):
    s.text(x, y, txt.upper(), size, fill, weight, anchor, ls=1.6)


def head(s, t, num, label, right=""):
    """Section line: number in the accent, label in caps, a hairline to the margin, a note on the right."""
    caps(s, X0, 40, num, t["accent"], size=12, weight=700)
    caps(s, X0 + 30, 40, label, t["ink"], size=12, weight=700)
    start = X0 + 30 + text_width(12, label.upper(), 700, 1.6) + 14
    end = X1 - (text_width(11, right.upper(), 600, 1.6) + 14 if right else 0)
    s.line(start, 36, end, 36, t["rule"], 1)
    if right:
        caps(s, X1, 40, right, t["grey"], "end")


def para(s, x, y, txt, size, fill, maxw, lead=1.45, weight=400):
    for ln in wrap(txt, size, maxw, weight):
        s.text(x, y, ln, size, fill, weight)
        y += size * lead
    return y


def figures(s, t, y, items, accent_last=False):
    """A row of big numbers with small labels, split by hairlines."""
    cw = (X1 - X0) / len(items)
    for i, (v, lab) in enumerate(items):
        x = X0 + i * cw + (16 if i else 0)
        hot = accent_last and i == len(items) - 1
        s.text(x, y, str(v), 34, t["accent"] if hot else t["ink"], 700, ls=-0.8)
        s.text(x, y + 22, lab, 12.5, t["grey"])
        if i:
            s.line(X0 + i * cw, y - 32, X0 + i * cw, y + 26, t["rule"], 1)


def vertical(s, x, y, txt, fill):
    s.add(f'<text x="0" y="0" font-size="10.5" fill="{fill}" letter-spacing="1.6" text-anchor="middle" '
          f'transform="translate({x} {y}) rotate(-90)">{txt.upper()}</text>')


def both(fn, name):
    for theme, t in THEMES.items():
        fn(t).save(OUT, f"{name}-{theme}.svg")


# ------------------------------------------------------------------ cover
def cover(t):
    H = 360
    f = facts()
    repos = DATA["repos"]
    last = f["last"]
    s = page(t, H, "Mitaro. Omar, computer science student at MTUCI. I build local-first software: the data stays "
             "on a machine you control.")
    caps(s, X0, 40, "mitaro-cs · GitHub profile", t["grey"])
    if last:
        caps(s, X1, 40, f"last commit {last.day} {MONTHS[last.month - 1]} {last.year}", t["grey"], "end")
    s.line(X0, 52, X1, 52, t["ink"], 1.5)
    s.text(X0 - 6, 178, "Mitaro", 124, t["ink"], 700, ls=-5)
    s.text(476, 106, "Omar, CS student at MTUCI.", 18, t["ink"], 600)
    para(s, 476, 134, "I build local-first software: the data stays on a machine you control, not on someone "
         "else's server.", 17, t["grey"], X1 - 476, 1.42)
    s.line(X0, 214, X1, 214, t["rule"], 1)
    figures(s, t, 270, [(sum(r["commits"] for r in repos), "commits"), (len(repos), "public repositories"),
                        (code_size(), "of code"), ("Campus", "pinned project")], accent_last=True)
    s.line(X0, 324, X1, 324, t["ink"], 1.5)
    caps(s, X0, 346, "Contents", t["grey"])
    x = X0 + 100
    for num, name in (("01", "Campus"), ("02", "Rhythm"), ("03", "Toolkit")):
        caps(s, x, 346, num, t["accent"], weight=700)
        caps(s, x + 24, 346, name, t["ink"], weight=700)
        x += 24 + text_width(11, name.upper(), 700, 1.6) + 28
    caps(s, X1, 346, f"online since {DATA['created'][:4]}", t["grey"], "end")
    return s


# ------------------------------------------------------------------ 01 Campus
def campus(t):
    H = 470
    r = pinned_repo()
    pin = DATA.get("pin") or {}
    items = [(pin.get(k), lab) for k, lab in (("java", "Java classes"), ("svelte", "Svelte components"),
                                              ("tests", "test files"), ("migrations", "DB migrations"),
                                              ("versions", "versions"))]
    items = [(v, lab) for v, lab in items if v] + [(r.get("release") or "—", "latest release")]
    s = page(t, H, "01 Campus: a site and an app for one study group that lives on the group leader's own "
             "computer. " + ", ".join(f"{v} {lab}" for v, lab in items) + ".",
             "How it works: the host computer runs the server with SQLite and encrypted files; a free HTTPS "
             "tunnel gives the group a link; every phone and laptop keeps its own copy and works offline.")
    head(s, t, "01", "Feature", "github.com/mitaro-cs/Campus")
    s.text(X0 - 3, 128, "Campus", 76, t["ink"], 700, ls=-2.5)
    para(s, X0, 170, "A site and an app for one study group: homework, a schedule from an .ics file, news and "
         "files. It lives on the group leader's own computer, and every phone keeps a copy that syncs when the "
         "host is back on.", 16.5, t["ink"], 390, 1.5)

    # how it works, drawn as the system it is
    bx, bw = 476, X1 - 476
    caps(s, bx, 84, "How it works", t["grey"])
    s.rect(bx, 96, bw, 76, "none", t["ink"], 1.2)
    caps(s, bx + 14, 118, "Host · group leader's computer", t["accent"], size=10.5, weight=700)
    s.text(bx + 14, 142, "Spring Boot · SQLite · AES-256-GCM files", 14.5, t["ink"], 600)
    s.text(bx + 14, 161, "Windows or macOS app, updates in one click", 12.5, t["grey"])
    cols = 3
    gap = 10
    cw = (bw - gap * (cols - 1)) / cols
    centers = [bx + cw / 2 + i * (cw + gap) for i in range(cols)]
    s.line(centers[1], 172, centers[1], 198, t["accent"], 1.5)
    s.line(centers[0], 198, centers[-1], 198, t["accent"], 1.5)
    s.text(centers[1] + 10, 190, "HTTPS tunnel: one link, one QR code", 11.5, t["grey"])
    for i, (name, note) in enumerate((("Phone", "own copy"), ("Phone", "works offline"), ("Laptop", "syncs later"))):
        x = bx + i * (cw + gap)
        s.line(centers[i], 198, centers[i], 214, t["accent"], 1.5)
        s.rect(x, 214, cw, 58, "none", t["ink"], 1.2)
        s.text(x + 12, 238, name, 14.5, t["ink"], 600)
        s.text(x + 12, 258, note, 12.5, t["grey"])

    s.line(X0, 318, X1, 318, t["rule"], 1)
    figures(s, t, 376, items, accent_last=True)
    s.line(X0, 422, X1, 422, t["rule"], 1)
    caps(s, X0, 446, f"{r['commits']} commits · AGPL-3.0", t["grey"])
    caps(s, X1, 446, "Windows · macOS · iPhone · Android", t["grey"], "end")
    return s


# ------------------------------------------------------------------ 02 Rhythm
def rhythm(t):
    H = 410
    f = facts()
    s = page(t, H, f"02 Rhythm: {f['night']}% of my commits land after 22:00 Moscow time. Peak hour "
             f"{f['peak']:02d}:00, longest streak {f['streak']} days, busiest day {f['weekday']}.",
             "Commits by hour of the day and commits per day over the last 26 weeks.")
    head(s, t, "02", "Rhythm", "Moscow time · last 26 weeks")
    s.text(X0 - 6, 178, f"{f['night']}%", 120, t["accent"], 700, ls=-5)
    para(s, X0, 222, "of my commits land after 22:00.", 19, t["ink"], 330, 1.4, 600)
    rows = [("Peak hour", f"{f['peak']:02d}:00"), ("Longest streak", f"{f['streak']} days"),
            ("Busiest day", f["weekday"]), ("Active days", str(len(f["per_day"])))]
    for i, (a, b) in enumerate(rows):
        y = 284 + i * 32
        s.line(X0, y - 21, X0 + 330, y - 21, t["rule"], 1)
        s.text(X0, y, a, 14, t["grey"])
        s.text(X0 + 330, y, b, 14, t["ink"], 600, "end")
    s.line(X0, 284 + len(rows) * 32 - 21, X0 + 330, 284 + len(rows) * 32 - 21, t["rule"], 1)

    # by hour: thin bars, the night ones in the accent
    cx, cw = 420, X1 - 420
    caps(s, cx, 76, "Commits by hour", t["grey"])
    bw = (cw - 23 * 4) / 24
    top = max(f["hours"]) or 1
    for h, n in enumerate(f["hours"]):
        bh = max(1.5, 130 * n / top)
        s.rect(cx + h * (bw + 4), 222 - bh, bw, bh, t["accent"] if h in NIGHT_HOURS else t["ink"])
    s.line(cx, 223, X1, 223, t["ink"], 1)
    for h in (0, 6, 12, 18):
        s.text(cx + h * (bw + 4), 240, f"{h:02d}", 11, t["grey"])
    s.text(X1, 240, "23", 11, t["grey"], anchor="end")

    # per day: 26 weeks, ink by intensity, the busiest day in the accent
    caps(s, cx, 280, "Commits per day", t["grey"])
    weeks, gap = 26, 3
    cell = (cw - gap * (weeks - 1)) / weeks
    today = dt.datetime.now(MSK).date()
    start = today - dt.timedelta(days=today.weekday() + 7 * (weeks - 1))
    shown = {d: n for d, n in f["per_day"].items() if d >= start}
    peak_day = max(shown, key=shown.get) if shown else None
    for w in range(weeks):
        for d in range(7):
            day = start + dt.timedelta(days=7 * w + d)
            if day > today:
                continue
            n = f["per_day"].get(day, 0)
            x, y = cx + w * (cell + gap), 292 + d * (cell + gap) * 0.62
            if day == peak_day:
                s.rect(x, y, cell, cell * 0.62, t["accent"])
            elif n:
                s.rect(x, y, cell, cell * 0.62, t["ink"], opacity=(0.35, 0.6, 0.8, 1)[(n >= 3) + (n >= 6) + (n >= 10)])
            else:
                s.rect(x, y, cell, cell * 0.62, t["rule"])
    if peak_day:
        caps(s, X1, 280, f"busiest: {shown[peak_day]} on {peak_day.day} {MONTHS[peak_day.month - 1]}",
             t["accent"], "end")
    caps(s, cx, 388, MONTHS[start.month - 1], t["grey"], size=10)
    caps(s, X1, 388, MONTHS[today.month - 1], t["grey"], "end", size=10)
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
    # one bar, the biggest language in the accent, the rest in steps of ink
    x, bw, y = X0, X1 - X0, 74
    shades = [1, 0.72, 0.52, 0.38, 0.26, 0.17, 0.11]
    for i, (k, v) in enumerate(langs):
        w = bw * v / total
        s.rect(x, y, max(0.0, w - 3), 16, t["accent"] if i == 0 else t["ink"], opacity=1 if i == 0 else shades[i])
        lab = f"{round(100 * v / total)}%"
        if w > text_width(13, k, 600) + 8:
            s.text(x, y + 40, k, 13, t["ink"], 600)
            s.text(x, y + 58, lab, 12.5, t["grey"])
        x += w
    s.line(X0, 162, X1, 162, t["rule"], 1)
    cw = (X1 - X0) / len(TOOLKIT)
    for i, (title, items) in enumerate(TOOLKIT):
        x = X0 + i * cw + (16 if i else 0)
        caps(s, x, 192, title, t["grey"])
        for j, item in enumerate(items):
            s.text(x, 222 + j * 22, item, 15.5, t["ink"])
        if i:
            s.line(X0 + i * cw, 178, X0 + i * cw, 330, t["rule"], 1)
    return s


if __name__ == "__main__":
    both(cover, "cover")
    both(campus, "campus")
    both(rhythm, "rhythm")
    both(toolkit, "toolkit")
