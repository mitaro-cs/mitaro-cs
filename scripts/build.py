#!/usr/bin/env python3
"""Builds every SVG of the profile README into ../assets from scripts/data.json.

Style: a park. The header is a small scene (trees, a lamp, a bench and the dog from the avatar),
the cards below are flat and quiet in the same leaf, bark and gravel colours. Every card is
rendered twice, `-light.svg` (a sunny day) and `-dark.svg` (the park after dusk), and the README
picks one with <picture> so it follows GitHub's theme. Text uses the system font, nothing embedded.
"""
import datetime as dt
import json
import os
import re
import sys

from lib import BARK, BENCH, DOG, FUR, LAMP, LEAF, LEAF_DEEP, LEAF_SOFT, SAND, SKY, Svg, icon_path, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
W = 888

THEMES = {
    "light": dict(top="#f7faf2", bottom="#e9f0e0", edge="#cddbc0", ink="#1e2b21", soft="#3f5244", mute="#5f7360",
                  accent=BENCH, leaf=LEAF, chip="#fbfdf8",
                  heat=["#dfe8d5", "#c2dbae", "#8fbb79", "#5a9150", "#2e6233"]),
    "dark": dict(top="#1d2e23", bottom="#152219", edge="#2f4636", ink="#eef3e8", soft="#c5d3c0", mute="#94a891",
                 accent=LAMP, leaf=LEAF_SOFT, chip="#14201a",
                 heat=["#22352a", "#2d5a36", "#3f7d45", "#68a85b", "#a5d68a"]),
}
LANG_COLOR = {"Java": BENCH, "Svelte": LAMP, "Python": SKY, "TypeScript": LEAF, "JavaScript": SAND,
              "CSS": LEAF_SOFT, "HTML": BARK, "Other": "#9aa395"}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]
NOT_CODE = {"Rich Text Format"}
PIN_NAMES = ("campus", "storagesystem")   # Campus was called StorageSystem before the rename
REPO_NAMES = {"campus": "Campus", "storagesystem": "Campus", "kworkingsystem": "Kworking"}
LEAF_ICON = "M3 21C3 10 10 3 21 3c0 11-7 18-18 18z"


# ------------------------------------------------------------------ data helpers
def pinned_repo():
    return next(r for r in DATA["repos"] if r["name"].lower() in PIN_NAMES)


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


def all_langs():
    tot = {}
    for r in CODE_REPOS:
        for k, v in r["langs"].items():
            tot[k] = tot.get(k, 0) + v
    return bucket_langs(tot, 4)


def code_size(kb):
    """Amount of code as text: megabytes once it passes 1000 KB."""
    return f"{kb / 1000:.1f} MB" if kb >= 1000 else f"{kb} KB"


def fit(txt, size, maxw, weight=400):
    """Cuts a line to maxw px, ending it with an ellipsis when it had to cut."""
    if text_width(size, txt, weight) <= maxw:
        return txt
    while txt and text_width(size, txt + "…", weight) > maxw:
        txt = txt[:-1]
    return txt.rstrip() + "…"


# ------------------------------------------------------------------ shared drawing bits
def card(t, h, title, desc=""):
    s = Svg(W, h, title, desc)
    bg = s.gradient([(0, t["top"], 1), (1, t["bottom"], 1)], 0, 0, 0, 1)
    s.rect(1, 1, W - 2, h - 2, bg, t["edge"], 1.5, 16)
    return s


def label(s, x, y, txt, fill, size=12, anchor="start"):
    """Small spaced capitals: the voice of every label."""
    s.text(x, y, txt, size, fill, 600, anchor=anchor, ls=1.4)


def heading(s, t, txt, right=""):
    """Card title with a leaf in front, and an optional note on the right."""
    s.path(LEAF_ICON, t["leaf"], extra='transform="translate(34 30) scale(.62)"')
    label(s, 56, 44, txt, t["mute"])
    if right:
        label(s, W - 36, 44, right, t["mute"], anchor="end")


