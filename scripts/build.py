#!/usr/bin/env python3
"""Builds every SVG of the profile README into ../assets from scripts/data.json.

Style: an old-web profile page on a Matrix terminal, in the colours of the avatar (lib.py):
dark boxes with bark borders, falling code in leaf green,
the Campus logo as the avatar, a Nokia that shows the pinned project, and a terminal
with the commit stats. The panels carry their own black background, so they read the same on
GitHub's light and dark themes. Text uses the system monospace font, nothing is embedded.
"""
import datetime as dt
import json
import os
import random
import re
import sys

from lib import BRASS, CODE, DIM, FRAME, GLOW, LCD, LCD_INK, LINE, MOSS, MUTED, PANEL, TEXT, VOID, Svg, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
W = 888

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MSK = dt.timezone(dt.timedelta(hours=3))
NIGHT_HOURS = (22, 23, 0, 1, 2, 3)
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]
NOT_CODE = {"Rich Text Format"}
PIN_NAMES = ("campus", "storagesystem")   # Campus was called StorageSystem before the rename
LANG_COLOR = {"Java": GLOW, "Svelte": BRASS, "Python": LCD, "TypeScript": CODE, "JavaScript": MUTED,
              "CSS": "#6c6662", "HTML": "#8a7a6a", "Other": "#473e3a"}
HEAT = ["#231f1e", "#473e3a", "#7a5546", "#b27660", "#e6a986"]   # bench wood warming up to skin
RAIN_CHARS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ0123456789Z:=*+<>"

RABBIT = [
    "..W...W.....",
    "..W...W.....",
    "..WW..W.....",
    "..WW.WW.....",
    ".WWWWWWW....",
    ".WEWWWEW....",
    ".WWWEWWW....",
    "..WWWWW.....",
    ".WWWWWWWW...",
    ".WWWWWWWWW..",
    ".WWWWWWWWWW.",
    "..WW...WW...",
]


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
    return f"{kb / 1000:.1f} MB" if kb >= 1000 else f"{kb} KB"


def facts():
    """Everything the panels say about when and how often I commit (Moscow time)."""
    times = [dt.datetime.fromisoformat(c["ts"].replace("Z", "+00:00")).astimezone(MSK) for c in DATA["commits"]]
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
    last = max(times) if times else None
    return dict(per_day=per_day, hours=hours, streak=best, days=len(per_day),
                night=round(100 * sum(hours[h] for h in NIGHT_HOURS) / max(1, len(times))),
                peak=max(range(24), key=lambda h: hours[h]), weekday=WEEKDAYS[max(range(7), key=lambda d: by_wd[d])],
                last=f"{last.day} {MONTHS[last.month - 1]} {last.year}" if last else "—")


