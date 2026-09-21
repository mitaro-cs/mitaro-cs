"""1-bit pixel-art panels: the Obsidian home dashboard redrawn as an old Macintosh window."""
import json
import os
import random
from datetime import date

from lib import BLACK, WHITE, Svg, jag, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITE = [ln for ln in open(os.path.join(HERE, "src", "sprite.txt")).read().split("\n") if ln]
VAULT = json.load(open(os.path.join(HERE, "vault.json")))

DIGITS = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}
CURSOR = [
    "X", "XX", "XoX", "XooX", "XoooX", "XooooX", "XoooooX", "XooooooX", "XoooooooX", "XooooooooX",
    "XoooooXXXXX", "XooXooX", "XoX.XooX", "XX..XooX", "X....XooX", ".....XooX", "......XX",
]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def runs_path(rows, x, y, u, on="#"):
    """Path data for a bitmap: horizontal runs of `on` cells become one rect each."""
    d = []
    for j, row in enumerate(rows):
        i = 0
        while i < len(row):
            if row[i] == on:
                k = i
                while k < len(row) and row[k] == on:
                    k += 1
                d.append(f"M{x + i * u} {y + j * u}h{(k - i) * u}v{u}h-{(k - i) * u}z")
                i = k
            else:
                i += 1
    return "".join(d)


def bitmap(s, rows, x, y, u, fill=BLACK, on="#"):
    s.add(f'<path d="{runs_path(rows, x, y, u, on)}" fill="{fill}" shape-rendering="crispEdges"/>')


def px_text(s, x, y, txt, size=16, fill=BLACK, key="px", anchor="start"):
    s.text(x, y, txt, key, size, fill, 400, anchor=anchor)


def box(s, x, y, w, h, fill=WHITE, stroke=BLACK, sw=2):
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
          'shape-rendering="crispEdges"/>')


def block(s, x, y, w, h, fill=BLACK):
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" shape-rendering="crispEdges"/>')


def dither_patterns(s):
    s.defs.append(
        f'<pattern id="d25" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="{WHITE}"/>'
        f'<rect width="2" height="2" fill="{BLACK}"/></pattern>'
        f'<pattern id="d50" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="{WHITE}"/>'
        f'<rect width="2" height="2" fill="{BLACK}"/><rect x="2" y="2" width="2" height="2" fill="{BLACK}"/></pattern>'
        f'<pattern id="d75" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="{BLACK}"/>'
        f'<rect x="2" y="2" width="2" height="2" fill="{WHITE}"/></pattern>'
    )


