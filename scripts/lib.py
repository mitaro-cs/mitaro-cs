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
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
MONO_EM = 0.6   # every glyph of a monospace font is about 0.6 em wide
METRICS = json.load(open(os.path.join(HERE, "metrics.json"), encoding="utf-8"))

# Motion, all CSS so it stops under prefers-reduced-motion. Every animated element's resting state is
# its final state, so a viewer without motion sees the finished page.
CSS = (
    "text{font-variant-numeric:tabular-nums}"
    ".lift,.roll,.fade,.wide,.grow,.packet,.pulse,.type,.shine,.wave,.ripple,.draw{animation-delay:var(--t,0s)}"
    "@keyframes draw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}"
    ".draw{animation:draw 2.4s cubic-bezier(.4,0,.2,1) both}"
    "@keyframes lift{from{transform:translateY(var(--dy))}to{transform:none}}"
    ".lift{animation:lift 1s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes roll{from{transform:translateY(var(--from))}to{transform:none}}"
    ".roll{animation:roll 1.8s cubic-bezier(.16,1,.3,1) both}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    ".fade{animation:fade .7s ease-out both}"
    "@keyframes wide{from{transform:scaleX(0)}to{transform:none}}"
    ".wide{transform-box:fill-box;transform-origin:0 50%;animation:wide 1s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes grow{from{transform:scale(0)}to{transform:none}}"
    ".grow{transform-box:view-box;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}"
    "@keyframes spin{to{transform:rotate(360deg)}}"
    ".sweep{transform-box:view-box;animation:spin 14s linear infinite}"
    "@keyframes flow{from{stroke-dashoffset:var(--start)}to{stroke-dashoffset:var(--end)}}"
    ".packet{animation:flow 2.6s cubic-bezier(.45,0,.55,1) infinite}"
    "@keyframes pulse{0%,100%{opacity:.25}50%{opacity:1}}"
    ".pulse{animation:pulse 2.6s ease-in-out infinite}"
    "@keyframes tick{to{transform:translateX(var(--shift))}}"
    ".ticker{animation:tick var(--d) linear infinite}"
    "@keyframes type{from{transform:translateX(var(--dx))}to{transform:none}}"
    ".type{animation:type var(--d,1s) both}"
    "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
    ".blink{animation:blink 1s steps(1) infinite}"
    ".rest{opacity:0}"
    "@keyframes shine{0%{transform:translateX(var(--from))}40%,100%{transform:translateX(var(--to))}}"
    ".shine{animation:shine 6s cubic-bezier(.45,0,.55,1) infinite}"
    "@keyframes wave{0%,100%{opacity:1}50%{opacity:.4}}"
    ".wave{animation:wave 3.6s ease-in-out infinite}"
    "@keyframes ripple{0%{transform:scale(.15);opacity:.9}75%,100%{transform:scale(1);opacity:0}}"
    ".ripple{transform-box:fill-box;transform-origin:center;animation:ripple 2.6s cubic-bezier(.2,.7,.3,1) infinite}"
    "@keyframes orbit{to{transform:rotate(360deg)}}"
    ".orbit{transform-box:view-box;transform-origin:0 0;animation:orbit 10s linear infinite}"
    "@keyframes depth{0%,40%{opacity:1}50%,90%{opacity:.15}100%{opacity:1}}"
    ".depth{animation:depth 10s linear infinite}"
    "@keyframes ping{0%{transform:scale(.4);opacity:.8}70%,100%{transform:scale(1.6);opacity:0}}"
    ".ping{transform-box:fill-box;transform-origin:center;animation:ping 2.4s ease-out infinite}"
    "@keyframes glide{0%{transform:translateX(0);opacity:0}8%{opacity:1}40%,100%{transform:translateX(var(--w));opacity:0}}"
    ".glide{opacity:0;animation:glide 7s cubic-bezier(.45,0,.55,1) infinite;animation-delay:var(--t,1.5s)}"
    "@keyframes twinkle{0%,100%{opacity:var(--o,.5)}50%{opacity:.08}}"
    ".twinkle{animation:twinkle var(--d,3s) ease-in-out infinite;animation-delay:var(--t,0s)}"
    "@media (prefers-reduced-motion:reduce){[class]{animation:none!important}}"
)


def mono_width(size, txt):
    return len(txt) * size * MONO_EM


def text_width(size, txt, weight=400, ls=0):
    m = METRICS["700" if weight >= 600 else "400"]
    return sum(m.get(ch, 560) for ch in txt) * size / 1000 * 1.05 + ls * len(txt)


class Svg:
    def __init__(self, w, h, title, desc=""):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.defs, self.body = [], []
        self.css = {}   # extra rules, keyed so each is written once
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

    def circle(self, cx, cy, r, fill, opacity=1, extra=""):
        a = f'cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"'
        if opacity != 1:
            a += f' opacity="{opacity}"'
        self.add(f"<circle {a} {extra}/>")

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

    def frames(self, n, dur, draw, style="", blend=False):
        """Flip-book animation: n groups shown one at a time, dur seconds per loop. draw(i) adds frame i.

        With blend, neighbouring frames cross-fade instead of cutting, which reads as smooth motion.
        Frame 0 is the resting state, so with reduced motion the first frame stays on screen."""
        name = f"f{n}x{round(dur * 1000)}{'b' if blend else ''}"
        cut = 100 / n
        if blend:
            keys = (f"0%{{opacity:0}}{cut * 0.5:.3f}%{{opacity:1}}{cut * 1.5:.3f}%{{opacity:0}}100%{{opacity:0}}")
            timing = "linear"
        else:
            keys = f"0%,{cut:.3f}%{{opacity:1}}{cut + 0.001:.3f}%,100%{{opacity:0}}"
            timing = "steps(1)"
        self.css[name] = (f"@keyframes {name}{{{keys}}}"
                          f"@media (prefers-reduced-motion:no-preference){{.{name}{{opacity:0;"
                          f"animation:{name} {dur}s {timing} infinite}}}}")
        for i in range(n):
            rest = " rest" if i else ""
            self.add(f'<g class="{name}{rest}" style="animation-delay:-{dur * (n - i) / n:.3f}s;{style}">')
            draw(i)
            self.add("</g>")

    def render(self):
        desc = f"<desc>{escape(self.desc)}</desc>" if self.desc else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{escape(self.title)}" '
                f'font-family="{FONT}">'
                f"<title>{escape(self.title)}</title>{desc}<defs><style>{CSS}{''.join(self.css.values())}</style>{''.join(self.defs)}</defs>"
                f"{''.join(self.body)}</svg>")

    def save(self, out_dir, name):
        data = self.render()
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(data)
        print(f"{name:26s}{len(data) / 1024:8.1f} KB")
