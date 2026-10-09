#!/usr/bin/env python3
"""Builds every SVG of the profile README into ../assets from scripts/data.json.

Light format: a few flat cards, no photos, no grain, small files. Every card is rendered twice,
`-light.svg` and `-dark.svg`, and the README picks one with <picture> so it follows GitHub's theme.
Palette rule: only the ten colours pulled from the avatar (lib.PALETTE).
Type: Instrument Serif for names, JetBrains Mono for everything that is data.
"""
import json
import os
import sys

from lib import (BENCH, CLAY, LEAF, MIST, NIGHT, PALETTE, SHADE, SHIRT, SKIN, STONE, WOOD, Svg, icon_path,
                 text_width)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(HERE, "data.json")))
W = 888

# one token set per GitHub theme, all from the avatar palette
THEMES = {
    "light": dict(bg=MIST, edge=STONE, ink=NIGHT, soft=BENCH, mute=WOOD, accent=CLAY, chip=MIST),
    "dark": dict(bg=SHADE, edge=BENCH, ink=MIST, soft=STONE, mute=STONE, accent=SKIN, chip=NIGHT),
}
# (light, dark) colour of each language
LANG_COLOR = {"Java": (CLAY, SKIN), "Svelte": (SKIN, CLAY), "Python": (SHIRT, SHIRT), "TypeScript": (LEAF, MIST),
              "JavaScript": (STONE, STONE), "CSS": (WOOD, WOOD), "HTML": (BENCH, LEAF), "Other": (SHADE, BENCH)}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CODE_REPOS = [r for r in DATA["repos"] if r["name"] != "mitaro-cs"]   # the profile repo only holds the generator
CODE_LANGS = ["Java", "Python", "Svelte", "TypeScript", "JavaScript", "CSS", "HTML"]
NOT_CODE = {"Rich Text Format"}
PIN_NAMES = ("campus", "storagesystem")   # Campus was called StorageSystem before the rename
REPO_NAMES = {"campus": "Campus", "storagesystem": "Campus", "kworkingsystem": "Kworking"}


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


def fit(txt, key, weight, size, maxw):
    """Cuts a line to maxw px, ending it with an ellipsis when it had to cut."""
    if text_width(key, weight, size, txt) <= maxw:
        return txt
    while txt and text_width(key, weight, size, txt + "…") > maxw:
        txt = txt[:-1]
    return txt.rstrip() + "…"


# ------------------------------------------------------------------ shared drawing bits
def card(t, h, title):
    s = Svg(W, h, title)
    s.rect(1, 1, W - 2, h - 2, t["bg"], t["edge"], 1.5, 14)
    return s


def kicker(s, x, y, txt, fill, size=11, anchor="start"):
    """Small spaced capitals: the voice of every label."""
    s.text(x, y, txt, "mono", size, fill, 700, anchor=anchor, ls=2.6)


def lang_bar(s, t, theme, x, y, w, h, langs):
    total = sum(v for _, v in langs) or 1
    cid = s.uid("lb")
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}"/></clipPath>')
    s.add(f'<g clip-path="url(#{cid})">')
    s.g("grow", "animation-delay:.3s")
    cx = x
    for k, v in langs:
        seg = w * v / total
        s.rect(cx, y, max(0.0, seg - 2), h, LANG_COLOR.get(k, LANG_COLOR["Other"])[theme == "dark"])
        cx += seg
    s.end()
    s.add("</g>")
    return total


def both(fn, name):
    for theme, t in THEMES.items():
        fn(t, theme).save(OUT, f"{name}-{theme}.svg")