def lang_bar(s, x, y, w, h, langs):
    total = sum(v for _, v in langs) or 1
    cid = s.uid("lb")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.g("grow", "animation-delay:.3s")
    cx = x
    for k, v in langs:
        seg = w * v / total
        s.rect(cx, y, max(0.0, seg - 2), h, LANG_COLOR.get(k, LANG_COLOR["Other"]))
        cx += seg
    s.end()
    s.add("</g>")
    return total


def legend(s, t, x, y, langs, total, step=None, size=13):
    for i, (k, v) in enumerate(langs):
        lx = x + i * step if step else x
        pct = f"{round(100 * v / total)}%"
        s.circle(lx + 5, y - 4.5, 5, LANG_COLOR.get(k, LANG_COLOR["Other"]))
        s.text(lx + 16, y, k, size, t["ink"], 600)
        s.text(lx + 16 + text_width(size, k + " ", 600), y, pct, size, t["mute"])
        if not step:
            x += text_width(size, f"{k} {pct}", 600) + 34


def both(fn, name):
    for theme, t in THEMES.items():
        fn(t, theme).save(OUT, f"{name}-{theme}.svg")


# ------------------------------------------------------------------ header: a corner of the park
def dog(s, x, y):
    """The little crested dog from the avatar, sitting; it wags and tilts its head now and then."""
    s.g(transform=f"translate({x} {y}) scale(1.3)")
    s.g("wag", transform="translate(12 -9)")
    s.path("M0 0C8-3 11-13 8-21", stroke=DOG, sw=3.2)
    s.circle(8, -22, 3.6, FUR)
    s.end()
    s.path("M-13 0C-15-18-10-34 0-36C10-34 15-18 13 0Z", DOG)
    s.add('<ellipse cx="9" cy="-7" rx="8" ry="7" fill="#2b221f"/>')
    s.rect(-8, -18, 5, 18, DOG, rx=2.5)
    s.rect(2, -18, 5, 18, DOG, rx=2.5)
    s.add(f'<ellipse cx="-5.5" cy="-.5" rx="4" ry="2.2" fill="{FUR}"/>'
          f'<ellipse cx="4.5" cy="-.5" rx="4" ry="2.2" fill="{FUR}"/>')
    s.path("M-5-30C-3-22 3-22 5-30C2-27-2-27-5-30Z", FUR, opacity=0.9)
    s.g("tilt", transform="translate(0 -44)")
    for sx in (-1, 1):
        s.path(f"M{-8 * sx} -4L{-15 * sx} -25L{-2 * sx} -9Z", DOG)
        for fx, fy, r in ((-14.6, -24, 2.7), (-13.4, -19.6, 2.5), (-11.9, -15, 2.2)):   # silky ear fringe
            s.circle(fx * sx, fy, r, FUR)
    s.add(f'<ellipse cx="0" cy="0" rx="10.5" ry="10" fill="{DOG}"/>')
    for cx, cy, r in ((-5, -8, 4.5), (0, -10.5, 5), (5, -8, 4.5), (-2.5, -13.5, 3.5), (3, -13.5, 3.5)):
        s.circle(cx, cy, r, FUR)
    s.add('<ellipse cx="0" cy="5" rx="6" ry="4.4" fill="#4a3d38"/><ellipse cx="0" cy="3.2" rx="2" ry="1.5" fill="#111"/>')
    for ex in (-4.2, 4.2):
        s.circle(ex, -1, 1.8, "#111")
        s.circle(ex + 0.5, -1.6, 0.6, FUR)
    s.path("M-4 9C-2 12 2 12 4 9", stroke=FUR, sw=2)
    s.end()
    s.end()


