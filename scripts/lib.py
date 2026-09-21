"""Shared helpers for the profile graphics: font embedding, zine-style shapes, SVG builder."""
import base64
import io
import math
import os
import random
import re
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
BLACK = "#000"
WHITE = "#fff"

FONTS = {
    "anton": ("Anton-Regular.ttf", "Anton", "Impact, 'Arial Narrow Bold', sans-serif"),
    "bebas": ("BebasNeue-Regular.ttf", "Bebas", "Impact, sans-serif"),
    "elite": ("SpecialElite-Regular.ttf", "Elite", "'Courier New', monospace"),
    "marker": ("PermanentMarker-Regular.ttf", "Marker", "'Marker Felt', cursive"),
    "play": ("PlayfairDisplay[wght].ttf", "Play", "Georgia, serif"),
    "mono": ("JetBrainsMono[wght].ttf", "JBMono", "ui-monospace, Menlo, Consolas, monospace"),
    "px": ("Silkscreen-Regular.ttf", "Silk", "monospace"),
    "pxb": ("Silkscreen-Bold.ttf", "SilkB", "monospace"),
    "ps": ("PressStart2P-Regular.ttf", "PS2P", "monospace"),
}

_cache = {}

ANIM_CSS = (
    ".o{transform-box:fill-box;transform-origin:center}"
    "@keyframes wob{0%{transform:rotate(calc(var(--a,1.3deg)*-1)) translate(0,0)}"
    "34%{transform:rotate(calc(var(--a,1.3deg)*.8)) translate(.8px,-.7px)}"
    "67%{transform:rotate(calc(var(--a,1.3deg)*-.4)) translate(-.7px,.6px)}}"
    ".wob{animation:wob var(--d,1s) steps(1) infinite}"
    "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}"
    ".bob{animation:bob 3.4s ease-in-out infinite}"
    "@keyframes sway{0%,100%{transform:rotate(-1.5deg)}50%{transform:rotate(1.5deg)}}"
    ".sway{transform-origin:50% 0;animation:sway 5.5s ease-in-out infinite}"
    "@keyframes pop{0%{transform:scale(.7) rotate(-7deg)}65%{transform:scale(1.07) rotate(1.2deg)}"
    "100%{transform:scale(1) rotate(0deg)}}"
    ".pop{animation:pop .6s cubic-bezier(.2,1.3,.4,1) both}"
    "@keyframes grow{from{transform:scaleX(.15)}to{transform:scaleX(1)}}"
    ".grow{transform-origin:0 50%;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes rise{from{transform:translateY(10px)}to{transform:translateY(0)}}"
    ".rise{animation:rise .6s ease-out both}"
    "@keyframes spin{to{transform:rotate(360deg)}}"
    ".spin{animation:spin 9s linear infinite}"
    "@keyframes draw{from{stroke-dashoffset:calc(var(--len)*.86)}to{stroke-dashoffset:0}}"
    ".draw{stroke-dasharray:var(--len);animation:draw 1.6s ease-out both}"
    "@keyframes marq{to{transform:translateX(var(--shift))}}"
    ".marq{animation:marq 18s linear infinite}"
    "@keyframes fA{0%,49.99%{opacity:1}50%,100%{opacity:0}}@keyframes fB{0%,49.99%{opacity:0}50%,100%{opacity:1}}"
    ".fA{animation:fA .8s steps(1) infinite}.fB{animation:fB .8s steps(1) infinite}"
    "@keyframes sweep{0%{transform:translateX(0)}42%,100%{transform:translateX(1400px)}}"
    ".sweep{animation:sweep 9s ease-in-out infinite}"
    "@media (prefers-reduced-motion:reduce){[class]{animation:none!important}}"
)


def font(key, weight=400):
    ck = (key, weight)
    if ck not in _cache:
        f = TTFont(os.path.join(HERE, "fonts", FONTS[key][0]))
        if "fvar" in f:
            f = instancer.instantiateVariableFont(f, {"wght": weight})
        _cache[ck] = f
    return _cache[ck]


def text_width(key, weight, size, txt, ls=0):
    f = font(key, weight)
    cmap, hm, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    total = 0
    for ch in txt:
        g = cmap.get(ord(ch), ".notdef")
        total += hm[g][0] if g in hm.metrics else hm[".notdef"][0]
    return total * size / upm + ls * len(txt)


def ink_bounds(key, weight, size, ch):
    """Real ink box of a glyph in px, y up: (xmin, ymin, xmax, ymax). Font metrics lie, outlines do not."""
    f = font(key, weight)
    gs = f.getGlyphSet()
    name = f.getBestCmap()[ord(ch)]
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    k = size / f["head"].unitsPerEm
    xmin, ymin, xmax, ymax = pen.bounds
    return xmin * k, ymin * k, xmax * k, ymax * k


def cap_height(key, weight, size):
    return ink_bounds(key, weight, size, "H")[3]