def wrap(txt, size, maxw):
    lines, cur = [], ""
    for wd in txt.split():
        t = (cur + " " + wd).strip()
        if text_width(size, t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    return lines + [cur]


# ------------------------------------------------------------------ shared drawing bits
def frame(title, h, desc=""):
    """A panel of the page: black screen with the dashed frame around it."""
    s = Svg(W, h, title, desc)
    s.rect(0, 0, W, h, VOID, rx=4)
    s.rect(3, 3, W - 6, h - 6, "none", FRAME, 1.5, extra='stroke-dasharray="3 3"')
    return s


def box(s, x, y, w, h, fill=PANEL):
    s.rect(x, y, w, h, fill, LINE, 1.5)


def strip(s, x, y, w, txt):
    """The thin title row on top of a small box."""
    s.rect(x, y, w, 20, "#241f1d", LINE, 1.2)
    s.text(x + 6, y + 14, txt, 11, TEXT, 700)


def button(s, x, y, w, h, txt, size=12):
    s.rect(x, y, w, h, MOSS, "#5c6e52", 1.2, rx=2)
    s.text(x + w / 2, y + h / 2 + size * 0.36, txt, size, TEXT, anchor="middle")


def dots(s, x, y, w, h):
    """A band of tiny dots, the old-web divider."""
    pid = s.uid("p")
    s.defs.append(f'<pattern id="{pid}" width="4" height="4" patternUnits="userSpaceOnUse">'
                  f'<rect width="2" height="2" fill="{LINE}"/></pattern>')
    s.rect(x, y, w, h, f"url(#{pid})")


def sprite(s, rows, x, y, px, colors):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colors:
                s.rect(x + i * px, y + j * px, px, px, colors[ch])


def campus_logo(s, x, y, size):
    """The Campus logo (Atlas carrying a globe, from icons/campus.svg) in the avatar's colours."""
    src = open(os.path.join(HERE, "icons", "campus.svg"), encoding="utf-8").read()
    grid = re.search(r'id="grid"[^>]*\sd="([^"]+)"', src).group(1)
    figure = re.search(r'id="figure"[^>]*\sd="([^"]+)"', src).group(1)
    k = size / 600
    cid = s.uid("gl")
    s.defs.append(f'<clipPath id="{cid}"><circle cx="347.8" cy="273.1" r="165"/></clipPath>')
    s.g(transform=f"translate({x:.1f} {y:.1f}) scale({k:.4f}) translate(-66 -72)")
    s.add(f'<circle cx="347.8" cy="273.1" r="165" fill="{MOSS}" stroke="{CODE}" stroke-width="4"/>')
    s.add(f'<path d="{grid}" clip-path="url(#{cid})" fill="none" stroke="{CODE}" stroke-width="4"/>')
    s.add(f'<path d="{figure}" fill="{GLOW}" stroke="{VOID}" stroke-width="6" paint-order="stroke"/>')
    s.add(f'<circle cx="503.5" cy="390" r="10" fill="{VOID}"/>')
    s.end()


def monitor(s, x, y):
    """A tiny pixel screen with a blinking prompt."""
    s.rect(x, y, 54, 40, PANEL, TEXT, 3, rx=3)
    s.rect(x + 6, y + 6, 42, 28, MOSS)
    s.text(x + 10, y + 26, ">", 14, GLOW, 700)
    s.rect(x + 22, y + 24, 9, 3, GLOW, extra='class="blink"')
    s.rect(x + 20, y + 40, 14, 6, TEXT)
    s.rect(x + 12, y + 46, 30, 4, TEXT)


def rain(s, x, y, w, h, seed=7):
    """Columns of falling code inside a clipped box; the lowest glyph of each column glows."""
    cid = s.uid("rc")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    rnd = random.Random(seed)
    step, line = 14, 14
    for c in range(int(w // step)):
        n = rnd.randint(10, 22)
        length = n * line
        dur = rnd.uniform(4.5, 9.5)
        s.g("rain", f"--from:{-length}px;--to:{h + 20}px;--d:{dur:.1f}s;--delay:-{rnd.uniform(0, dur):.1f}s")
        for k in range(n):
            ch = rnd.choice(RAIN_CHARS)
            head = k == n - 1
            op = 1 if head else 0.25 + 0.75 * k / n
            s.text(x + 3 + c * step, y + k * line, ch, 12, TEXT if head else CODE, 700 if head else 400, opacity=round(op, 2))
        s.end()
    s.add("</g>")


# ------------------------------------------------------------------ 1. the profile window
def profile():
    H = 424
    s = frame("Mitaro's profile: Omar, computer science student at MTUCI, backend and security, local-first.",
              H, "A retro profile window with the Campus logo (Atlas carrying a globe) as the avatar, likes and dislikes, and falling code.")
    # title bar
    box(s, 14, 14, W - 28, 38)
    s.text(32, 40, "×  −  +", 17, TEXT, 700)
    s.text(140, 38, "mitaro-cs", 14, TEXT)
    s.rect(690, 20, 170, 26, MOSS, GLOW, 1)
    s.add(f'<circle cx="706" cy="32" r="5" fill="none" stroke="{GLOW}" stroke-width="1.6"/>')
    s.line(710, 36, 714, 40, GLOW, 1.8)
    s.text(724, 38, "Search...", 13, GLOW)

    box(s, 14, 62, W - 28, H - 76)
    # left: handle, avatar, status
    s.text(30, 86, "@mitaro-cs", 13, TEXT, 700)
    s.rect(30, 96, 204, 204, s.gradient([(0, "#2f3b2c", 1), (1, VOID, 1)], 0, 0, 0, 1), LINE, 1.2)
    s.g("flick")
    campus_logo(s, 37, 103, 190)
    s.end()
    pid = s.uid("sl")
    s.defs.append(f'<pattern id="{pid}" width="4" height="3" patternUnits="userSpaceOnUse">'
                  f'<rect width="4" height="1" fill="#000" opacity=".35"/></pattern>')
    s.rect(31, 97, 202, 202, f"url(#{pid})")
    button(s, 52, 314, 160, 28, "receiving data...")
    dots(s, 30, 356, 204, 10)
    s.text(30, 390, f"online since {DATA['created'][:4]}", 12, MUTED)

    # middle: who
    x0 = 254
    s.text(x0, 90, "My Profile", 17, TEXT)
    s.line(x0, 94, x0 + text_width(17, "My Profile"), 94, TEXT, 1.2)
    s.text(x0, 120, "Omar", 13, TEXT, 700)
    s.text(x0 + text_width(13, "Omar "), 120, "or Mitaro,", 13, MUTED)
    s.text(x0, 139, "CS student @ MTUCI,", 13, MUTED)
    s.text(x0, 158, "backend + security,", 13, MUTED)
    s.text(x0, 177, "local-first nerd", 13, MUTED)
    button(s, x0 + 18, 192, 88, 26, "follow", 12)
    button(s, x0 + 116, 192, 88, 26, "campus", 12)
    dots(s, x0, 230, 266, 8)
    for i, (face, txt) in enumerate((("\\(^o^)/", "Java, Svelte, encryption, local-first apps, combat sports"),
                                     ("(-_-)", "cloud lock-in, clever code, plain-text passwords"))):
        y = 248 + i * 76
        s.rect(x0, y, 266, 66, PANEL, LINE, 1.2)
        s.rect(x0, y, 266, 22, "#241f1d", LINE, 1.2)
        s.text(x0 + 6, y + 16, face, 12, TEXT, 700)
        for j, ln in enumerate(wrap(txt, 12, 252)[:2]):
            s.text(x0 + 6, y + 40 + j * 16, ln, 12, TEXT)

    # right: the rain
    s.rect(542, 76, 318, 334, "#120f10", LINE, 1.2)
    rain(s, 543, 77, 316, 332)
    return s


# ------------------------------------------------------------------ 2. before you follow
def rules():
    H = 98
    f = facts()
    notes = [("BEFORE YOU FOLLOW", f"I commit at odd hours ({f['night']}% after 22:00), in Russian and English, "
                                   "mostly Java and Svelte."),
             ("DON'T FOLLOW IF", "you keep passwords in plain text, trust only the cloud, or think readable "
                                 "code is for beginners.")]
    s = frame(" ".join(f"{a}: {b}" for a, b in notes), H)
    for i, (head, txt) in enumerate(notes):
        x = 14 + i * 436
        box(s, x, 14, 424, H - 28)
        strip(s, x, 14, 424, head)
        for j, ln in enumerate(wrap(txt, 12, 408)[:3]):
            s.text(x + 8, 52 + j * 17, ln, 12, TEXT)
    return s


# ------------------------------------------------------------------ 3. interests and where to find me
INTERESTS = ["Campus, my study-group app", "Local-first software", "Security and cryptography", "Java + Spring Boot",
             "Svelte + Tauri", "Hand-to-hand combat", "A Jarvis-style AI assistant"]


def interests():
    H = 344
    f = facts()
    s = frame("Mitaro is online. My interests: " + ", ".join(INTERESTS) + ". Find me on Telegram, email, Instagram "
              "and GitHub.", H)
    box(s, 14, 14, W - 28, H - 28)
    s.line(444, 30, 444, H - 30, LINE, 1.2)

    # left: online sign and the list
    monitor(s, 70, 34)
    s.text(140, 56, "mitaro", 24, GLOW, 700)
    s.text(140, 84, "is online", 24, GLOW, 700)
    s.rect(140 + text_width(24, "is online") + 6, 64, 13, 22, GLOW, extra='class="blink"')
    s.text(229, 124, "MY INTERESTS", 16, TEXT, anchor="middle")
    s.rect(30, 136, 398, 24, PANEL, LINE, 1.2)
    s.line(358, 136, 358, 160, LINE, 1.2)
    s.text(194, 152, "MY INTERESTS", 12, TEXT, anchor="middle")
    s.text(393, 152, "<3", 12, TEXT, anchor="middle")
    for i, item in enumerate(INTERESTS):
        y = 184 + i * 22
        s.text(32, y, "☆ " + item, 12.5, TEXT)
        s.line(30, y + 7, 428, y + 7, DIM, 1)

    # right: where to find me and a status readout
    button(s, 584, 32, 150, 34, "FIND ME ON", 15)
    icons = ["telegram", "gmail", "instagram", "github"]
    x = 659 - (len(icons) * 28 + (len(icons) - 1) * 22) / 2
    for ic in icons:
        s.icon(ic, x, 86, 28, TEXT)
        x += 50
    status = [("status", "online"), ("last commit", f["last"]), ("best streak", f"{f['streak']} days"),
              ("night shift", f"{f['night']}%"), ("peak hour", f"{f['peak']:02d}:00"), ("best day", f["weekday"])]
    s.rect(474, 140, 370, 176, "#120f10", LINE, 1.2)
    for i, (k, v) in enumerate(status):
        y = 168 + i * 25
        lead = f"> {k} " + "." * (16 - len(k)) + " "
        s.text(488, y, lead, 13, MUTED)
        s.text(488 + text_width(13, lead), y, v, 13, GLOW if i == 0 else TEXT, 700 if i == 0 else 400)
    return s


# ------------------------------------------------------------------ 4. the Nokia: the pinned project
def nokia():
    H = 300
    r = pinned_repo()
    p = DATA.get("pin") or {}
    lcd = [f"CAMPUS {r.get('release') or ''}".strip(), "-" * 19,
           f"{p.get('java', '?')} java {p.get('svelte', '?')} ui".strip(),
           f"{p.get('tests', '?')} tests {p.get('migrations', '?')} db", f"{r['commits']} commits"]
    s = frame("Pinned project Campus, shown on a Nokia screen: " + ", ".join(lcd[2:]) + ". Follow the white rabbit.", H)
    box(s, 14, 14, W - 28, H - 28)
    s.line(444, 30, 444, H - 30, LINE, 1.2)

    # the phone, cut off by the box like a photo
    cid = s.uid("nc")
    s.defs.append(f'<clipPath id="{cid}"><rect x="15" y="15" width="428" height="{H - 30}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.rect(119, 30, 220, 320, s.gradient([(0, "#3d4448", 1), (1, "#1e2224", 1)], 0, 0, 0, 1), VOID, 2, rx=46)
    s.text(229, 62, "NOKIA", 15, TEXT, 700, anchor="middle", ls=1)
    s.rect(141, 76, 176, 150, "#151313", rx=12)
    s.rect(151, 86, 156, 130, LCD, rx=4)
    for i, ln in enumerate(lcd):
        s.text(159, 106 + i * 19, ln, 11.5, LCD_INK, 700)
    s.text(159, 208, "Options", 11.5, LCD_INK, 700)
    s.text(299, 208, "Back", 11.5, LCD_INK, 700, anchor="end")
    s.add('<ellipse cx="229" cy="256" rx="42" ry="14" fill="#4a5258" stroke="#0e0b0d" stroke-width="1.5"/>')
    for kx in (160, 298):
        s.add(f'<ellipse cx="{kx}" cy="252" rx="18" ry="8" fill="#33393c"/>')
    s.add("</g>")

    # the white rabbit
    s.rect(512, 104, 294, 40, PANEL, BRASS, 1.5, extra='stroke-dasharray="3 2"')
    sprite(s, RABBIT, 520, 110, 2.4, {"W": FRAME, "E": VOID})
    s.text(556, 129, "follow the white rabbit", 13, BRASS, 700)
    s.text(659, 186, "Campus is pinned. Open it.", 13, MUTED, anchor="middle")
    s.text(659, 220, "c u l8r", 18, TEXT, 700, anchor="middle")
    s.text(W - 34, H - 34, "( made with Python, not Carrd )", 11, MUTED, anchor="end")
    return s


# ------------------------------------------------------------------ 5. the terminal: numbers
def terminal():
    f = facts()
    langs = all_langs()
    repos = DATA["repos"]
    kb = sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k not in NOT_CODE) // 1000
    nums = [("repos", str(len(repos))), ("commits", str(sum(r["commits"] for r in repos))),
            ("stars", str(sum(r["stars"] for r in repos))), ("followers", str(DATA["followers"])),
            ("code", code_size(kb))]
    H = 392
    s = frame("Commit stats: activity over the last 26 weeks, commits by hour, " + ", ".join(f"{a} {b}" for a, b in nums)
              + ", code by language: " + ", ".join(k for k, _ in langs), H)
    box(s, 14, 14, W - 28, H - 28)
    cmd = "$ git log --stats --since=26.weeks"
    s.text(32, 44, cmd, 13, GLOW)
    s.rect(32 + text_width(13, cmd) + 6, 33, 8, 14, GLOW, extra='class="blink"')

    weeks, cell, gap = 26, 13, 3
    today = dt.datetime.now(MSK).date()
    start = today - dt.timedelta(days=today.weekday() + 7 * (weeks - 1))
    last_month = None
    for w in range(weeks):
        for d in range(7):
            day = start + dt.timedelta(days=7 * w + d)
            if day > today:
                continue
            n = f["per_day"].get(day, 0)
            s.rect(32 + w * (cell + gap), 64 + d * (cell + gap), cell, cell,
                   HEAT[0 if not n else 1 + (n >= 3) + (n >= 6) + (n >= 10)])
        first = start + dt.timedelta(days=7 * w)
        if first.month != last_month and w < weeks - 1:
            s.text(32 + w * (cell + gap), 196, MONTHS[first.month - 1], 11, MUTED)
            last_month = first.month

    hx, hw = 500, W - 32 - 500
    s.text(hx, 58, "commits by hour, moscow time", 11, MUTED)
    bw = (hw - 23 * 3) / 24
    top = max(f["hours"]) or 1
    for h, n in enumerate(f["hours"]):
        bh = max(2.0, 104 * n / top)
        s.rect(hx + h * (bw + 3), 176 - bh, bw, bh, GLOW if h in NIGHT_HOURS else CODE, opacity=1 if n else 0.3)
    for h in (0, 6, 12, 18):
        s.text(hx + h * (bw + 3), 196, f"{h:02d}", 11, MUTED)
    s.text(hx + hw, 196, "23", 11, MUTED, anchor="end")

    s.line(32, 214, W - 32, 214, DIM, 1.2)
    cw = (W - 64) / len(nums)
    for i, (a, b) in enumerate(nums):
        s.text(32 + i * cw, 242, a, 11, MUTED)
        s.text(32 + i * cw, 272, b, 24, TEXT, 700)
    s.text(32, 306, "code by language", 11, MUTED)
    total = sum(v for _, v in langs) or 1
    cx = 32
    for k, v in langs:
        seg = (W - 64) * v / total
        s.rect(cx, 316, max(0.0, seg - 2), 10, LANG_COLOR.get(k, LANG_COLOR["Other"]))
        cx += seg
    x = 32
    for k, v in langs:
        lab = f"{k} {round(100 * v / total)}%"
        if x + text_width(12, lab) + 18 > W - 32:
            break
        s.rect(x, 342, 9, 9, LANG_COLOR.get(k, LANG_COLOR["Other"]))
        s.text(x + 15, 351, lab, 12, TEXT)
        x += text_width(12, lab) + 32
    return s


if __name__ == "__main__":
    for name, fn in (("profile", profile), ("rules", rules), ("interests", interests), ("nokia", nokia),
                     ("terminal", terminal)):
        fn().save(OUT, f"{name}.svg")