def header(t, theme):
    H = 236
    day = theme == "light"
    s = Svg(W, H, "Mitaro. Omar, computer science student at MTUCI. Builds local-first software.",
            "A corner of a park: plane trees, a street lamp and a wooden bench with a small crested dog on it.")
    s.defs.append(f'<clipPath id="hc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16"/></clipPath>')
    s.add('<g clip-path="url(#hc)">')
    sky = ["#cfe4ec", "#eef4e6"] if day else ["#172a35", "#1d3427"]
    s.rect(0, 0, W, H, s.gradient([(0, sky[0], 1), (0.8, sky[1], 1)], 0, 0, 0, 1))
    if day:
        s.rect(0, 0, W, H, s.gradient([(0, "#fbecc4", 0.9), (1, "#fbecc4", 0)], 0.08, 0, 0.5, kind="radial"))
    else:
        for x, y, r in ((60, 30, 1.2), (150, 22, 1), (250, 40, 1.3), (330, 18, 1), (420, 34, 1.1), (210, 70, 0.9),
                        (470, 16, 1), (380, 64, 0.8)):
            s.circle(x, y, r, FUR, 0.7)

    # far trees across the whole width, then near plane trees on the right
    far = "#c3d9b0" if day else "#203a2a"
    for i, x in enumerate(range(-20, W + 40, 52)):
        s.circle(x, 168 - (i * 37 % 23), 34 + (i * 17 % 14), far)
    trunk = BARK if day else "#4a3e33"
    for x, top in ((520, 104), (628, 92), (848, 98)):
        s.rect(x - 6, top, 12, 120, trunk, rx=3)
        s.add(f'<ellipse cx="{x - 1}" cy="{top + 60}" rx="3" ry="6" fill="{SAND}" opacity=".45"/>')
    s.g("sway")
    for col, dy in ((LEAF_DEEP if day else "#1f3626", 6), (LEAF if day else "#2e4a33", 0)):
        for cx, cy, r in ((498, 104, 30), (525, 82, 40), (556, 102, 30), (600, 76, 36), (632, 58, 46), (668, 80, 36),
                          (820, 84, 34), (852, 62, 44), (884, 86, 34)):
            s.circle(cx, cy + dy, r, col)
    s.end()

    # ground and the gravel path
    s.rect(0, 196, W, H - 196, "#cfe2bb" if day else "#1b3022")
    s.path("M0 214C300 198 600 226 888 206L888 236L0 236Z", SAND if day else "#3a3a2c", opacity=0.85)

    # street lamp
    post = "#33413a" if day else "#0f1813"
    if not day:
        s.circle(588, 90, 90, s.gradient([(0, LAMP, 0.45), (1, LAMP, 0)], 0.5, 0.5, 0.5, kind="radial"),
                 extra='class="glow"')
    s.rect(586, 92, 5, 116, post, rx=2)
    s.path("M578 92L599 92L595 80L582 80Z", post)
    s.circle(588.5, 92, 4.5, "#f3dcae" if day else LAMP)

    # the bench and the dog on it
    wood, legs = (BENCH, "#4d3a2b") if day else ("#7d5034", "#2a1f17")
    for x in (652, 786):
        s.rect(x, 146, 5, 30, legs)
        s.rect(x, 184, 5, 24, legs)
    for y in (146, 154, 162):
        s.rect(640, y, 160, 5, wood, rx=2)
    for y in (174, 180):
        s.rect(632, y, 176, 5, wood, rx=2)
    dog(s, 712, 175)

    # the name
    s.g("rise")
    label(s, 40, 62, "OMAR  ·  MTUCI  ·  COMPUTER SCIENCE", "#4d6050" if day else "#a9bba6")
    s.text(38, 122, "Mitaro", 56, "#1e2b21" if day else "#eef3e8", 700, ls=-1)
    s.end()
    s.g("rise", "animation-delay:.15s")
    s.text(40, 156, "I build local-first software:", 19, "#3f5244" if day else "#c5d3c0")
    s.text(40, 182, "your data stays on your machine.", 19, BENCH if day else LAMP, 600)
    s.end()
    s.add("</g>")
    s.rect(1, 1, W - 2, H - 2, "none", t["edge"], 1.5, 16)
    return s


