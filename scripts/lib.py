"""Shared helpers for the profile graphics: the terminal palette, text measuring, SVG builder.

Text uses the system monospace font (SF Mono, Menlo, Consolas, ...), nothing is embedded. Every
glyph of a monospace font is 0.6 em wide or a little less, so widths are measured as 0.6 em.
"""
import os
import re
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"

# the avatar's colours: a man on a park bench in muted 35mm, a pale blue shirt, a little dark dog
VOID = "#0e0b0d"       # night under the bench, the screen behind everything
PANEL = "#1a1718"      # shade between the planks, inside a box
LINE = "#5e584b"       # sunlit bark, box borders
DIM = "#2f2a27"        # weathered wood, faint rules and empty cells
MOSS = "#354331"       # the trees behind, buttons
CODE = "#7f9470"       # leaves in the light, falling code
GLOW = "#e6a986"       # sunlit skin, the warm highlight
TEXT = "#e3eeef"       # light on the shirt, body text
MUTED = "#bdaea3"      # khaki trousers, quiet text
FRAME = "#bdaea3"      # the dashed outer frame
LCD = "#a2bbc5"        # the pale blue shirt, a backlit Nokia screen
LCD_INK = "#0e0b0d"    # its pixels
BRASS = "#b27660"      # skin in shadow, a sticker border

ANIM_CSS = (
    "@keyframes rain{from{transform:translateY(var(--from))}to{transform:translateY(var(--to))}}"
    ".rain{animation:rain var(--d) linear infinite;animation-delay:var(--delay)}"
    "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
    ".blink{animation:blink 1.1s steps(1) infinite}"
    "@keyframes flick{0%,100%{opacity:1}4%{opacity:.7}6%{opacity:1}48%{opacity:.9}50%{opacity:1}}"
    ".flick{animation:flick 5s steps(1) infinite}"
    "@keyframes rise{from{opacity:0}to{opacity:1}}"
    ".rise{animation:rise .6s steps(4) both}"
    "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    ".grow{transform-box:fill-box;transform-origin:0 50%;animation:grow 1.1s steps(12) both}"
    "@media (prefers-reduced-motion:reduce){[class]{animation:none!important}}"
)


def text_width(size, txt, weight=400, ls=0):
    return len(txt) * (size * 0.6 + ls)


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

    def text(self, x, y, txt, size=16, fill=TEXT, weight=400, anchor="start", ls=0, opacity=1):
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