# ------------------------------------------------------------------ header
def header(t, theme):
    H = 168
    s = card(t, H, "Mitaro. Omar, computer science student at MTUCI. Builds local-first software.")
    s.g("rise")
    kicker(s, 36, 46, "OMAR  ·  MTUCI  ·  COMPUTER SCIENCE", t["mute"])
    s.text(32, 132, "Mitaro", "serif", 92, t["ink"])
    s.end()
    x = 32 + text_width("serif", 400, 92, "Mitaro") + 36
    s.line(x - 18, 76, x - 18, 134, t["edge"], 1.5)
    s.g("rise", "animation-delay:.15s")
    s.text(x, 102, "I build local-first software:", "serif", 27, t["ink"])
    s.text(x, 132, "your data stays on your machine.", "serif", 27, t["accent"])
    s.end()
    for i, (_, c) in enumerate(PALETTE):     # the avatar's colours, a quiet signature
        s.add(f'<circle cx="{W - 40 - (len(PALETTE) - 1 - i) * 15}" cy="42" r="5" fill="{c}" '
              f'stroke="{t["edge"]}" stroke-width="1"/>')
    return s


# ------------------------------------------------------------------ pinned project
PIN = dict(
    name="Campus",
    tag="A study-group site and app that lives on the group leader's own computer.",
    feats=["Works offline, syncs when the host is back on",
           "Schedule straight from an .ics calendar file",
           "Files encrypted on disk with AES-256-GCM",
           "Sign in with a passkey, fingerprint or face",
           "Live updates and push for new homework",
           "Host app for Windows and macOS, one-click updates"],
    stack=["Java", "Spring Boot", "Svelte", "Tauri"],
    platforms="Windows · macOS · iPhone · Android",
    license="AGPL-3.0",
)