# ------------------------------------------------------------------ pinned project
PIN = dict(
    name="Campus",
    tag="A study-group site and app that lives on the group leader's own computer.",
    platforms="Windows · macOS · iPhone · Android",
    license="AGPL-3.0",
    stack=["Java", "Spring Boot", "Svelte", "Tauri"],
)
# what the project is made of; counted from its file tree by fetch.py
PIN_TILES = [("java", "Java classes"), ("svelte", "Components"), ("tests", "Test files"),
             ("migrations", "Migrations"), ("screens", "Screens"), ("versions", "Versions")]


def pinned(t, theme):
    r = pinned_repo()
    stats = DATA.get("pin") or {}
    tiles = [(str(stats[k]), lab) for k, lab in PIN_TILES if stats.get(k)]
    H = 372 if tiles else 268
    s = card(t, H, f"Pinned: {PIN['name']}. {PIN['tag']} "
             + ", ".join(f"{v} {lab.lower()}" for v, lab in tiles))
    s.path(icon_path("pin"), t["accent"], extra='transform="translate(34 30) scale(.62)"')
    label(s, 56, 44, "PINNED PROJECT", t["accent"])
    label(s, W - 36, 44, PIN["platforms"].upper(), t["mute"], anchor="end")
    s.g("rise")
    s.text(34, 100, PIN["name"], 44, t["ink"], 700, ls=-0.5)
    s.end()
    s.text(36, 132, PIN["tag"], 17, t["soft"])
    y = 160
    if tiles:
        s.line(36, y, W - 36, y, t["edge"], 1.2)
        cw = (W - 72) / len(tiles)
        for i, (v, lab) in enumerate(tiles):
            x = 36 + i * cw
            s.g("rise", f"animation-delay:{0.1 + i * 0.06:.2f}s")
            s.text(x, 214, v, 36, t["ink"], 700, ls=-0.5)
            s.text(x, 238, lab, 13, t["mute"])
            s.end()
            if i:
                s.line(x - 14, 184, x - 14, 242, t["edge"], 1)
        y = 266
    s.line(36, y, W - 36, y, t["edge"], 1.2)
    langs = bucket_langs(r["langs"], 3)
    label(s, 36, y + 30, "LANGUAGES", t["mute"])
    total = lang_bar(s, 36, y + 42, 360, 8, langs)
    legend(s, t, 36, y + 78, langs[:4], total, size=12.5)
    cx = W - 36
    for k in reversed(PIN["stack"]):
        tw = text_width(12.5, k, 600) + 24
        cx -= tw
        s.rect(cx, y + 20, tw, 28, t["chip"], t["edge"], 1.2, 14)
        s.text(cx + tw / 2, y + 38.5, k, 12.5, t["soft"], 600, anchor="middle")
        cx -= 8
    s.text(W - 36, y + 78, f"{r.get('release') or 'no release'}  ·  {r['commits']} commits  ·  {PIN['license']}",
           12.5, t["mute"], anchor="end")
    return s


# ------------------------------------------------------------------ activity: when and how often
MSK = dt.timezone(dt.timedelta(hours=3))
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
NIGHT_HOURS = (22, 23, 0, 1, 2, 3)


def commit_times():
    return [dt.datetime.fromisoformat(c["ts"].replace("Z", "+00:00")).astimezone(MSK) for c in DATA["commits"]]


def longest_streak(days):
    best = run = 0
    prev = None
    for d in sorted(days):
        run = run + 1 if prev and (d - prev).days == 1 else 1
        best, prev = max(best, run), d
    return best


