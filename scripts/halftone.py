"""Turns the avatar into a halftone PNG (paper-white dots on transparent), cropped to the subject."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 1.9           # upscale of the 499x564 source
CELL = 7.6            # dot pitch in output px
SS = 4                # supersampling for smooth dots


def main(out=os.path.join(HERE, "src", "portrait-halftone.png")):
    im = Image.open(os.path.join(HERE, "src", "avatar.jpg")).convert("L")
    W, H = round(im.width * SCALE), round(im.height * SCALE)
    im = im.resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=7, percent=170, threshold=2)).filter(ImageFilter.GaussianBlur(0.9))
    g = np.asarray(im, dtype=np.float32) / 255.0
    g = np.clip((g - 0.06) / 0.90, 0, 1) ** 1.25
    canvas = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(canvas)
    ca, sa = math.cos(math.radians(45)), math.sin(math.radians(45))
    diag = int(math.hypot(W, H) / CELL) + 2
    for i in range(-diag, diag):
        for j in range(-diag, diag):
            u, v = i * CELL, j * CELL
            x, y = u * ca - v * sa + W / 2, u * sa + v * ca + H / 2
            if not (0 <= x < W and 0 <= y < H):
                continue
            val = g[int(y), int(x)]
            if val < 0.05:
                continue
            r = CELL * math.sqrt(val / math.pi) * 1.08
            d.ellipse(((x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS), fill=255)
    a = canvas.resize((W, H), Image.LANCZOS)
    rgba = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    rgba.putalpha(a)
    # crop to the subject (drop the empty black margins), keep the bottom edge
    box = a.point(lambda p: 255 if p > 40 else 0).getbbox()
    pad = 18
    l, t, r_, b = box
    rgba = rgba.crop((max(0, l - pad), max(0, t - pad), min(W, r_ + pad), H))
    rgba.save(out, optimize=True)
    print(out, rgba.size, os.path.getsize(out) // 1024, "KB", "bbox", box)


if __name__ == "__main__":
    main()
