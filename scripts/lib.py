"""Shared helpers for the profile graphics: text measuring and a small SVG builder.

Text uses the system sans-serif stack GitHub itself uses, so nothing is embedded. Widths are
measured with Liberation Sans advances (metric-compatible with Arial, metrics.json), plus a little
slack for wider system fonts such as SF Pro.
"""
import json
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
METRICS = json.load(open(os.path.join(HERE, "metrics.json"), encoding="utf-8"))

CSS = "text{font-variant-numeric:tabular-nums}"


def text_width(size, txt, weight=400, ls=0):
    m = METRICS["700" if weight >= 600 else "400"]
    return sum(m.get(ch, 560) for ch in txt) * size / 1000 * 1.05 + ls * len(txt)


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

    def text(self, x, y, txt, size=16, fill="#000", weight=400, anchor="start", ls=0, opacity=1, extra=""):
        a = f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"'
        if weight != 400:
            a += f' font-weight="{weight}"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if ls:
            a += f' letter-spacing="{ls}"'
        if opacity != 1:
            a += f' fill-opacity="{opacity}"'
        self.add(f"<text {a} {extra}>{escape(txt)}</text>")

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1, rx=0, opacity=1, extra=""):
        a = f'x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
        if rx:
            a += f' rx="{rx}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        self.add(f"<rect {a} {extra}/>")

    def line(self, x1, y1, x2, y2, stroke, sw=1, opacity=1):
        a = f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"'
        if opacity != 1:
            a += f' stroke-opacity="{opacity}"'
        self.add(f"<line {a}/>")

    def path(self, d, fill="none", stroke=None, sw=1, opacity=1, extra=""):
        a = f'd="{d}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        self.add(f"<path {a} {extra}/>")

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
                f"<title>{escape(self.title)}</title>{desc}<defs><style>{CSS}</style>{''.join(self.defs)}</defs>"
                f"{''.join(self.body)}</svg>")

    def save(self, out_dir, name):
        data = self.render()
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(data)
        print(f"{name:26s}{len(data) / 1024:8.1f} KB")