def _woff2_b64(key, weight, chars):
    tmp = io.BytesIO()
    font(key, weight).save(tmp)
    tmp.seek(0)
    f = TTFont(tmp)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk"]
    opts.notdef_outline = True
    opts.name_IDs = [1, 2]
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)) + " ")
    sub.subset(f)
    f.flavor = "woff2"
    buf = io.BytesIO()
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def jag(x, y, w, h, j=2.4, seed=1, step=15):
    """Polygon points for a hand-cut rectangle: every edge is subdivided and jittered."""
    r = random.Random(seed)
    pts = []

    def edge(x1, y1, x2, y2):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) // step))
        for i in range(n):
            t = i / n
            pts.append((x1 + (x2 - x1) * t + r.uniform(-j, j), y1 + (y2 - y1) * t + r.uniform(-j, j)))

    edge(x, y, x + w, y)
    edge(x + w, y, x + w, y + h)
    edge(x + w, y + h, x, y + h)
    edge(x, y + h, x, y)
    return " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)


def star_points(cx, cy, r_out, r_in, n=9, rot=0):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi * i / n + rot
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return " ".join(pts)


def icon_path(name):
    """Returns the path data of a Simple Icons glyph (24x24 viewBox)."""
    svg = open(os.path.join(HERE, "icons", f"{name}.svg"), encoding="utf-8").read()
    return re.search(r'<path[^>]*\sd="([^"]+)"', svg).group(1)


class Svg:
    def __init__(self, w, h, title, desc=""):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.defs, self.body, self.used = [], [], {}
        self.extra_css = ""
        self._id = 0

    def uid(self, prefix="i"):
        self._id += 1
        return f"{prefix}{self._id}"

    def add(self, s):
        self.body.append(s)

    def gradient(self, stops, x1=0, y1=0, x2=1, y2=0, units="objectBoundingBox", kind="linear", extra=""):
        gid = self.uid("g")
        st = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
        if kind == "linear":
            self.defs.append(f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                             f'gradientUnits="{units}">{st}</linearGradient>')
        else:
            self.defs.append(f'<radialGradient id="{gid}" cx="{x1}" cy="{y1}" r="{x2}" '
                             f'gradientUnits="{units}" {extra}>{st}</radialGradient>')
        return f"url(#{gid})"

    def text(self, x, y, txt, key="mono", size=16, fill=WHITE, weight=400, anchor="start", ls=0,
             opacity=1, transform=None, extra=""):
        self.used.setdefault((key, weight), set()).update(txt)
        _, fam, fb = FONTS[key]
        a = (f'x="{x:.1f}" y="{y:.1f}" font-family="{fam}, {fb}" font-size="{size}" '
             f'font-weight="{weight}" fill="{fill}"')
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if ls:
            a += f' letter-spacing="{ls}"'
        if opacity != 1:
            a += f' fill-opacity="{opacity}"'
        if transform:
            a += f' transform="{transform}"'
        self.add(f"<text {a} {extra}>{escape(txt)}</text>")

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1, rx=0, opacity=1, transform=None, extra=""):
        a = f'x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
        if rx:
            a += f' rx="{rx}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        if transform:
            a += f' transform="{transform}"'
        self.add(f"<rect {a} {extra}/>")

    def poly(self, pts, fill="none", stroke=None, sw=1, opacity=1, transform=None, extra=""):
        a = f'points="{pts}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        if transform:
            a += f' transform="{transform}"'
        self.add(f"<polygon {a} {extra}/>")

    def path(self, d, fill="none", stroke=None, sw=1, opacity=1, transform=None, extra=""):
        a = f'd="{d}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        if transform:
            a += f' transform="{transform}"'
        self.add(f"<path {a} {extra}/>")

    def line(self, x1, y1, x2, y2, stroke=WHITE, sw=1, opacity=1, dash=None):
        a = f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"'
        if opacity != 1:
            a += f' stroke-opacity="{opacity}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.add(f"<line {a}/>")

    def icon(self, name, x, y, size, fill=WHITE):
        self.add(f'<path d="{icon_path(name)}" fill="{fill}" '
                 f'transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})"/>')

    def g(self, cls="", style=""):
        self.add(f'<g class="{cls}"' + (f' style="{style}"' if style else "") + ">")

    def end(self):
        self.add("</g>")

    def grain(self, opacity=0.09, w=None, h=None, seed=3):
        self.defs.append(
            '<filter id="grain" x="0" y="0" width="100%" height="100%">'
            f'<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="{seed}" stitchTiles="stitch">'
            '<animate attributeName="seed" values="3;9;14;6;21;11" dur=".7s" calcMode="discrete" repeatCount="indefinite"/>'
            "</feTurbulence>"
            '<feColorMatrix type="matrix" values=".33 .33 .33 0 0 .33 .33 .33 0 0 .33 .33 .33 0 0 0 0 0 1 0"/>'
            "</filter>")
        self.add(f'<rect width="{w or self.w}" height="{h or self.h}" filter="url(#grain)" opacity="{opacity}"/>')

    def render(self):
        faces = []
        for (key, weight), chars in sorted(self.used.items()):
            fam = FONTS[key][1]
            faces.append(f"@font-face{{font-family:{fam};font-weight:{weight};"
                         f"src:url(data:font/woff2;base64,{_woff2_b64(key, weight, chars)}) format('woff2');}}")
        style = "".join(faces) + ANIM_CSS + self.extra_css
        desc = f"<desc>{escape(self.desc)}</desc>" if self.desc else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{escape(self.title)}">'
                f"<title>{escape(self.title)}</title>{desc}<defs><style>{style}</style>{''.join(self.defs)}</defs>"
                f"{''.join(self.body)}</svg>")

    def save(self, out_dir, name):
        data = self.render()
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(data)
        print(f"{name:26s}{len(data) / 1024:8.1f} KB")
