"""Draw share/vinyl_holder/side_view_dimensions.png (to scale) from the part's own parameters."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "parts"))
import vinyl_holder as v  # noqa: E402

OUT = ROOT / "share" / "vinyl_holder" / "side_view_dimensions.png"
SCALE = 7.0  # px per mm
ORIGIN = (230, 560)  # px of (wall face, underside of floor)
CANVAS = (640, 640)
WALL_T, VIEW_TOP = 3.0, 70.0  # drawn wall thickness and top of drawing, mm
DASH, DASH_GAP = 1.5, 3.0
FONT, FONT_S = 18, 15
TICK = 6


def main():
    img = Image.new("RGB", CANVAS, "white")
    d = ImageDraw.Draw(img)
    f, fs = ImageFont.load_default(size=FONT), ImageFont.load_default(size=FONT_S)

    def P(x, y):
        return (ORIGIN[0] + x * SCALE, ORIGIN[1] - y * SCALE)

    prof = [(0, 0), (v.LIP_X1, 0), (v.LIP_X1, v.LIP_TOP), (v.LIP_X0, v.LIP_TOP), (v.LIP_X0, v.FLOOR_T),
            (v.BACK_T, v.FLOOR_T), (v.BACK_T, v.BACK_H), (0, v.BACK_H)]
    d.polygon([P(*p) for p in prof], fill="#2b2b2b", outline="black")
    (wx0, wy0), (wx1, wy1) = P(-WALL_T, VIEW_TOP), P(0, -WALL_T)
    d.rectangle([wx0, wy0, wx1, wy1], fill="#d9d9d9")
    d.text(P(-WALL_T + 0.4, VIEW_TOP - 4), "WALL", fill="black", font=fs)

    jx0 = v.LIP_X0 - v.JACKET_T_MAX  # 8 mm sleeve standing against the lip
    y = v.FLOOR_T
    while y < VIEW_TOP:
        y1 = min(y + DASH, VIEW_TOP)
        d.line([P(jx0, y), P(jx0, y1)], fill="#c0392b", width=2)
        if y >= v.LIP_TOP:
            d.line([P(v.LIP_X0, y), P(v.LIP_X0, y1)], fill="#c0392b", width=2)
        y += DASH_GAP
    d.text(P(jx0 + 0.6, 50), f"{v.JACKET_T_MAX:.0f} mm\nrecord\nsleeve", fill="#c0392b", font=fs)

    def dim_h(x0, x1, yy, label, dy=TICK):
        a, b = P(x0, yy), P(x1, yy)
        d.line([a, b], fill="black")
        for p in (a, b):
            d.line([(p[0], p[1] - TICK), (p[0], p[1] + TICK)], fill="black")
        d.text(((a[0] + b[0]) / 2 - 14, a[1] + dy), label, fill="black", font=f)

    def dim_v(x, y0, y1, label):
        a, b = P(x, y0), P(x, y1)
        d.line([a, b], fill="black")
        for p in (a, b):
            d.line([(p[0] - TICK, p[1]), (p[0] + TICK, p[1])], fill="black")
        d.text((a[0] + 8, (a[1] + b[1]) / 2 - 9), label, fill="black", font=f)

    dim_h(0, v.LIP_X1, -4, f"{v.LIP_X1:.0f} mm deep")
    dim_h(v.BACK_T, v.LIP_X0, 30, f"{v.JACKET_GAP:.0f} mm", dy=-26)
    dim_v(v.LIP_X1 + 3, v.FLOOR_T, v.LIP_TOP, f"{v.LIP_H:.0f} mm lip")
    dim_v(v.LIP_X1 + 12, 0, v.BACK_H, f"{v.BACK_H:.0f} mm tall")
    d.text((20, 20), "Vinyl record holder - side view (to scale)", fill="black", font=f)
    d.text((20, 46), f"Width along the wall: {v.WIDTH:.0f} mm.  Walls {v.BACK_T:.0f} mm.  "
           f"Channel {v.JACKET_GAP:.0f} mm (fits sleeves up to {v.JACKET_GAP:.0f} mm).", fill="black", font=fs)
    d.text((20, 66), "Prints in this orientation: floor on the bed.", fill="black", font=fs)
    img.save(OUT)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
