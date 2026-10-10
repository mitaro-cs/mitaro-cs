"""Shared helpers for the profile graphics: the park palette, text measuring, SVG builder.

Text uses the system font stack GitHub itself uses, so nothing is embedded. Widths are measured
with Liberation Sans advances (metric-compatible with Arial) from metrics.json, plus a little slack
for wider system fonts such as SF Pro.
"""
import json
import os
import re
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

# The park palette: a bench under plane trees on a bright day, and the same park after dusk.
LEAF_DEEP = "#2e4a33"   # shade under the canopy
LEAF = "#4f7d4a"        # leaves in the sun
LEAF_SOFT = "#9cbf86"   # young leaves
MEADOW = "#e4edd9"      # the lawn in light
MIST = "#f4f7ef"        # bright morning air
SKY = "#a9c8d6"         # sky between the trees
BARK = "#6b5a48"        # plane tree bark
BENCH = "#a8683f"       # the wooden bench
SAND = "#d9c79a"        # the gravel path
LAMP = "#e9a25f"        # a street lamp at dusk
DOG = "#3b302c"         # the little dog on the bench
FUR = "#f3efe8"         # its white crest
FOREST = "#1a2a20"      # the park after dusk
NIGHT = "#121b16"       # deepest shadow

METRICS = json.load(open(os.path.join(HERE, "metrics.json"), encoding="utf-8"))

ANIM_CSS = (
    "text{font-variant-numeric:tabular-nums}"
    "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}"
    ".rise{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    ".grow{transform-box:fill-box;transform-origin:0 50%;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes wag{0%,100%{transform:rotate(-14deg)}50%{transform:rotate(16deg)}}"
    ".wag{transform-box:fill-box;transform-origin:0 100%;animation:wag .7s ease-in-out infinite}"
    "@keyframes tilt{0%,62%,100%{transform:rotate(0)}70%,88%{transform:rotate(-9deg)}}"
    ".tilt{transform-box:fill-box;transform-origin:50% 90%;animation:tilt 5s ease-in-out infinite}"
    "@keyframes sway{0%,100%{transform:rotate(-.8deg)}50%{transform:rotate(.8deg)}}"
    ".sway{transform-box:fill-box;transform-origin:50% 100%;animation:sway 7s ease-in-out infinite}"
    "@keyframes glow{0%,100%{opacity:.85}50%{opacity:1}}"
    ".glow{animation:glow 3.2s ease-in-out infinite}"
    "@media (prefers-reduced-motion:reduce){[class]{animation:none!important}}"
)


def text_width(size, txt, weight=400, ls=0):
    m = METRICS["700" if weight >= 600 else "400"]
    return sum(m.get(ch, 560) for ch in txt) * size / 1000 * 1.05 + ls * len(txt)


def icon_path(name):
    """Returns the path data of a Simple Icons glyph (24x24 viewBox)."""
    svg = open(os.path.join(HERE, "icons", f"{name}.svg"), encoding="utf-8").read()
    return re.search(r'<path[^>]*\sd="([^"]+)"', svg).group(1)


class Svg:
    def __init__(self, w, h, title, desc=""):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.defs, self.body = [], []
        self._id = 0

    def uid(self, prefix="i"):
        self._id += 1
        return f"{prefix}{self._id}"

    def add(self, s):
        self.body.append(s)

    def gradient(self, stops, x1=0, y1=0, x2=1, y2=0, kind="linear"):
        gid = self.uid("g")
        st = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
        if kind == "linear":
            self.defs.append(f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{st}</linearGradient>')
        else:
            self.defs.append(f'<radialGradient id="{gid}" cx="{x1}" cy="{y1}" r="{x2}">{st}</radialGradient>')
        return f"url(#{gid})"

    def text(self, x, y, txt, size=16, fill=NIGHT, weight=400, anchor="start", ls=0, opacity=1):
        a = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"'
        if weight != 400:
            a += f' font-weight="{weight}"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if ls:
            a += f' letter-spacing="{ls}"'
        if opacity != 1:
            a += f' fill-opacity="{opacity}"'
        self.add(f"<text {a}>{escape(txt)}</text>")

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1, rx=0, opacity=1, extra=""):
        a = f'x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
        if rx:
            a += f' rx="{rx}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        self.add(f"<rect {a} {extra}/>")

    def circle(self, cx, cy, r, fill, opacity=1, extra=""):
        a = f'cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        self.add(f"<circle {a} {extra}/>")

    def path(self, d, fill="none", stroke=None, sw=1, opacity=1, extra=""):
        a = f'd="{d}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        self.add(f"<path {a} {extra}/>")

    def line(self, x1, y1, x2, y2, stroke, sw=1, opacity=1):
        a = f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"'
        if opacity != 1:
            a += f' stroke-opacity="{opacity}"'
        self.add(f"<line {a}/>")

    def icon(self, name, x, y, size, fill):
        self.add(f'<path d="{icon_path(name)}" fill="{fill}" '
                 f'transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})"/>')

    def g(self, cls="", style="", transform=""):
        a = f' class="{cls}"' if cls else ""
        a += f' style="{style}"' if style else ""
        a += f' transform="{transform}"' if transform else ""
        self.add(f"<g{a}>")

    def end(self):
        self.add("</g>")

    def render(self):
        desc = f"<desc>{escape(self.desc)}</desc>" if self.desc else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{escape(self.title)}" '
                f'font-family="{FONT}">'
                f"<title>{escape(self.title)}</title>{desc}<defs><style>{ANIM_CSS}</style>{''.join(self.defs)}</defs>"
                f"{''.join(self.body)}</svg>")

    def save(self, out_dir, name):
        data = self.render()
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(data)
        print(f"{name:26s}{len(data) / 1024:8.1f} KB")