def activity(t, theme):
    times = commit_times()
    per_day, hours, by_wd = {}, [0] * 24, [0] * 7
    for m in times:
        per_day[m.date()] = per_day.get(m.date(), 0) + 1
        hours[m.hour] += 1
        by_wd[m.weekday()] += 1
    night = sum(hours[h] for h in NIGHT_HOURS)
    peak = max(range(24), key=lambda h: hours[h])
    tiles = [("Longest streak", f"{longest_streak(per_day)} days"), ("Active days", str(len(per_day))),
             ("Busiest day", WEEKDAYS[max(range(7), key=lambda d: by_wd[d])]),
             ("Peak hour", f"{peak:02d}:00"), ("After 22:00", f"{round(100 * night / max(1, len(times)))}%")]
    H = 324
    s = card(t, H, "Activity: commits per day over the last 26 weeks and by hour of the day. "
             + ", ".join(f"{a.lower()} {b}" for a, b in tiles))

    # heatmap: 26 weeks x 7 days, newest week on the right, in leaf greens
    weeks, cell, gap = 26, 13, 3
    today = dt.datetime.now(MSK).date()
    start = today - dt.timedelta(days=today.weekday() + 7 * (weeks - 1))
    shown = sum(v for d, v in per_day.items() if d >= start)
    heading(s, t, "LAST 26 WEEKS")
    label(s, 36 + weeks * (cell + gap) - gap, 44, f"{shown} COMMITS", t["accent"], anchor="end")
    last_month = None
    for w in range(weeks):
        for d in range(7):
            day = start + dt.timedelta(days=7 * w + d)
            if day > today:
                continue
            n = per_day.get(day, 0)
            level = 0 if not n else 1 + (n >= 3) + (n >= 6) + (n >= 10)
            s.rect(36 + w * (cell + gap), 64 + d * (cell + gap), cell, cell, t["heat"][level], rx=3)
        first = start + dt.timedelta(days=7 * w)
        if first.month != last_month and w < weeks - 1:
            s.text(36 + w * (cell + gap), 196, MONTHS[first.month - 1], 12, t["mute"])
            last_month = first.month

    # commits by hour, Moscow time; late hours glow like the lamp
    hx, hw = 500, W - 36 - 500
    label(s, hx, 44, "BY HOUR, MOSCOW TIME", t["mute"])
    bw = (hw - 23 * 3) / 24
    top = max(hours) or 1
    for h, n in enumerate(hours):
        bh = max(2.0, 110 * n / top)
        s.g("rise", f"animation-delay:{h * 0.02:.2f}s")
        s.rect(hx + h * (bw + 3), 174 - bh, bw, bh, LAMP if h in NIGHT_HOURS else t["leaf"], rx=2,
               opacity=1 if n else 0.35)
        s.end()
    for h in (0, 6, 12, 18):
        s.text(hx + h * (bw + 3), 196, f"{h:02d}", 12, t["mute"])
    s.text(hx + hw, 196, "23", 12, t["mute"], anchor="end")

    s.line(36, 218, W - 36, 218, t["edge"], 1.2)
    cw = (W - 72) / len(tiles)
    for i, (a, b) in enumerate(tiles):
        x = 36 + i * cw
        s.g("rise", f"animation-delay:{0.2 + i * 0.07:.2f}s")
        s.text(x, 248, a, 13, t["accent"] if a == "After 22:00" else t["mute"])
        s.text(x, 286, b, 28, t["ink"], 700, ls=-0.5)
        s.end()
    return s


# ------------------------------------------------------------------ numbers and languages
def numbers(t, theme):
    repos = DATA["repos"]
    kb = sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k not in NOT_CODE) // 1000
    items = [("Repositories", str(len(repos))), ("Commits", str(sum(r["commits"] for r in repos))),
             ("Stars", str(sum(r["stars"] for r in repos))), ("Followers", str(DATA["followers"])),
             ("Code", code_size(kb))]
    langs = all_langs()
    rows = (len(langs) + 3) // 4
    H = 228 + rows * 26
    s = card(t, H, "GitHub in numbers: " + ", ".join(f"{a} {b}" for a, b in items)
             + ". Code by language: " + ", ".join(k for k, _ in langs))
    heading(s, t, "ON GITHUB")
    cw = (W - 72) / len(items)
    for i, (a, b) in enumerate(items):
        x = 36 + i * cw
        s.g("rise", f"animation-delay:{i * 0.07:.2f}s")
        s.text(x, 108, b, 36, t["ink"], 700, ls=-0.5)
        s.text(x, 132, a, 13, t["mute"])
        s.end()
    label(s, 36, 172, "CODE BY LANGUAGE", t["mute"])
    total = lang_bar(s, 36, 184, W - 72, 10, langs)
    for r0 in range(rows):
        legend(s, t, 36, 226 + r0 * 26, langs[r0 * 4:r0 * 4 + 4], total, step=(W - 72) / 4)
    return s


