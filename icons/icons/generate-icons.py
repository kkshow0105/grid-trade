#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grid Trading Assistant - Icon Generator (fast)"""

import struct, zlib, os, math, sys

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def chunk(t, d):
    c = t + d
    return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

def make_png(w, h, px):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    raw = b''
    for y in range(h):
        raw += b'\x00'
        off = y * w
        for x in range(w):
            raw += bytes(px[off + x])
    return sig + ihdr + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')

def draw_icon(sz):
    """Draw grid trading icon at sz x sz"""
    BG = (18, 23, 40)
    BL = (37, 99, 235)
    GR = (63, 185, 80)
    RD = (248, 81, 73)

    cr = int(sz * 0.18)
    cr2 = cr * cr
    corners = [(cr, cr, -1, -1), (sz-cr, cr, 1, -1),
               (cr, sz-cr, -1, 1), (sz-cr, sz-cr, 1, 1)]

    gys = [int(sz * i / 6) for i in range(1, 6)]
    gw = max(1, int(sz * 0.015))

    x1, y1 = int(sz*0.12), int(sz*0.72)
    x2, y2 = int(sz*0.88), int(sz*0.22)
    dx, dy = x2-x1, y2-y1
    ln = math.hypot(dx, dy)
    lw = max(1, int(sz * 0.025))

    x1b, y1b = int(sz*0.20), int(sz*0.30)
    x2b, y2b = int(sz*0.72), int(sz*0.62)
    dxb, dyb = x2b-x1b, y2b-y1b
    lnb = math.hypot(dxb, dyb)
    lwb = max(1, int(sz * 0.025))

    dr = max(1, int(sz * 0.035))
    dr2 = dr * dr
    dots = [
        (int(sz*0.12), int(sz*0.72), 1),
        (int(sz*0.37), int(sz*0.59), 1),
        (int(sz*0.63), int(sz*0.42), 1),
        (int(sz*0.88), int(sz*0.22), 1),
        (int(sz*0.20), int(sz*0.30), 0),
        (int(sz*0.46), int(sz*0.47), 0),
    ]

    def _blend(c1, c2, t):
        t = max(0, min(1, t))
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    px = []
    for y in range(sz):
        for x in range(sz):
            # Rounded corner mask
            vis = True
            for cx, cy, sx, sy in corners:
                dxc, dyc = x - cx, y - cy
                if sx * dxc < 0 and sy * dyc < 0 and dxc*dxc + dyc*dyc > cr2:
                    vis = False
                    break
            if not vis:
                px.append((0, 0, 0, 0))
                continue

            c = BG

            # Grid lines
            for gy in gys:
                dg = abs(y - gy)
                if dg <= gw:
                    c = _blend(c, BL, 0.12 * (1 - dg / gw))

            # Green uptrend line
            if min(x1, x2) - lw <= x <= max(x1, x2) + lw:
                d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / ln
                if d <= lw:
                    c = _blend(c, GR, 0.85 * (1 - d / lw))

            # Red downtrend line
            if min(x1b, x2b) - lwb <= x <= max(x1b, x2b) + lwb:
                d = abs(dyb * x - dxb * y + x2b * y1b - y2b * x1b) / lnb
                if d <= lwb:
                    c = _blend(c, RD, 0.70 * (1 - d / lwb))

            # Price dots
            for dxp, dyp, is_green in dots:
                dd = (x - dxp) * (x - dxp) + (y - dyp) * (y - dyp)
                if dd <= dr2:
                    dc = GR if is_green else RD
                    c = _blend(c, dc, 1 - math.sqrt(dd) / dr)

            px.append((*c, 255))

    return px


def nn_scale(src, sw, sh, tw, th):
    """Nearest-neighbor scale up"""
    out = []
    for y in range(th):
        sy = int(y * sh / th) * sw
        for x in range(tw):
            out.append(src[sy + int(x * sw / tw)])
    return out


def main():
    base = 64
    print(f'Drawing {base}x{base} base icon...')
    bp = draw_icon(base)
    print(f'  Done: {len(bp)} pixels')

    for sz in [180, 192, 512]:
        print(f'Generating {sz}x{sz}...')
        px = bp if sz == base else nn_scale(bp, base, base, sz, sz)
        png = make_png(sz, sz, px)
        path = os.path.join(OUTPUT_DIR, f'icon-{sz}.png')
        with open(path, 'wb') as f:
            f.write(png)
        print(f'  [OK] icon-{sz}.png ({len(png)/1024:.1f} KB)')

    print(f'\nAll icons saved to: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
