#!/usr/bin/env python3
"""Generate PWA icons (no external deps) for the meigen app.

Draws a dark gradient rounded square with two stylized quotation marks.
Outputs:
  icons/icon-192.png
  icons/icon-512.png
  icons/icon-maskable-512.png  (extra safe-zone padding for Android masks)
  icons/apple-touch-icon.png   (180x180)
"""
import os
import struct
import zlib
import math

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


# Palette (matches the app's CSS gradient).
TOP = (124, 92, 255)      # violet
BOTTOM = (24, 19, 48)     # deep indigo/near-black
ACCENT = (255, 255, 255)  # quote marks


def rounded_alpha(x, y, size, radius):
    """Return 1.0 inside a rounded square, with a soft 1px edge."""
    rx = min(x, size - 1 - x)
    ry = min(y, size - 1 - y)
    if rx >= radius or ry >= radius:
        return 1.0
    dx = radius - rx
    dy = radius - ry
    d = math.hypot(dx, dy)
    return max(0.0, min(1.0, radius - d + 0.5))


def quote_alpha(x, y, size, cx, cy, scale):
    """Stylized double quotation mark made of two comma-like blobs."""
    a = 0.0
    gap = scale * 1.25
    for k in (0, 1):
        bx = cx + (k - 0.5) * gap
        # round head
        r = scale * 0.62
        d = math.hypot(x - bx, y - cy)
        a = max(a, max(0.0, min(1.0, r - d + 0.5)))
        # tail (curved-ish trapezoid going down-left)
        tx = bx - scale * 0.30
        ty = cy + scale * 0.95
        tw = scale * 0.34
        th = scale * 1.05
        if ty - th * 0.2 <= y <= ty + th:
            prog = (y - (ty - th * 0.2)) / (th * 1.2)
            half = tw * (1.0 - prog * 0.7)
            curve = tx - prog * scale * 0.45
            if abs(x - curve) <= half:
                edge = half - abs(x - curve)
                a = max(a, max(0.0, min(1.0, edge + 0.5)))
    return min(1.0, a)


def render(size, maskable=False):
    pad = int(size * 0.16) if maskable else 0
    inner = size - 2 * pad
    radius = int(inner * (0.30 if not maskable else 0.30))

    # quote mark geometry
    qscale = inner * 0.16
    qcx = pad + inner * 0.5
    qcy = pad + inner * 0.40

    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type 0
        for x in range(size):
            # background gradient over the whole canvas
            ty = y / (size - 1)
            bg = mix(TOP, BOTTOM, ty ** 0.85)

            ix = x - pad
            iy = y - pad
            if 0 <= ix < inner and 0 <= iy < inner:
                ra = rounded_alpha(ix, iy, inner, radius)
            else:
                ra = 0.0

            if maskable:
                # full-bleed background for maskable, card only as visual
                base = bg
                a_card = ra
            else:
                base = (10, 8, 20)
                a_card = ra

            # compose card over (transparent) backdrop
            r, g, b = base
            if not maskable:
                r, g, b = mix((10, 8, 20), bg, 1.0)
            out_a = a_card if not maskable else 1.0
            r, g, b = bg if maskable else mix((10, 8, 20), bg, ra)

            # draw quote marks
            qa = quote_alpha(x, y, size, qcx, qcy, qscale)
            if qa > 0:
                r, g, b = mix((r, g, b), ACCENT, qa * 0.92)

            alpha = 255 if maskable else int(round(out_a * 255))
            raw.extend((r & 255, g & 255, b & 255, alpha))
    return raw


def write_png(path, size, raw):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # RGBA
    idat = zlib.compress(bytes(raw), 9)
    png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote", path, size, "x", size)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    write_png(os.path.join(OUT_DIR, "icon-192.png"), 192, render(192))
    write_png(os.path.join(OUT_DIR, "icon-512.png"), 512, render(512))
    write_png(os.path.join(OUT_DIR, "icon-maskable-512.png"), 512, render(512, maskable=True))
    write_png(os.path.join(OUT_DIR, "apple-touch-icon.png"), 180, render(180))


if __name__ == "__main__":
    main()