# ------------------------------------------------------------------ tech stack
STACK = [("python", "Python", 1), ("flask", "Flask", 1), ("openjdk", "Java", 1), ("springboot", "Spring", 1),
         ("svelte", "Svelte", 1), ("typescript", "TypeScript", 0), ("javascript", "JavaScript", 0),
         ("html5", "HTML5", 0), ("css3", "CSS3", 0), ("sqlite", "SQLite", 0), ("docker", "Docker", 0),
         ("tauri", "Tauri", 0), ("rust", "Rust", 0), ("git", "Git", 0), ("githubactions", "Actions", 0),
         ("gnubash", "Bash", 0), ("linux", "Linux", 0), ("figma", "Figma", 0), ("obsidian", "Obsidian", 0),
         ("zedindustries", "Zed", 0)]


def stack(t, theme):
    chips, x, y = [], 36, 66
    for ic, name, hot in STACK:                     # flow layout, wraps at the card edge
        w = text_width(13, name, 600) + 52
        if x + w > W - 36:
            x, y = 36, y + 46
        chips.append((x, y, w, ic, name, hot))
        x += w + 8
    H = y + 36 + 30
    s = card(t, H, "Tech stack: " + ", ".join(n for _, n, _ in STACK))
    heading(s, t, "TOOLKIT", "DAILY DRIVERS FIRST")
    for i, (x, y, w, ic, name, hot) in enumerate(chips):
        s.g("rise", f"animation-delay:{i * 0.03:.2f}s")
        s.rect(x, y, w, 36, t["chip"], t["accent"] if hot else t["edge"], 1.3, 18)
        s.icon(ic, x + 14, y + 10, 16, t["accent"] if hot else t["soft"])
        s.text(x + 38, y + 23, name, 13, t["ink"], 600)
        s.end()
    return s


# ------------------------------------------------------------------ latest commits
def commits(t, theme):
    rows = [c for c in DATA["commits"] if not c["msg"].startswith(("Initial commit", "Merge "))][:6]
    kinds = {}
    for c in DATA["commits"]:
        m = re.match(r"(\w+)(\(.*?\))?!?:", c["msg"])
        if m:
            kinds[m.group(1).lower()] = kinds.get(m.group(1).lower(), 0) + 1
    top = sorted(kinds.items(), key=lambda kv: -kv[1])[:3]
    H = 72 + len(rows) * 36 + 12
    s = card(t, H, "Latest commits: " + "; ".join(c["msg"] for c in rows))
    heading(s, t, "LATEST COMMITS", "  ·  ".join(f"{n} {k}" for k, n in top).upper())
    for i, c in enumerate(rows):
        y = 88 + i * 36
        if i:
            s.line(36, y - 23, W - 36, y - 23, t["edge"], 1)
        _, m, d = c["ts"][:10].split("-")
        repo = REPO_NAMES.get(c["repo"].lower(), c["repo"])
        s.g("rise", f"animation-delay:{i * 0.06:.2f}s")
        s.text(36, y, f"{int(d)} {MONTHS[int(m) - 1]}", 13.5, t["mute"])
        s.text(104, y, fit(repo, 13.5, 120, 600), 13.5, t["accent"], 600)
        s.text(240, y, fit(c["msg"], 14, W - 36 - 240), 14, t["ink"])
        s.end()
    return s


if __name__ == "__main__":
    both(header, "header")
    both(pinned, "pinned")
    both(activity, "activity")
    both(numbers, "numbers")
    both(stack, "stack")
    both(commits, "commits")
