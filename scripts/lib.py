"""Shared helpers for the profile graphics: the avatar palette, font embedding, SVG builder."""
import base64
import io
import os
import re
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
# Palette: every colour is a k-means cluster or region mean of the avatar's pixels
# (a man on a park bench, muted 35mm look). Nothing outside this list is drawn.
NIGHT = "#0e0b0d"    # deepest shadow under the bench
SHADE = "#1a1718"    # shade between the planks
BENCH = "#37302e"    # weathered bench wood
WOOD = "#6c6662"     # sunlit plank grey
STONE = "#bdaea3"    # khaki trousers
MIST = "#e3eeef"     # highlight on the shirt
SHIRT = "#a2bbc5"    # the pale blue shirt
SKIN = "#e6a986"     # sunlit skin
CLAY = "#b27660"     # skin in shadow
LEAF = "#2f3b2c"     # the trees behind
PALETTE = [("NIGHT", NIGHT), ("SHADE", SHADE), ("BENCH", BENCH), ("LEAF", LEAF), ("WOOD", WOOD),
           ("CLAY", CLAY), ("SKIN", SKIN), ("STONE", STONE), ("SHIRT", SHIRT), ("MIST", MIST)]

FONTS = {
    "mono": ("JetBrainsMono[wght].ttf", "JBMono", "ui-monospace, Menlo, Consolas, monospace"),
    "serif": ("InstrumentSerif-Regular.ttf", "ISerif", "Georgia, 'Times New Roman', serif"),
    "italic": ("InstrumentSerif-Italic.ttf", "ISerifIt", "Georgia, 'Times New Roman', serif"),
}

_cache = {}

ANIM_CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}"
    ".rise{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    ".fade{animation:fade 1.4s ease-out both}"
    "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    ".grow{transform-box:fill-box;transform-origin:0 50%;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes marq{to{transform:translateX(var(--shift))}}"
    ".marq{animation:marq 18s linear infinite}"
    "@keyframes fA{0%,49.99%{opacity:1}50%,100%{opacity:0}}@keyframes fB{0%,49.99%{opacity:0}50%,100%{opacity:1}}"
    ".fA{animation:fA .9s steps(1) infinite}.fB{animation:fB .9s steps(1) infinite}"
    "@keyframes flick{0%,100%{opacity:1}7%{opacity:.86}9%{opacity:1}52%{opacity:.93}54%{opacity:1}}"
    ".flick{animation:flick 4.2s steps(1) infinite}"
    "@keyframes blink{0%,55%{opacity:1}56%,100%{opacity:.15}}"
    ".blink{animation:blink 1.6s steps(1) infinite}"
    "@keyframes draw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}"
    ".draw{stroke-dasharray:var(--len);animation:draw 1.8s cubic-bezier(.4,0,.2,1) both}"
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

    def text(self, x, y, txt, key="mono", size=16, fill=MIST, weight=400, anchor="start", ls=0,
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

    def line(self, x1, y1, x2, y2, stroke=MIST, sw=1, opacity=1, dash=None):
        a = f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"'
        if opacity != 1:
            a += f' stroke-opacity="{opacity}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.add(f"<line {a}/>")

    def icon(self, name, x, y, size, fill=MIST):
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