def pinned(t, theme):
    r = pinned_repo()
    H = 318
    s = card(t, H, f"Pinned: {PIN['name']}. {PIN['tag']}")
    s.add(f'<path d="{icon_path("pin")}" fill="{t["accent"]}" transform="translate(34 30) scale(.67)"/>')
    kicker(s, 56, 44, "PINNED PROJECT", t["accent"])
    kicker(s, W - 36, 44, PIN["platforms"].upper(), t["mute"], 10.5, anchor="end")
    s.g("rise")
    s.text(32, 106, PIN["name"], "serif", 62, t["ink"])
    s.end()
    s.text(36, 138, PIN["tag"], "serif", 22, t["soft"])
    colw = (W - 72) / 2
    for i, f in enumerate(PIN["feats"]):
        x, y = 36 + (i % 2) * colw, 178 + (i // 2) * 28
        s.g("rise", f"animation-delay:{0.1 + i * 0.06:.2f}s")
        s.text(x, y, "—", "mono", 13, t["accent"], 700)
        s.text(x + 22, y, f, "mono", 13, t["ink"], 500)
        s.end()
    s.line(36, 252, W - 36, 252, t["edge"], 1.2)
    meta = [("RELEASE", r.get("release") or "—"), ("COMMITS", str(r["commits"])), ("LICENSE", PIN["license"])]
    x = 36
    for a, b in meta:
        kicker(s, x, 276, a, t["mute"], 10)
        s.text(x, 300, b, "mono", 15, t["ink"], 700)
        x += max(text_width("mono", 700, 15, b), text_width("mono", 700, 10, a, 2.6)) + 34
    cx = W - 36
    for k in reversed(PIN["stack"]):
        tw = text_width("mono", 700, 11.5, k) + 22
        cx -= tw
        s.rect(cx, 278, tw, 26, t["chip"], t["edge"], 1.2, 13)
        s.text(cx + tw / 2, 295.5, k, "mono", 11.5, t["soft"], 700, anchor="middle")
        cx -= 8
    return s


# ------------------------------------------------------------------ numbers and languages
def numbers(t, theme):
    repos = DATA["repos"]
    kb = sum(v for r in CODE_REPOS for k, v in r["langs"].items() if k not in NOT_CODE) // 1000
    items = [("REPOS", str(len(repos))), ("COMMITS", str(sum(r["commits"] for r in repos))),
             ("STARS", str(sum(r["stars"] for r in repos))), ("FOLLOWERS", str(DATA["followers"])),
             ("CODE", code_size(kb))]
    langs = all_langs()
    H = 222 + (len(langs) - 1) // 4 * 24
    s = card(t, H, "GitHub in numbers: " + ", ".join(f"{a} {b}" for a, b in items)
             + ". Code by language: " + ", ".join(k for k, _ in langs))
    cw = (W - 72) / len(items)
    for i, (a, b) in enumerate(items):
        x = 36 + i * cw
        s.g("rise", f"animation-delay:{i * 0.07:.2f}s")
        kicker(s, x, 44, a, t["accent"] if i == 1 else t["mute"], 10.5)
        s.text(x - 2, 92, b, "serif", 46, t["ink"])
        s.end()
    kicker(s, 36, 142, "CODE BY LANGUAGE", t["mute"], 10.5)
    total = lang_bar(s, t, theme, 36, 154, W - 72, 10, langs)
    for i, (k, v) in enumerate(langs):
        x, y = 36 + (i % 4) * (W - 72) / 4, 192 + (i // 4) * 24
        s.add(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{LANG_COLOR.get(k, LANG_COLOR["Other"])[theme == "dark"]}" '
              f'stroke="{t["edge"]}" stroke-width="1"/>')
        s.text(x + 17, y, k, "mono", 12.5, t["ink"], 600)
        s.text(x + 17 + text_width("mono", 600, 12.5, k + " "), y, f"{round(100 * v / total)}%", "mono", 12.5,
               t["mute"], 500)
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
        w = text_width("mono", 600, 12.5, name) + 50
        if x + w > W - 36:
            x, y = 36, y + 44
        chips.append((x, y, w, ic, name, hot))
        x += w + 8
    H = y + 34 + 28
    s = card(t, H, "Tech stack: " + ", ".join(n for _, n, _ in STACK))
    kicker(s, 36, 44, "TOOLKIT", t["mute"], 10.5)
    kicker(s, W - 36, 44, "DAILY DRIVERS FIRST", t["mute"], 10.5, anchor="end")
    for i, (x, y, w, ic, name, hot) in enumerate(chips):
        s.g("rise", f"animation-delay:{i * 0.03:.2f}s")
        s.rect(x, y, w, 34, t["chip"], t["accent"] if hot else t["edge"], 1.3, 17)
        s.icon(ic, x + 14, y + 9, 16, t["accent"] if hot else t["soft"])
        s.text(x + 38, y + 22, name, "mono", 12.5, t["ink"], 600)
        s.end()
    return s


# ------------------------------------------------------------------ latest commits
def commits(t, theme):
    rows = [c for c in DATA["commits"] if not c["msg"].startswith(("Initial commit", "Merge "))][:6]
    H = 70 + len(rows) * 34 + 14
    s = card(t, H, "Latest commits: " + "; ".join(c["msg"] for c in rows))
    kicker(s, 36, 44, "LATEST COMMITS", t["mute"], 10.5)
    kicker(s, W - 36, 44, "UPDATES EVERY 6 HOURS", t["mute"], 10.5, anchor="end")
    for i, c in enumerate(rows):
        y = 84 + i * 34
        if i:
            s.line(36, y - 22, W - 36, y - 22, t["edge"], 1, opacity=0.6)
        _, m, d = c["ts"][:10].split("-")
        repo = REPO_NAMES.get(c["repo"].lower(), c["repo"])
        s.g("rise", f"animation-delay:{i * 0.06:.2f}s")
        s.text(36, y, f"{d} {MONTHS[int(m) - 1]}", "mono", 12.5, t["mute"], 600)
        s.text(110, y, fit(repo, "mono", 700, 12.5, 128), "mono", 12.5, t["accent"], 700)
        s.text(256, y, fit(c["msg"], "mono", 500, 13, W - 36 - 256), "mono", 13, t["ink"], 500)
        s.end()
    return s


if __name__ == "__main__":
    both(header, "header")
    both(pinned, "pinned")
    both(numbers, "numbers")
    both(stack, "stack")
    both(commits, "commits")
