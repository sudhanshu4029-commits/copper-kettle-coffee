"""
Generates a stylised illustration (PNG) for every menu item into ./images.

These are drawn illustrations, not photos. To use real photos instead, drop a
file named <item_id>.jpg (or .png / .webp) into ./images. The app always prefers
a photo over the illustration if both exist. See image_prompts.md / generate_photos.py.

Run:  python make_illustrations.py
"""
import json
import math
import os

import cairosvg

W = H = 600
OUT = os.path.join(os.path.dirname(__file__), "images")

# ---------------------------------------------------------------- helpers

def svg(body, bg, defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  <radialGradient id="bgGlow" cx="50%" cy="38%" r="70%">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.55"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="steel" x1="0" x2="1">
    <stop offset="0" stop-color="#8d949b"/><stop offset="0.25" stop-color="#e9edf0"/>
    <stop offset="0.5" stop-color="#b5bcc3"/><stop offset="0.8" stop-color="#f4f6f7"/>
    <stop offset="1" stop-color="#7d848b"/>
  </linearGradient>
  <linearGradient id="ceramic" x1="0" x2="1">
    <stop offset="0" stop-color="#d9d4cc"/><stop offset="0.35" stop-color="#ffffff"/>
    <stop offset="0.7" stop-color="#f3efe9"/><stop offset="1" stop-color="#c9c2b8"/>
  </linearGradient>
  <linearGradient id="glassShine" x1="0" x2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.05"/>
    <stop offset="0.15" stop-color="#ffffff" stop-opacity="0.55"/>
    <stop offset="0.3" stop-color="#ffffff" stop-opacity="0.05"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  {defs}
</defs>
<rect width="{W}" height="{H}" fill="{bg}"/>
<rect width="{W}" height="{H}" fill="url(#bgGlow)"/>
<rect y="430" width="{W}" height="170" fill="#000" opacity="0.06"/>
{body}
</svg>"""


def shadow(cx, cy, rx, ry, op=0.18):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#2b1b14" opacity="{op}"/>'


def plate(cx=300, cy=440, rx=210, ry=62, color="#ffffff"):
    return (shadow(cx, cy + 14, rx + 6, ry + 6, 0.16) +
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{color}"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.72}" ry="{ry*0.68}" fill="#000" opacity="0.04"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#000" stroke-opacity="0.08" stroke-width="3"/>')


# ---------------------------------------------------------------- drinks

def latte_art(cx, cy, rx, ry, kind, foam="#f3e3c8", base="#8a5232"):
    if kind == "heart":
        s = rx * 0.55
        return (f'<path d="M{cx},{cy+ry*0.55} C{cx-s*1.5},{cy-ry*0.1} {cx-s*0.9},{cy-ry*0.85} {cx},{cy-ry*0.3} '
                f'C{cx+s*0.9},{cy-ry*0.85} {cx+s*1.5},{cy-ry*0.1} {cx},{cy+ry*0.55}Z" fill="{foam}"/>'
                f'<path d="M{cx},{cy-ry*0.32} L{cx},{cy+ry*0.5}" stroke="{base}" stroke-width="3" opacity="0.5"/>')
    if kind == "rosetta":
        out = []
        for i in range(6):
            t = i / 5
            yy = cy + ry * 0.55 - t * ry * 1.05
            ww = rx * (0.62 - t * 0.38)
            out.append(f'<ellipse cx="{cx}" cy="{yy}" rx="{ww}" ry="{ry*0.13}" fill="{foam}"/>')
            out.append(f'<ellipse cx="{cx}" cy="{yy+ry*0.06}" rx="{ww*0.85}" ry="{ry*0.07}" fill="{base}" opacity="0.55"/>')
        out.append(f'<path d="M{cx},{cy-ry*0.6} L{cx},{cy+ry*0.75}" stroke="{base}" stroke-width="3" opacity="0.7"/>')
        return "".join(out)
    if kind == "dust":
        dots = []
        for i in range(140):
            a = i * 2.39996
            r = math.sqrt(i / 140) * 0.8
            dots.append(f'<circle cx="{cx + math.cos(a)*rx*r:.1f}" cy="{cy + math.sin(a)*ry*r:.1f}" r="2.2" fill="#5a3320" opacity="0.55"/>')
        return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.85}" ry="{ry*0.85}" fill="{foam}"/>' + "".join(dots)
    if kind == "crema":
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#b5703c"/>'
                f'<ellipse cx="{cx-rx*0.15}" cy="{cy-ry*0.1}" rx="{rx*0.55}" ry="{ry*0.5}" fill="#d29357" opacity="0.8"/>'
                f'<ellipse cx="{cx+rx*0.25}" cy="{cy+ry*0.2}" rx="{rx*0.25}" ry="{ry*0.22}" fill="#8b4f27" opacity="0.6"/>')
    if kind == "black":
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#2e1a10"/>'
                f'<ellipse cx="{cx-rx*0.35}" cy="{cy-ry*0.35}" rx="{rx*0.3}" ry="{ry*0.18}" fill="#fff" opacity="0.18"/>'
                f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.9}" ry="{ry*0.85}" fill="none" stroke="#7a4a2a" stroke-width="4" opacity="0.6"/>')
    if kind == "mocha":
        return (f'<path d="M{cx-rx*0.6},{cy} q{rx*0.3},{-ry*0.5} {rx*0.6},0 t{rx*0.6},0" stroke="#3a1f12" stroke-width="7" fill="none" opacity="0.8"/>'
                f'<path d="M{cx-rx*0.5},{cy+ry*0.35} q{rx*0.25},{-ry*0.4} {rx*0.5},0 t{rx*0.5},0" stroke="#3a1f12" stroke-width="6" fill="none" opacity="0.7"/>'
                + "".join(f'<rect x="{cx-rx*0.4+i*rx*0.2}" y="{cy-ry*0.55+(i%2)*ry*0.25}" width="10" height="7" rx="2" fill="#4a2716" transform="rotate({i*23} {cx} {cy})"/>' for i in range(5)))
    return ""


def ceramic_cup(cx, top, w, h, cup_fill, liquid, art, foam="#f3e3c8", saucer=True, uid="c"):
    rx, ry = w / 2, w * 0.17
    bw = w * 0.62
    bottom = top + h
    parts = []
    if saucer:
        sr = w * 0.85
        parts.append(shadow(cx, bottom + 22, sr + 10, sr * 0.24, 0.2))
        parts.append(f'<ellipse cx="{cx}" cy="{bottom+8}" rx="{sr}" ry="{sr*0.22}" fill="url(#ceramic)"/>')
        parts.append(f'<ellipse cx="{cx}" cy="{bottom+4}" rx="{sr*0.55}" ry="{sr*0.12}" fill="#000" opacity="0.07"/>')
    else:
        parts.append(shadow(cx, bottom + 10, w * 0.55, w * 0.1, 0.22))
    # handle
    hx = cx + rx * 0.82
    parts.append(f'<path d="M{hx},{top+h*0.18} C{hx+w*0.38},{top+h*0.1} {hx+w*0.36},{top+h*0.72} {hx-w*0.06},{top+h*0.72}" '
                 f'fill="none" stroke="{cup_fill}" stroke-width="{w*0.085}" stroke-linecap="round"/>')
    parts.append(f'<path d="M{hx},{top+h*0.18} C{hx+w*0.38},{top+h*0.1} {hx+w*0.36},{top+h*0.72} {hx-w*0.06},{top+h*0.72}" '
                 f'fill="none" stroke="#000" stroke-opacity="0.12" stroke-width="{w*0.02}" stroke-linecap="round" transform="translate(4,4)"/>')
    # body
    parts.append(f'<path d="M{cx-rx},{top} C{cx-rx},{top+h*0.75} {cx-bw/2},{bottom} {cx},{bottom} '
                 f'C{cx+bw/2},{bottom} {cx+rx},{top+h*0.75} {cx+rx},{top}Z" fill="{cup_fill}"/>')
    parts.append(f'<path d="M{cx-rx},{top} C{cx-rx},{top+h*0.75} {cx-bw/2},{bottom} {cx},{bottom} '
                 f'C{cx+bw/2},{bottom} {cx+rx},{top+h*0.75} {cx+rx},{top}Z" fill="url(#ceramic)" opacity="0.35"/>')
    # rim + liquid
    parts.append(f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="{cup_fill}"/>')
    parts.append(f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="none" stroke="#000" stroke-opacity="0.1" stroke-width="2"/>')
    lrx, lry = rx * 0.9, ry * 0.82
    parts.append(f'<clipPath id="liq{uid}"><ellipse cx="{cx}" cy="{top+2}" rx="{lrx}" ry="{lry}"/></clipPath>')
    parts.append(f'<g clip-path="url(#liq{uid})"><ellipse cx="{cx}" cy="{top+2}" rx="{lrx}" ry="{lry}" fill="{liquid}"/>'
                 f'{latte_art(cx, top + 2, lrx, lry, art, foam, liquid)}</g>')
    return "".join(parts)


def tall_glass(cx, top, w, h, layers, ice=True, straw="#3d6b56", topping=None, uid="g", cream=False):
    """layers: list of (fraction_from_bottom_top, color) drawn bottom-up."""
    bw = w * 0.8
    bottom = top + h
    ry = w * 0.14
    body = f"M{cx-w/2},{top} L{cx-bw/2},{bottom} Q{cx},{bottom+ry*1.1} {cx+bw/2},{bottom} L{cx+w/2},{top}Z"
    p = [shadow(cx, bottom + 18, w * 0.62, w * 0.12, 0.22),
         f'<clipPath id="gl{uid}"><path d="{body}"/></clipPath>',
         f'<path d="{body}" fill="#ffffff" opacity="0.35"/>']
    fill_top = top + h * 0.1
    p.append(f'<g clip-path="url(#gl{uid})">')
    prev = bottom + ry * 2
    for frac, color in layers:
        y = bottom - (bottom - fill_top) * frac
        p.append(f'<rect x="{cx-w}" y="{y}" width="{w*2}" height="{prev-y}" fill="{color}"/>')
        prev = y
    if ice:
        for i, (dx, dy, s, r) in enumerate([(-0.22, 0.12, 0.3, -12), (0.16, 0.08, 0.28, 15), (-0.05, 0.28, 0.3, 6),
                                            (0.2, 0.36, 0.26, -20), (-0.24, 0.46, 0.27, 10)]):
            x = cx + dx * w
            y = fill_top + dy * h
            sz = s * w
            p.append(f'<rect x="{x-sz/2}" y="{y}" width="{sz}" height="{sz}" rx="{sz*0.18}" fill="#ffffff" opacity="0.32" '
                     f'stroke="#ffffff" stroke-opacity="0.6" stroke-width="2" transform="rotate({r} {x} {y+sz/2})"/>')
    p.append('</g>')
    # surface
    p.append(f'<ellipse cx="{cx}" cy="{fill_top}" rx="{w/2*0.97 - (w-bw)/2*0.1}" ry="{ry*0.85}" fill="{layers[-1][1]}"/>')
    if cream:
        for i in range(7):
            p.append(f'<circle cx="{cx-60+i*20}" cy="{fill_top-12-(i%3)*8}" r="{26-(abs(i-3)*3)}" fill="#fffaf2"/>')
    if topping == "caramel":
        p.append(f'<clipPath id="top{uid}"><ellipse cx="{cx}" cy="{fill_top}" rx="{w/2*0.92}" ry="{ry*0.8}"/></clipPath><g clip-path="url(#top{uid})">')
        for i in range(-3, 4):
            p.append(f'<path d="M{cx+i*22-50},{fill_top-ry*0.7} L{cx+i*22+50},{fill_top+ry*0.7}" stroke="#c97a22" stroke-width="5" stroke-linecap="round"/>')
            p.append(f'<path d="M{cx+i*22+50},{fill_top-ry*0.7} L{cx+i*22-50},{fill_top+ry*0.7}" stroke="#d98a2e" stroke-width="5" stroke-linecap="round"/>')
        p.append('</g>')
    # straw
    if straw:
        p.append(f'<path d="M{cx+w*0.12},{fill_top+10} L{cx+w*0.32},{top-h*0.32}" stroke="{straw}" stroke-width="16" stroke-linecap="round"/>')
        p.append(f'<path d="M{cx+w*0.12},{fill_top+10} L{cx+w*0.32},{top-h*0.32}" stroke="#ffffff" stroke-opacity="0.35" stroke-width="4" stroke-linecap="round" transform="translate(-4,0)"/>')
    # glass rim + shine
    p.append(f'<path d="{body}" fill="url(#glassShine)"/>')
    p.append(f'<path d="{body}" fill="none" stroke="#ffffff" stroke-opacity="0.8" stroke-width="3"/>')
    p.append(f'<ellipse cx="{cx}" cy="{top}" rx="{w/2}" ry="{ry}" fill="#ffffff" fill-opacity="0.12" stroke="#ffffff" stroke-opacity="0.9" stroke-width="3"/>')
    return "".join(p)


def filter_coffee():
    cx = 300
    p = [shadow(cx, 470, 200, 40, 0.22)]
    # davara (wide bowl)
    p.append(f'<path d="M110,370 Q120,470 300,470 Q480,470 490,370Z" fill="url(#steel)"/>')
    p.append(f'<ellipse cx="300" cy="370" rx="190" ry="40" fill="#cfd5da"/>')
    p.append(f'<ellipse cx="300" cy="372" rx="170" ry="32" fill="#a8775a"/>')
    p.append(f'<ellipse cx="300" cy="372" rx="170" ry="32" fill="none" stroke="#e8dccb" stroke-width="6" opacity="0.6"/>')
    # tumbler
    p.append(f'<path d="M205,150 L228,392 Q300,410 372,392 L395,150Z" fill="url(#steel)"/>')
    for y in (190, 360):
        p.append(f'<path d="M{208+ (y-150)*0.095},{y} Q300,{y+16} {392-(y-150)*0.095},{y}" stroke="#7f878e" stroke-width="3" fill="none" opacity="0.6"/>')
    p.append(f'<ellipse cx="300" cy="150" rx="95" ry="24" fill="#d8dde1"/>')
    p.append(f'<ellipse cx="300" cy="152" rx="85" ry="19" fill="#c58e64"/>')
    for i in range(28):
        a = i * 2.39996
        r = math.sqrt(i / 28)
        p.append(f'<circle cx="{300+math.cos(a)*70*r:.1f}" cy="{150+math.sin(a)*14*r:.1f}" r="{7-r*3:.1f}" fill="#f1dfc6" opacity="0.9"/>')
    # steam
    for dx in (-30, 10, 45):
        p.append(f'<path d="M{300+dx},125 q-18,-30 0,-55 t0,-55" stroke="#ffffff" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.55"/>')
    return "".join(p)


# ---------------------------------------------------------------- snacks

def croissant():
    p = [plate()]
    segs = [(-150, 30, 46, -38), (-95, -10, 62, -22), (-30, -28, 76, -6), (30, -28, 76, 6), (95, -10, 62, 22), (150, 30, 46, 38)]
    order = [0, 5, 1, 4, 2, 3]
    for i in order:
        dx, dy, r, rot = segs[i]
        x, y = 300 + dx, 400 + dy
        p.append(f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*0.9}" fill="#b8692a" transform="rotate({rot} {x} {y})"/>')
        p.append(f'<ellipse cx="{x}" cy="{y-r*0.15}" rx="{r*0.85}" ry="{r*0.65}" fill="#d98c3e" transform="rotate({rot} {x} {y})"/>')
        p.append(f'<ellipse cx="{x-r*0.2}" cy="{y-r*0.4}" rx="{r*0.4}" ry="{r*0.18}" fill="#f4c27a" opacity="0.8" transform="rotate({rot} {x} {y})"/>')
        p.append(f'<path d="M{x-r*0.7},{y+r*0.1} Q{x},{y+r*0.45} {x+r*0.7},{y+r*0.1}" stroke="#8c4a18" stroke-width="3" fill="none" opacity="0.5" transform="rotate({rot} {x} {y})"/>')
    return "".join(p)


def muffin():
    p = [plate(rx=170, ry=50)]
    # paper cup
    p.append('<path d="M200,330 L225,450 Q300,470 375,450 L400,330Z" fill="#6b8fb3"/>')
    for i in range(11):
        x0 = 205 + i * 19
        p.append(f'<path d="M{x0},332 L{228+i*14.5},452" stroke="#4d6f92" stroke-width="4"/>')
    # dome
    p.append('<path d="M180,335 Q170,200 300,190 Q430,200 420,335 Q300,365 180,335Z" fill="#d79a52"/>')
    p.append('<path d="M200,300 Q215,215 300,208 Q385,215 400,300" fill="#e8b571" opacity="0.8"/>')
    for (x, y) in [(240, 260), (300, 235), (355, 270), (270, 305), (335, 315), (220, 315), (385, 315), (310, 280)]:
        p.append(f'<circle cx="{x}" cy="{y}" r="13" fill="#3b3a78"/><circle cx="{x-4}" cy="{y-4}" r="4" fill="#9a9ad6"/>')
    for (x, y) in [(258, 230), (330, 250), (285, 270), (365, 295), (230, 285)]:
        p.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#f6dba6"/>')
    return "".join(p)


def cookie():
    p = [plate(rx=200, ry=58)]
    for (cx, cy, r, s) in [(230, 400, 95, 0), (370, 380, 90, 1)]:
        p.append(f'<ellipse cx="{cx}" cy="{cy+8}" rx="{r}" ry="{r*0.42}" fill="#9a5b25"/>')
        p.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*0.42}" fill="#cf8d48"/>')
        p.append(f'<ellipse cx="{cx-10}" cy="{cy-6}" rx="{r*0.75}" ry="{r*0.28}" fill="#dfa462" opacity="0.8"/>')
        for i in range(9):
            a = i * 2.39996 + s
            rr = math.sqrt((i + 1) / 10) * 0.8
            x = cx + math.cos(a) * r * rr
            y = cy + math.sin(a) * r * 0.42 * rr
            p.append(f'<path d="M{x-9},{y+4} L{x},{y-7} L{x+10},{y+3}Z" fill="#3a1d10"/>')
    return "".join(p)


def brownie():
    p = [plate(rx=190, ry=56)]
    for (ox, oy) in [(-70, 10), (75, -5)]:
        x, y = 300 + ox, 380 + oy
        p.append(f'<path d="M{x-80},{y-30} L{x+10},{y-60} L{x+90},{y-25} L{x},{y+5}Z" fill="#5b2f1a"/>')
        p.append(f'<path d="M{x-80},{y-30} L{x},{y+5} L{x},{y+60} L{x-80},{y+25}Z" fill="#3b1d10"/>')
        p.append(f'<path d="M{x},{y+5} L{x+90},{y-25} L{x+90},{y+30} L{x},{y+60}Z" fill="#2c140a"/>')
        p.append(f'<path d="M{x-60},{y-32} l30,-6 l20,10 l25,-12 l30,8" stroke="#7d4a2c" stroke-width="3" fill="none"/>')
        p.append(f'<path d="M{x-40},{y-20} l25,4 l18,-14 l30,10" stroke="#8a5534" stroke-width="2.5" fill="none"/>')
        for k in range(5):
            p.append(f'<circle cx="{x-60+k*8}" cy="{y+15+(k%2)*12}" r="3" fill="#1f0d05"/>')
    return "".join(p)


def banana_bread():
    p = [plate(rx=200, ry=58)]
    x, y = 300, 380
    p.append(f'<path d="M{x-150},{y-20} L{x+110},{y-60} L{x+150},{y-10} L{x-110},{y+35}Z" fill="#7a4520"/>')
    p.append(f'<path d="M{x-150},{y-20} L{x-110},{y+35} L{x-110},{y+80} L{x-150},{y+25}Z" fill="#6a3a18"/>')
    p.append(f'<path d="M{x-110},{y+35} L{x+150},{y-10} L{x+150},{y+35} L{x-110},{y+80}Z" fill="#d9a560"/>')
    p.append(f'<path d="M{x-110},{y+35} L{x+150},{y-10}" stroke="#6a3a18" stroke-width="8"/>')
    for (dx, dy) in [(-60, 45), (10, 30), (80, 15), (-20, 55), (50, 40), (110, 10)]:
        p.append(f'<ellipse cx="{x+dx}" cy="{y+dy}" rx="10" ry="6" fill="#8a5a2c"/>')
    for (dx, dy) in [(-80, -20), (-10, -32), (60, -45), (20, -15)]:
        p.append(f'<path d="M{x+dx},{y+dy} q8,-10 16,0 q8,10 16,0" stroke="#e7c48a" stroke-width="7" fill="none" stroke-linecap="round"/>')
    return "".join(p)


def cinnamon_roll():
    p = [plate(rx=190, ry=56)]
    cx, cy = 300, 370
    p.append(f'<ellipse cx="{cx}" cy="{cy+35}" rx="130" ry="55" fill="#b56a2c"/>')
    p.append(f'<rect x="{cx-130}" y="{cy}" width="260" height="35" fill="#b56a2c"/>')
    p.append(f'<ellipse cx="{cx}" cy="{cy}" rx="130" ry="55" fill="#d99550"/>')
    pts = []
    for i in range(240):
        t = i / 240 * 4.2 * math.pi
        r = 6 + t * 8.6
        pts.append(f"{cx + math.cos(t) * r:.1f},{cy + math.sin(t) * r * 0.42:.1f}")
    p.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#7a3d14" stroke-width="9" stroke-linecap="round"/>')
    for (dx, w) in [(-70, 1), (-20, 1.2), (40, 1), (85, 0.9)]:
        p.append(f'<path d="M{cx+dx},{cy-50} q{10*w},40 0,90 q-6,10 -12,0" fill="#fbf4e6" opacity="0.95"/>')
    p.append(f'<path d="M{cx-110},{cy-5} q110,-55 220,0" stroke="#fbf4e6" stroke-width="10" fill="none" stroke-linecap="round" opacity="0.9"/>')
    return "".join(p)


def sandwich(filling):
    p = [plate(rx=210, ry=60)]
    for (ox, flip) in [(-80, 1), (85, -1)]:
        x, y = 300 + ox, 400
        # triangle half: bread top, layers on cut side
        top = f"M{x-90*flip},{y-10} L{x+70*flip},{y-80} L{x+80*flip},{y+20}Z"
        p.append(f'<path d="M{x-90*flip},{y+25} L{x+80*flip},{y+55} L{x+80*flip},{y+20} L{x-90*flip},{y-10}Z" fill="#c98a4b"/>')
        p.append(f'<path d="{top}" fill="#e3b77c"/>')
        p.append(f'<path d="M{x-90*flip},{y-10} L{x+70*flip},{y-80}" stroke="#a8692f" stroke-width="7"/>')
        # cut face layers
        face_y = [y + 2, y + 14, y + 26, y + 38]
        cols = filling
        for i, c in enumerate(cols):
            p.append(f'<path d="M{x-90*flip},{y-10+i*9+4} L{x+80*flip},{y+20+i*9+4}" stroke="{c}" stroke-width="9" stroke-linecap="round"/>')
        p.append(f'<path d="M{x-90*flip},{y+30} L{x+80*flip},{y+60}" stroke="#d2a066" stroke-width="10" stroke-linecap="round"/>')
        for k in range(6):
            p.append(f'<circle cx="{x-50*flip+k*20*flip}" cy="{y-25-k*7}" r="2.5" fill="#8a5a2c" opacity="0.7"/>')
    return "".join(p)


def biscotti():
    p = [plate(rx=200, ry=56)]
    for i, (ox, rot) in enumerate([(-110, -18), (-35, -10), (40, -2), (115, 6)]):
        x, y = 300 + ox, 390
        g = f'<g transform="rotate({rot} {x} {y})">'
        g += f'<rect x="{x-28}" y="{y-80}" width="56" height="150" rx="14" fill="#c8894a"/>'
        g += f'<rect x="{x-22}" y="{y-74}" width="44" height="138" rx="10" fill="#ecd2a3"/>'
        for (dx, dy) in [(-8, -50), (8, -10), (-6, 25), (10, 45)]:
            g += f'<ellipse cx="{x+dx}" cy="{y+dy}" rx="9" ry="6" fill="#f7ead2" stroke="#b47a42" stroke-width="2"/>'
        g += '</g>'
        p.append(g)
    return "".join(p)


def granola_cup():
    cx, top, w, h = 300, 200, 200, 250
    bw = w * 0.82
    bottom = top + h
    body = f"M{cx-w/2},{top} L{cx-bw/2},{bottom} Q{cx},{bottom+20} {cx+bw/2},{bottom} L{cx+w/2},{top}Z"
    p = [shadow(cx, bottom + 18, w * 0.6, 24, 0.22), f'<clipPath id="gc"><path d="{body}"/></clipPath>', '<g clip-path="url(#gc)">']
    layers = [(bottom - 70, bottom + 30, "#f7f3ea"), (bottom - 110, bottom - 70, "#c88a3f"), (bottom - 170, bottom - 110, "#f7f3ea"),
              (bottom - 205, bottom - 170, "#c88a3f")]
    for (y1, y2, c) in layers:
        p.append(f'<rect x="{cx-w}" y="{y1}" width="{w*2}" height="{y2-y1}" fill="{c}"/>')
        if c == "#c88a3f":
            for k in range(14):
                p.append(f'<circle cx="{cx-w/2+k*15}" cy="{y1+8+(k%3)*10}" r="6" fill="#8e5a22"/>')
    p.append('</g>')
    p.append(f'<ellipse cx="{cx}" cy="{top+45}" rx="{w/2*0.95}" ry="22" fill="#f7f3ea"/>')
    for (dx, dy, c) in [(-40, 38, "#b3123b"), (5, 30, "#3b3a78"), (40, 42, "#b3123b"), (-10, 50, "#e04a6b"), (25, 55, "#3b3a78"), (-50, 52, "#3b3a78")]:
        p.append(f'<circle cx="{cx+dx}" cy="{top+dy}" r="13" fill="{c}"/><circle cx="{cx+dx-4}" cy="{top+dy-4}" r="3.5" fill="#fff" opacity="0.5"/>')
    p.append(f'<path d="M{cx-60},{top+30} q60,-25 120,10" stroke="#e6a51e" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.85"/>')
    p.append(f'<path d="{body}" fill="url(#glassShine)"/><path d="{body}" fill="none" stroke="#fff" stroke-opacity="0.85" stroke-width="3"/>')
    p.append(f'<path d="M{cx+30},{top+20} L{cx+95},{top-70}" stroke="#c9b48c" stroke-width="12" stroke-linecap="round"/>')
    return "".join(p)


# ---------------------------------------------------------------- registry

DRAW = {
    "espresso": ("#e8d5bf", lambda: ceramic_cup(300, 300, 170, 120, "#ffffff", "#5a3320", "crema", uid="a")),
    "americano": ("#d8e2dc", lambda: ceramic_cup(300, 230, 230, 200, "#2f4f46", "#2e1a10", "black", saucer=False, uid="b")),
    "cappuccino": ("#f0dcc7", lambda: ceramic_cup(300, 240, 260, 170, "#ffffff", "#8a5232", "dust", uid="c")),
    "latte": ("#e6d3c3", lambda: ceramic_cup(300, 220, 280, 200, "#ffffff", "#9a5d36", "rosetta", uid="d")),
    "flat_white": ("#dfe6ea", lambda: ceramic_cup(300, 260, 240, 150, "#ffffff", "#7a4628", "heart", uid="e")),
    "mocha": ("#ead2c4", lambda: ceramic_cup(300, 230, 260, 190, "#7b3f2b", "#5b311d", "mocha", uid="f")),
    "caramel_macchiato": ("#f2dfc2", lambda: tall_glass(300, 170, 200, 290, [(0.55, "#f3e7d6"), (0.8, "#c69062"), (1.0, "#8e5730")], topping="caramel", uid="g1")),
    "cold_brew": ("#d6e3e8", lambda: tall_glass(300, 170, 200, 290, [(1.0, "#3b2112")], straw="#1f3a2e", uid="g2")),
    "iced_latte": ("#e4ddd2", lambda: tall_glass(300, 170, 200, 290, [(0.6, "#efe2cf"), (0.75, "#c59b72"), (1.0, "#9a643b")], uid="g3")),
    "filter_coffee": ("#efe0c9", filter_coffee),
    "croissant": ("#f3e2c6", croissant),
    "blueberry_muffin": ("#e2e3f0", muffin),
    "choc_chip_cookie": ("#efe1cf", cookie),
    "brownie": ("#ead7cf", brownie),
    "banana_bread": ("#f4e9c6", banana_bread),
    "cinnamon_roll": ("#f1ddc9", cinnamon_roll),
    "paneer_sandwich": ("#f3dfc8", lambda: sandwich(["#3f8f4f", "#f08a3c", "#f6e7d0"])),
    "chicken_pesto_sandwich": ("#e3ebdc", lambda: sandwich(["#d9442f", "#4e8a36", "#f2e3c9"])),
    "almond_biscotti": ("#efe6da", biscotti),
    "granola_cup": ("#f3e0e4", granola_cup),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "menu.json"), encoding="utf-8") as f:
        ids = [i["id"] for i in json.load(f)["items"]]
    for item_id in ids:
        bg, fn = DRAW[item_id]
        cairosvg.svg2png(bytestring=svg(fn(), bg).encode(), write_to=os.path.join(OUT, f"{item_id}_illustration.png"))
        print("wrote", item_id)


if __name__ == "__main__":
    main()
