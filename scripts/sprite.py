"""Builds the 1-bit pixel-art sprite of the portrait (ordered dithering) from a background-free cut-out.

usage: sprite.py [cutout.png]   -> writes src/sprite.txt ('#' = black pixel, '.' = white)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(HERE, "..", "tools", "src", "cutout.png")
OUT = os.path.join(HERE, "src", "sprite.txt")
SW, SH = 80, 96
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0


def main(src=DEFAULT_IN):
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im.split()[3])
    ys, xs = np.where(a > 128)
    x0, x1, y0 = xs.min(), xs.max(), ys.min()
    w = x1 - x0
    top = max(0, y0 - int(w * 0.06))
    box = (x0, top, x1, min(im.height, top + int(w * SH / SW)))
    im = im.crop(box).resize((SW, SH), Image.LANCZOS)
    alpha = np.asarray(im.split()[3], dtype=np.float32) / 255.0 > 0.5
    lum = im.convert("RGB").convert("L").filter(ImageFilter.UnsharpMask(radius=2.2, percent=230, threshold=1))
    g = np.asarray(lum, dtype=np.float32) / 255.0
    lo, hi = np.percentile(g[alpha], [6, 99])
    g = np.clip((g - lo) / (hi - lo), 0, 1) ** 1.45
    thr = np.tile(BAYER4, (SH // 4 + 1, SW // 4 + 1))[:SH, :SW]
    light = g > thr
    dark = alpha & ~light
    er = np.asarray(Image.fromarray(np.uint8(alpha) * 255).filter(ImageFilter.MinFilter(3))) > 128
    dark |= alpha & ~er                      # 1px outline around the silhouette
    rows = ["".join("#" if dark[y, x] else "." for x in range(SW)) for y in range(SH)]
    open(OUT, "w").write("\n".join(rows) + "\n")
    print(OUT, SW, "x", SH, "dark px:", int(dark.sum()))


if __name__ == "__main__":
    main(*sys.argv[1:2])
