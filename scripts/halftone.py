"""Turns a background-free portrait (RGBA cut-out) into a halftone PNG: white dots on transparent.

usage: halftone.py [cutout.png]   (the cut-out itself is made locally and is not part of the repo)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(HERE, "..", "tools", "src", "cutout.png")
OUT = os.path.join(HERE, "src", "portrait-halftone.png")
WIDTH = 740           # output width in px
CELL = 6.3            # dot pitch
SS = 4                # supersampling for smooth dots


def main(src=DEFAULT_IN):
    im = Image.open(src).convert("RGBA")
    h = round(im.height * WIDTH / im.width)
    im = im.resize((WIDTH, h), Image.LANCZOS)
    alpha = np.asarray(im.split()[3], dtype=np.float32) / 255.0
    lum_img = im.convert("RGB").convert("L")
    # calm the plaid shirt so it does not moire against the dot grid
    soft = lum_img.filter(ImageFilter.GaussianBlur(3.2))
    ramp = np.clip((np.arange(h, dtype=np.float32) / h - 0.60) / 0.12, 0, 1)[:, None]
    lum = np.asarray(lum_img, np.float32) * (1 - ramp) + np.asarray(soft, np.float32) * ramp
    lum = Image.fromarray(np.uint8(np.clip(lum, 0, 255))).filter(ImageFilter.UnsharpMask(radius=5, percent=210, threshold=2))
    g = np.asarray(lum, dtype=np.float32) / 255.0
    g = np.clip((g - 0.15) / 0.68, 0, 1) ** 1.05
    inner = np.asarray(Image.fromarray(np.uint8(alpha > 0.5) * 255).filter(ImageFilter.MinFilter(15)), np.float32) / 255.0
    rim = np.clip((alpha > 0.5) * 1.0 - inner, 0, 1)          # thin light edge so dark hair keeps its silhouette
    g = np.maximum(g, rim * 0.42)
    fade = np.clip((1 - np.arange(h, dtype=np.float32) / h) / 0.30, 0, 1)[:, None]   # torso dissolves at the bottom
    g = g * (alpha > 0.5) * (0.25 + 0.75 * fade)

    canvas = Image.new("L", (WIDTH * SS, h * SS), 0)
    d = ImageDraw.Draw(canvas)
    ca = sa = math.sqrt(0.5)
    n = int(math.hypot(WIDTH, h) / CELL) + 2
    for i in range(-n, n):
        for j in range(-n, n):
            u, v = i * CELL, j * CELL
            x, y = u * ca - v * sa + WIDTH / 2, u * sa + v * ca + h / 2
            if not (0 <= x < WIDTH and 0 <= y < h):
                continue
            val = g[int(y), int(x)]
            if val < 0.05:
                continue
            r = CELL * math.sqrt(val / math.pi) * 1.08
            d.ellipse(((x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS), fill=255)
    a = canvas.resize((WIDTH, h), Image.LANCZOS)
    out = Image.new("RGBA", (WIDTH, h), (255, 255, 255, 0))
    out.putalpha(a)
    box = a.point(lambda p: 255 if p > 40 else 0).getbbox()
    pad = 14
    out = out.crop((0, max(0, box[1] - pad), WIDTH, h))
    out.save(OUT, optimize=True)
    print(OUT, out.size, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main(*sys.argv[1:2])
