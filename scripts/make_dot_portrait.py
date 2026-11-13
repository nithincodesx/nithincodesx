#!/usr/bin/env python3
"""
Build data/portrait_dots.json: a dot-only (halftone) portrait of the character
in a source photo, for the hero card. Dots only -- no image is embedded.

Method: a hand-traced polygon isolates the figure from its background; each
grid cell inside the figure becomes one dot whose radius follows the cell's
darkness (dark -> full dot, rim light -> tiny dot), so the lit outline of the
figure survives in dots. The render script fades the dots in row by row.

Usage: python scripts/make_dot_portrait.py <source-image>
Requires Pillow + numpy (build-time only; the daily workflow does NOT run
this -- the committed JSON is the portrait).
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

SRC = sys.argv[1] if len(sys.argv) > 1 else ""
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "portrait_dots.json")

# Figure outline in the 640x640 source photo (head bowed, shoulders, shirt).
POLY = [(250,70),(300,55),(360,60),(405,95),(430,150),(435,210),(420,260),(398,298),
        (432,332),(500,362),(540,420),(548,640),(92,640),(100,430),(125,370),(190,320),
        (215,272),(205,200),(215,130),(230,95)]
CROP = (70, 30, 570, 640)   # x0, y0, x1, y1
COLS, ROWS = 42, 52

def main():
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(float)
    lum = 0.299*a[:,:,0] + 0.587*a[:,:,1] + 0.114*a[:,:,2]
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(POLY, fill=255)
    m = np.asarray(mask) > 0
    cw = (CROP[2]-CROP[0]) / COLS
    ch = (CROP[3]-CROP[1]) / ROWS
    dots = []
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = int(CROP[0]+c*cw), int(CROP[1]+r*ch)
            x1, y1 = int(CROP[0]+(c+1)*cw), int(CROP[1]+(r+1)*ch)
            cell_m = m[y0:y1, x0:x1]
            if cell_m.mean() < 0.55:
                continue
            if (x0+x1)/2 > 478 and (y0+y1)/2 > 545:  # bright forearm block reads as noise
                continue
            L = lum[y0:y1, x0:x1][cell_m].mean()
            f = max(0.0, min(1.0, (150 - L) / 130))
            if f < 0.12:
                continue
            dots.append([c, r, round(float(f), 2)])
    with open(OUT, "w") as fh:
        json.dump({"cols": COLS, "rows": ROWS, "dots": dots}, fh)
    print(f"wrote {OUT}: {len(dots)} dots")

if __name__ == "__main__":
    main()