def poster(s, x, y, w, h, kind):
    s.defs.append(f'<clipPath id="pc{kind}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
    s.add(f'<g clip-path="url(#pc{kind})" shape-rendering="crispEdges">')
    block(s, x, y, w, h, WHITE)
    if kind == 0:                                   # sun over the sea
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h * 0.62}" fill="url(#d25)"/>')
        s.add(f'<circle cx="{x + w / 2}" cy="{y + h * 0.5}" r="{w * 0.27}" fill="{WHITE}" stroke="{BLACK}" stroke-width="2"/>')
        s.add(f'<rect x="{x}" y="{y + h * 0.62}" width="{w}" height="{h * 0.38}" fill="url(#d75)"/>')
        for k in range(3):
            block(s, x, y + h * 0.7 + k * 8, w, 2, WHITE)
    elif kind == 1:                                 # mountains
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#d50)"/>')
        s.add(f'<polygon points="{x},{y + h} {x + w * 0.36},{y + h * 0.28} {x + w * 0.7},{y + h}" fill="{BLACK}"/>')
        s.add(f'<polygon points="{x + w * 0.42},{y + h} {x + w * 0.74},{y + h * 0.46} {x + w + 4},{y + h}" fill="{WHITE}" stroke="{BLACK}" stroke-width="2"/>')
    else:                                           # skyline
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#d25)"/>')
        r = random.Random(7)
        cx = x
        while cx < x + w:
            bw = r.choice([10, 12, 14])
            bh = r.randint(int(h * 0.3), int(h * 0.75))
            block(s, cx, y + h - bh, bw, bh, BLACK)
            for wy in range(y + h - bh + 4, y + h - 4, 8):
                block(s, cx + 3, wy, 2, 2, WHITE)
                if bw > 10:
                    block(s, cx + 8, wy, 2, 2, WHITE)
            cx += bw + 2
    s.add("</g>")
    box(s, x, y, w, h, "none")


def panel_head(s, x, y, w, title, right=None):
    block(s, x + 12, y + 14, 8, 8)
    px_text(s, x + 28, y + 24, title, 16, BLACK, "pxb")
    if right:
        px_text(s, x + w - 12, y + 24, right, 16, BLACK, "px", "end")


def obsidian_window(out_dir, commits):
    W, H = 888, 552
    today = date.today()
    s = Svg(W, H, "Pixel-art sketch of my Obsidian home dashboard, drawn as an old Macintosh window")
    dither_patterns(s)
    s.extra_css = (
        "@keyframes bk{0%,49%{opacity:1}50%,100%{opacity:0}}.blinkc{animation:bk 1s steps(1) infinite}"
        "@keyframes secs{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
        ".secs{transform-box:fill-box;transform-origin:100% 50%;animation:secs 60s steps(60,end) infinite}"
        "@keyframes cur{0%{transform:translate(430px,262px)}14%{transform:translate(120px,282px)}"
        "28%{transform:translate(520px,262px)}42%{transform:translate(150px,446px)}"
        "56%{transform:translate(600px,440px)}72%{transform:translate(770px,300px)}86%,100%{transform:translate(430px,262px)}}"
        ".cur{animation:cur 18s steps(20) infinite}"
    )
    # window + hard shadow
    block(s, 16, 16, 866, 524, BLACK)
    box(s, 6, 6, 866, 524, WHITE, BLACK, 3)
    # title bar: horizontal stripes, centered title tile, close box
    for yy in range(12, 36, 4):
        block(s, 9, yy, 860, 2, BLACK)
    title = "HOME / EQ CORE"
    tw_ = text_width("pxb", 400, 16, title) + 32
    block(s, 439 - tw_ / 2, 10, tw_, 24, WHITE)
    px_text(s, 439, 28, title, 16, BLACK, "pxb", "middle")
    box(s, 20, 12, 18, 18, WHITE, BLACK, 2)
    block(s, 6, 38, 866, 2)

    # ---------------------------------------------------------------- row A
    ay, ah = 52, 124
    # sticker heading with the day-of-year meter
    doy = today.timetuple().tm_yday
    block(s, 22, ay, 176, ah)
    px_text(s, 36, ay + 44, "HOME", 24, WHITE, "ps")
    px_text(s, 36, ay + 76, f"DAY {doy}/365", 16, WHITE)
    box(s, 36, ay + 90, 148, 14, BLACK, WHITE, 2)
    block(s, 39, ay + 93, round(142 * doy / 365), 8, WHITE)
    # clock
    box(s, 210, ay, 206, ah)
    px_text(s, 224, ay + 24, "CLOCK", 16)
    cx = 224
    for ch in "12:00":
        if ch == ":":
            s.g("blinkc")
            block(s, cx + 5, ay + 66, 5, 5)
            block(s, cx + 5, ay + 84, 5, 5)
            s.end()
            cx += 20
        else:
            bitmap(s, DIGITS[ch], cx, ay + 46, 5, BLACK, "1")
            cx += 34
    cover_x = 224
    for i in range(60):
        block(s, cover_x + i * 3, ay + 100, 2, 10)
    s.add(f'<rect class="secs" x="{cover_x - 1}" y="{ay + 98}" width="182" height="14" fill="{WHITE}"/>')
    # dot calendar of the current month, marked with the days I pushed commits
    box(s, 428, ay, 252, ah)
    px_text(s, 442, ay + 24, f"ACTIVE {MONTHS[today.month - 1]}", 16)
    marked = {c["ts"][:10] for c in commits}
    first = date(today.year, today.month, 1)
    nxt = date(today.year + (today.month == 12), today.month % 12 + 1, 1)
    ndays = (nxt - first).days
    for d in range(1, ndays + 1):
        pos = first.weekday() + d - 1
        gx, gy = 442 + (pos % 7) * 32, ay + 38 + (pos // 7) * 16
        iso = date(today.year, today.month, d).isoformat()
        if d == today.day:
            block(s, gx, gy, 12, 12)
            s.g("blinkc")
            box(s, gx - 3, gy - 3, 18, 18, "none", BLACK, 2)
            s.end()
        elif iso in marked:
            block(s, gx, gy, 12, 12)
        elif d < today.day:
            box(s, gx + 1, gy + 1, 10, 10, "none", BLACK, 2)
        else:
            block(s, gx + 5, gy + 5, 2, 2)

    # ---------------------------------------------------------------- row B
    by, bh = 188, 172
    box(s, 22, by, 322, bh)
    panel_head(s, 22, by, 322, "STUDY", "3/5 THIS WEEK")
    names = ["SUBJECT 01", "SUBJECT 02", "SUBJECT 03", "SUBJECT 04", "SUBJECT 05"]
    counts = ["24", "18", "31", "12", "9"]
    fresh = [True, True, False, True, False]
    for i, (n, c, f) in enumerate(zip(names, counts, fresh)):
        ry = by + 50 + i * 24
        box(s, 36, ry - 12, 14, 14, WHITE, BLACK, 2)
        if f:
            bitmap(s, ["1...1", ".1.1.", "..1..", ".1.1.", "1...1"], 39, ry - 9, 2, BLACK, "1")
        px_text(s, 62, ry, n, 16)
        px_text(s, 330, ry, c, 16, BLACK, "pxb", "end")
    box(s, 356, by, 324, bh)
    panel_head(s, 356, by, 324, "RECENT")
    kinds = [("LEC", "NOTE 01", "TODAY"), ("LAB", "NOTE 02", "TODAY"), ("PRA", "NOTE 03", "1D AGO"),
             ("LEC", "NOTE 04", "2D AGO"), ("PRA", "NOTE 05", "4D AGO")]
    for i, (k, n, ago) in enumerate(kinds):
        ry = by + 50 + i * 24
        block(s, 370, ry - 14, 44, 18)
        px_text(s, 392, ry, k, 16, WHITE, "px", "middle")
        px_text(s, 426, ry, n, 16)
        px_text(s, 666, ry, ago, 16, BLACK, "px", "end")

    # ---------------------------------------------------------------- row C
    cy, chh = 372, 116
    box(s, 22, cy, 456, chh)
    panel_head(s, 22, cy, 456, "WATCHING", "CINEMA >")
    for i, (k, badge) in enumerate([(0, "S1 E4"), (1, "S2 E1"), (2, "S3 E7")]):
        px_x = 36 + i * 148
        poster(s, px_x, cy + 40, 54, 66, k)
        block(s, px_x + 62, cy + 44, 68, 20)
        px_text(s, px_x + 96, cy + 60, badge, 16, WHITE, "px", "middle")
    box(s, 490, cy, 190, chh)
    stats = [(str(VAULT["notes"]), "NOTES"), (str(VAULT["sections"]), "FOLDERS"),
             (str(VAULT["community_plugins"]), "PLUGINS"), (str(VAULT["css_lines"]), "CSS")]
    for i, (n, lab) in enumerate(stats):
        sx, sy = 498 + (i % 2) * 92, cy + 8 + (i // 2) * 54
        block(s, sx, sy, 88, 48)
        px_text(s, sx + 44, sy + 24, n, 16, WHITE, "ps", "middle")
        px_text(s, sx + 44, sy + 42, lab, 16, WHITE, "px", "middle")

    # ---------------------------------------------------------------- avatar card
    box(s, 694, ay, 176, 308)
    px_text(s, 708, ay + 24, "OWNER", 16)
    bitmap(s, SPRITE, 702, ay + 34, 2)
    px_text(s, 782, ay + 260, "OMAR", 24, BLACK, "ps", "middle")
    px_text(s, 782, ay + 290, "AKA MITARO", 16, BLACK, "pxb", "middle")
    # what the dashboard runs on
    box(s, 694, cy, 176, chh)
    panel_head(s, 694, cy, 176, "BUILT ON")
    for i, name in enumerate(["DATACORE", "DYNAMIC VIEWS", "BASES", "KANBAN"]):
        px_text(s, 708, cy + 50 + i * 18, name, 16)

    # ---------------------------------------------------------------- link pills
    lx = 22
    for lab in ["PLANNER", "CINEMA", "VAULT MAP", "KNOWLEDGE", "CONFIG"]:
        w_ = text_width("px", 400, 16, lab) + 24
        box(s, lx, 498, w_, 24, WHITE, BLACK, 2)
        px_text(s, lx + w_ / 2, 516, lab, 16, BLACK, "px", "middle")
        lx += w_ + 10
    px_text(s, 860, 516, "SAMPLE DATA", 16, BLACK, "px", "end")

    # cursor on top
    s.add('<g class="cur">')
    bitmap(s, CURSOR, 0, 0, 2, WHITE, "o")
    bitmap(s, CURSOR, 0, 0, 2, BLACK, "X")
    s.add("</g>")
    s.save(out_dir, "obsidian.svg")
