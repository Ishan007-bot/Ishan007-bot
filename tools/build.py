"""Draws every image in this profile, in two inks.

    python tools/build.py

One geometry definition per image; LIGHT and DARK only change colours.
Text is measured with the real font metrics, and each SVG embeds only the
glyphs it actually uses (subset WOFF2), so the files render the same
everywhere without loading anything from the network.
"""
from __future__ import annotations

import base64
import logging
logging.getLogger("fontTools").setLevel(logging.ERROR)
import io
import math
import os
import sys
from html import escape

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "tools", "fonts")
OUT = os.path.join(ROOT, "assets")
W = 880

FONTS = {
    # key: (file, css family, weight)
    "D": ("BarlowCondensed-ExtraBold.ttf", "BCX", 800),
    "DS": ("BarlowCondensed-SemiBold.ttf", "BCS", 600),
    "B": ("Barlow-Regular.ttf", "BR", 400),
    "BM": ("Barlow-Medium.ttf", "BM", 500),
    "BS": ("Barlow-SemiBold.ttf", "BS", 600),
    "M": ("IBMPlexMono-Regular.ttf", "PM", 400),
    "MM": ("IBMPlexMono-Medium.ttf", "PMM", 500),
}

LIGHT = dict(
    name="light", bg="#f6f1e6", ink="#1c1a16", muted="#6a6458", soft="#8f887a",
    hair="#d8cfbd", faint="#e9e2d3", track="#c0512e", track2="#e9b7a2",
    lane="#fffaf1", grass="#2d6a48", grass2="#d3e5d6", chip="#1c1a16",
)
DARK = dict(
    name="dark", bg="#0f1412", ink="#efe9dd", muted="#9aa097", soft="#727a73",
    hair="#2b3430", faint="#18201c", track="#cf5f39", track2="#4c2a1f",
    lane="#f4eee2", grass="#6db68b", grass2="#1b3326", chip="#0f1412",
)

# ----------------------------------------------------------------- fonts
_tt: dict[str, TTFont] = {}


def tt(key: str) -> TTFont:
    if key not in _tt:
        _tt[key] = TTFont(os.path.join(FONT_DIR, FONTS[key][0]))
    return _tt[key]


def has_glyph(key: str, ch: str) -> bool:
    return ord(ch) in tt(key).getBestCmap()


def text_width(key: str, size: float, s: str, ls: float = 0.0) -> float:
    f = tt(key)
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    upm = f["head"].unitsPerEm
    total = 0
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None:
            g = cmap.get(ord("?"))
        total += hmtx[g][0]
    return total * size / upm + ls * max(len(s) - 1, 0)


def wrap(key: str, size: float, s: str, width: float, ls: float = 0.0) -> list[str]:
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(key, size, trial, ls) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


_subset_cache: dict[tuple[str, str], str] = {}


def font_face(key: str, chars: set[str]) -> str:
    text = "".join(sorted(chars | {" "}))
    ck = (key, text)
    if ck not in _subset_cache:
        f = TTFont(os.path.join(FONT_DIR, FONTS[key][0]))
        opts = Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "tnum", "lnum"]
        opts.name_IDs = []
        opts.hinting = False
        sub = Subsetter(opts)
        sub.populate(text=text)
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        _subset_cache[ck] = base64.b64encode(buf.getvalue()).decode()
    _, fam, wt = FONTS[key]
    return (f"@font-face{{font-family:'{fam}';font-weight:{wt};"
            f"src:url(data:font/woff2;base64,{_subset_cache[ck]}) format('woff2')}}")


# ----------------------------------------------------------------- canvas
class Svg:
    def __init__(self, w: int, h: int, t: dict, label: str):
        self.w, self.h, self.t, self.label = w, h, t, label
        self.parts: list[str] = []
        self.chars: dict[str, set[str]] = {}
        self.css: list[str] = []
        self.defs: list[str] = []

    def add(self, s: str):
        self.parts.append(s)

    def text(self, x, y, s, key="B", size=15, fill=None, anchor="start",
             ls=0.0, extra="", upper=False):
        if upper:
            s = s.upper()
        for ch in s:
            if not has_glyph(key, ch):
                sys.exit(f"missing glyph {ch!r} (U+{ord(ch):04X}) in {key} for {s!r}")
        self.chars.setdefault(key, set()).update(s)
        fam = FONTS[key][1]
        wt = FONTS[key][2]
        fill = fill or self.t["ink"]
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{wt}" '
                 f'font-size="{size}" fill="{fill}"{a}{l} {extra}>{escape(s)}</text>')
        return text_width(key, size, s, ls)

    def para(self, x, y, s, key, size, width, lh, fill=None):
        lines = wrap(key, size, s, width)
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, key, size, fill)
        return y + (len(lines) - 1) * lh

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1, rx=0, extra=""):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        r = f' rx="{rx}"' if rx else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{r} fill="{fill}"{s} {extra}/>')

    def line(self, x1, y1, x2, y2, stroke, sw=1, extra=""):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=1, extra="", inner=""):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        if inner:
            self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"{s} {extra}>{inner}</circle>')
        else:
            self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"{s} {extra}/>')

    def path(self, d, fill="none", stroke=None, sw=1, extra=""):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<path d="{d}" fill="{fill}"{s} {extra}/>')

    def render(self) -> str:
        faces = "".join(font_face(k, v) for k, v in self.chars.items())
        css = faces + "".join(self.css)
        defs = "".join(self.defs)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.label)}">'
                f'<defs><style>{css}</style>'
                f'<clipPath id="card"><rect width="{self.w}" height="{self.h}" rx="14"/></clipPath>{defs}</defs>'
                f'<g clip-path="url(#card)"><rect width="{self.w}" height="{self.h}" fill="{self.t["bg"]}"/>'
                + "".join(self.parts) +
                f'</g><rect x="0.5" y="0.5" width="{self.w-1}" height="{self.h-1}" rx="14" '
                f'fill="none" stroke="{self.t["hair"]}"/></svg>')


def save(name: str, svg: Svg):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{name}-{svg.t['name']}.svg")
    data = svg.render()
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)
    print(f"  {os.path.basename(p):34s} {len(data)/1024:6.1f} KB")


def arrow_ne(c: Svg, x, y, size, stroke, sw=1.6):
    """A drawn ↗ so we never depend on a font having the glyph."""
    c.path(f"M{x:.1f} {y+size:.1f} L{x+size:.1f} {y:.1f} M{x+size*0.3:.1f} {y:.1f} "
           f"L{x+size:.1f} {y:.1f} L{x+size:.1f} {y+size*0.7:.1f}",
           stroke=stroke, sw=sw, extra='stroke-linecap="round" stroke-linejoin="round"')


def lanes(c: Svg, x, y, w, n, lh, t, numbers=True, labels=None, start_x=None):
    """A straight stretch of track: n lanes of height lh."""
    c.rect(x, y, w, n * lh, fill=t["track"])
    for i in range(n + 1):
        c.line(x, y + i * lh, x + w, y + i * lh, t["lane"], 1.4 if i in (0, n) else 1)
    if numbers:
        for i in range(n):
            c.text(x + 14, y + i * lh + lh / 2 + 5, str(i + 1), "D", lh * 0.62,
                   t["lane"], anchor="middle")
    if labels:
        for i, lab in enumerate(labels):
            c.text(x + 34, y + i * lh + lh / 2 + 4, lab, "M", 11, t["lane"], ls=0.4)


# ================================================================== HERO
def hero(t):
    H = 490
    c = Svg(W, H, t, "Ishan Ganguly, bib 007. Builds AI systems where the model proposes and "
                     "deterministic code decides. CS at BITS Pilani, Bengaluru. State-level athlete.")
    c.text(40, 58, "BENGALURU  ·  CS AT BITS PILANI  ·  STATE-LEVEL ATHLETE", "DS", 14,
           t["muted"], ls=2.4)
    c.text(36, 158, "ISHAN", "D", 112, t["ink"], ls=1)
    c.text(36, 258, "GANGULY", "D", 112, t["ink"], ls=1)
    c.rect(40, 286, 44, 4, fill=t["track"])
    c.text(40, 326, "I build AI systems where the model proposes", "BM", 22, t["ink"])
    c.text(40, 354, "and deterministic code decides.", "BM", 22, t["ink"])

    # ---- race bib, pinned on slightly crooked
    bx, by, bw, bh = 560, 66, 264, 236
    c.add(f'<g transform="rotate(-3.5 {bx+bw/2} {by+bh/2})">')
    c.rect(bx + 6, by + 8, bw, bh, fill=t["ink"], rx=6, extra='opacity="0.10"')
    c.rect(bx, by, bw, bh, fill=t["lane"], stroke=t["hair"], rx=6)
    c.rect(bx, by, bw, 40, fill=t["track"], rx=6)
    c.rect(bx, by + 30, bw, 10, fill=t["track"])
    c.text(bx + bw / 2, by + 26, "AGENTS · RETRIEVAL · SYSTEMS", "DS", 14, t["lane"],
           anchor="middle", ls=2.2)
    c.text(bx + bw / 2, by + 168, "007", "D", 136, "#1c1a16", anchor="middle", ls=2)
    c.text(bx + 26, by + 198, "I. GANGULY", "DS", 15, "#1c1a16", ls=2)
    c.text(bx + 26, by + 215, "@ISHAN007-BOT", "M", 10, "#6a6458", ls=0.6)
    # timing chip barcode
    xx = bx + bw - 22
    for i, wdt in enumerate([2, 1, 3, 1, 1, 2, 1, 3, 2, 1, 1, 2, 3, 1, 2]):
        xx -= wdt + 2
        c.rect(xx, by + 186, wdt, 28, fill="#1c1a16")
    for px, py in [(bx + 13, by + 53), (bx + bw - 13, by + 53), (bx + 13, by + bh - 11),
                   (bx + bw - 13, by + bh - 11)]:
        c.circle(px, py, 5.2, fill="#d8cfbd")
        c.circle(px, py, 2.4, fill=t["bg"])
    c.add("</g>")

    # ---- the straight, with a runner on lane 4
    ty, lh = 388, 17
    n = 6
    lanes(c, 0, ty, W, n, lh, t, numbers=False)
    c.line(96, ty, 96, ty + n * lh, t["lane"], 3)            # start line
    for i in range(n):
        c.text(80, ty + i * lh + 12.5, str(i + 1), "DS", 13, t["lane"], anchor="middle")
    labels = ["agents", "retrieval", "systems", "voice", "devsecops", "open source"]
    for i, lab in enumerate(labels):
        c.text(110, ty + i * lh + 12, lab, "M", 10, t["lane"], ls=0.8,
               extra='opacity="0.85"')
    # finish line, checkered
    fx = 812
    sq = lh * n / 14
    for i in range(14):
        for j in range(2):
            if (i + j) % 2 == 0:
                c.rect(fx + j * sq, ty + i * sq, sq, sq, fill=t["lane"])
    # runner
    c.defs.append(
        f'<linearGradient id="trail" x1="0" x2="1"><stop offset="0" stop-color="{t["lane"]}" '
        f'stop-opacity="0"/><stop offset="1" stop-color="{t["lane"]}" stop-opacity="0.9"/></linearGradient>')
    ry = ty + 3 * lh + lh / 2
    c.add(f'<g><rect x="-90" y="{ry-1.5}" width="90" height="3" fill="url(#trail)"/>'
          f'<circle cx="0" cy="{ry}" r="4.5" fill="{t["lane"]}"/>'
          f'<animateTransform attributeName="transform" type="translate" '
          f'values="96 0;812 0;812 0" keyTimes="0;0.7;1" dur="5s" repeatCount="indefinite" '
          f'calcMode="spline" keySplines="0.35 0 0.25 1;0 0 1 1"/></g>')
    w1 = c.text(W - 40 - text_width("MM", 11, "25+ PRs merged at INNO-TECH"), ty - 14,
                "25+ PRs merged at INNO-TECH", "MM", 11, t["ink"])
    c.text(W - 40 - w1 - 10, ty - 14, "OPEN SOURCE", "DS", 12, t["track"], anchor="end", ls=1.8)
    save("hero", c)


# ================================================================ BUTTONS
def button(name, label, t):
    tw = text_width("BS", 15, label, 0.3)
    w = int(tw + 24 + 30)
    c = Svg(w, 40, t, label)
    c.parts.clear()
    c.text(20, 25.5, label, "BS", 15, t["ink"], ls=0.3)
    arrow_ne(c, 20 + tw + 10, 15, 9, t["track"])
    svg = c.render().replace(f'rx="14"', 'rx="20"')
    p = os.path.join(OUT, f"btn-{name}-{t['name']}.svg")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    print(f"  {os.path.basename(p):34s} {len(svg)/1024:6.1f} KB")


# ================================================================= PLATES
FIG_X0, FIG_X1 = 486, 846


def plate(slug, t, n, line, title, subtitle, stack, desc, marks, note, figure, label):
    # measure the left column first so the card is exactly as tall as it needs
    sub_lines = wrap("BM", 19, subtitle, 400)
    desc_lines = wrap("B", 15, desc, 400)
    y_sub = 138
    y_stack = y_sub + (len(sub_lines) - 1) * 25 + 28
    y_desc = y_stack + 32
    y_desc_end = y_desc + (len(desc_lines) - 1) * 22
    H = max(450, int(y_desc_end + 170))
    c = Svg(W, H, t, label)
    # lane strip along the top
    c.rect(0, 0, W, 10, fill=t["track"])
    for x in range(0, W, 28):
        c.rect(x + 6, 4.3, 14, 1.4, fill=t["lane"], extra='opacity="0.7"')

    c.text(40, 54, f"HEAT {n:02d}  ·  {line}", "DS", 14, t["track"], ls=2.6, upper=True)
    c.text(38, 104, title, "D", 50, t["ink"], ls=0.4)
    for i, ln in enumerate(sub_lines):
        c.text(40, y_sub + i * 25, ln, "BM", 19, t["ink"])
    if text_width("M", 11.5, stack) > 410:
        sys.exit(f"stack line too long for {slug}: {stack!r}")
    c.text(40, y_stack, stack, "M", 11.5, t["soft"])
    for i, ln in enumerate(desc_lines):
        c.text(40, y_desc + i * 22, ln, "B", 15, t["muted"])

    my = H - 116
    for i, (num, lab) in enumerate(marks):
        x = 40 + i * 140
        c.text(x, my, num, "D", 38, t["ink"])
        for j, ln in enumerate(wrap("DS", 12.5, lab.upper(), 122, 0.9)):
            c.text(x, my + 22 + j * 15, ln, "DS", 12.5, t["muted"], ls=0.9)

    c.line(40, H - 52, W - 40, H - 52, t["hair"])
    c.path(f"M40 {H-30} l9 0 m-4 -4 l4 4 l-4 4", stroke=t["track"], sw=1.6,
           extra='stroke-linecap="round" stroke-linejoin="round"')
    c.text(58, H - 26, note, "M", 12, t["muted"])
    figure(c, t, H)
    save(slug, c)


def caption(c, x, y, s, t, anchor="start"):
    c.text(x, y, s, "DS", 12.5, t["soft"], ls=1.6, upper=True, anchor=anchor)


# ---- 03 Typeahead: the hash ring is a running track
def fig_typeahead(c, t, H):
    cx, cy = 690, 200
    R1, R2 = 128, 92
    caption(c, FIG_X0, 58, "consistent-hash ring · md5 · virtual nodes", t)
    c.circle(cx, cy, (R1 + R2) / 2, stroke=t["track"], sw=R1 - R2)
    for r in (R2, R2 + 12, R2 + 24, R1 - 12, R1):
        c.circle(cx, cy, r, stroke=t["lane"], sw=1 if r not in (R1, R2) else 1.4)
    c.circle(cx, cy, R2 - 1, fill=t["grass2"])
    nodes = {"a": "#f4eee2", "b": "#1c1a16", "c": t["grass"]}
    seq = "abcbacbcacab"
    for i, nd in enumerate(seq):
        ang = math.radians(i * 30 + 8 + (i % 3) * 5)
        x = cx + math.cos(ang) * (R1 + R2) / 2
        y = cy + math.sin(ang) * (R1 + R2) / 2
        c.add(f'<rect x="{x-6:.1f}" y="{y-6:.1f}" width="12" height="12" rx="2" fill="{nodes[nd]}" '
              f'stroke="{t["track"]}" stroke-width="1.5" transform="rotate({i*30+8+(i%3)*5:.0f} {x:.1f} {y:.1f})"/>')
    # a prefix hashes onto the ring and walks clockwise to its owner
    a0, a1 = 200, 248   # degrees: hash point -> owning vnode (index 8 sits at 255)
    rr = (R1 + R2) / 2
    hx, hy = cx + math.cos(math.radians(a0)) * rr, cy + math.sin(math.radians(a0)) * rr
    c.line(FIG_X0 + 4, hy - 46, hx - 10, hy - 4, t["ink"], 1.2, extra='stroke-dasharray="3 3"')
    c.text(FIG_X0, hy - 54, 'md5("wea")', "MM", 12, t["ink"])
    end = 255 + (8 % 3) * 5 - 15
    ex, ey = cx + math.cos(math.radians(end)) * rr, cy + math.sin(math.radians(end)) * rr
    arc = f"M{hx:.1f} {hy:.1f} A{rr} {rr} 0 0 1 {ex:.1f} {ey:.1f}"
    c.path(arc, stroke=t["ink"], sw=2.4, extra='stroke-linecap="round" opacity="0.9"')
    c.circle(hx, hy, 5, fill=t["ink"], stroke=t["lane"], sw=2)
    c.add(f'<circle r="5" fill="{t["lane"]}" stroke="{t["ink"]}" stroke-width="2">'
          f'<animateMotion dur="3s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.5;1" '
          f'calcMode="linear" path="{arc}"/></circle>')
    # infield
    c.text(cx, cy - 22, "INFIELD", "DS", 11.5, t["grass"], anchor="middle", ls=2.4)
    c.text(cx, cy + 4, "trie, top-10", "BS", 15, t["ink"], anchor="middle")
    c.text(cx, cy + 22, "at every node", "B", 13, t["muted"], anchor="middle")
    c.text(cx, cy + 44, "miss → suggest()", "M", 10.5, t["muted"], anchor="middle")
    # legend
    ly = cy + R1 + 30
    lx = FIG_X0 + 10
    for i, (nd, lab) in enumerate([("a", "redis-a"), ("b", "redis-b"), ("c", "redis-c")]):
        x = lx + i * 92
        c.rect(x, ly - 10, 11, 11, fill=nodes[nd], stroke=t["track"], sw=1.5, rx=2)
        c.text(x + 17, ly, lab, "M", 11, t["muted"])
    c.text(FIG_X0 + 10, ly + 22, "add or remove a node: only ~1/N keys move", "M", 11, t["muted"])


# ---- 04 Synapse: head to head
def fig_synapse(c, t, H):
    x0, x1 = FIG_X0, FIG_X1
    caption(c, x0, 58, "the hop vector-only retrieval can't make", t)
    labs = ["OpenAI", "Amodei", "Anthropic"]
    ny, gap = 110, 46
    widths = [text_width("BS", 13, l) + 28 for l in labs]
    total = sum(widths) + gap * 2
    xs, x = [], x0 + (x1 - x0 - total) / 2
    for w_ in widths:
        xs.append((x, x + w_))
        x += w_ + gap
    for i in range(2):
        xa, xb = xs[i][1], xs[i + 1][0]
        c.line(xa + 4, ny, xb - 4, ny, t["ink"], 1.6)
        c.path(f"M{xb-11} {ny-5} L{xb-4} {ny} L{xb-11} {ny+5}", stroke=t["ink"], sw=1.6,
               extra='stroke-linejoin="round"')
        c.text((xa + xb) / 2, ny - 10, f"hop {i+1}", "M", 10.5, t["muted"], anchor="middle")
    for lab, (a, b) in zip(labs, xs):
        c.rect(a, ny - 19, b - a, 38, fill=t["bg"], stroke=t["track"], sw=2, rx=19)
        c.text((a + b) / 2, ny + 5, lab, "BS", 13, t["ink"], anchor="middle")
    c.text(x0, ny + 54, "link entities → walk N hops → fuse with vector top-k", "M", 11,
           t["muted"])

    caption(c, x0, 214, "multi-hop context recall", t)
    caption(c, x1, 214, "4-question pilot", t, anchor="end")
    ly, lh = 228, 44
    fin = x1 - 12
    c.rect(x0, ly, x1 - x0, lh * 2, fill=t["track"])
    for i in range(3):
        c.line(x0, ly + i * lh, x1, ly + i * lh, t["lane"], 1.2)
    span = fin - (x0 + 30)
    for i, (lab, v) in enumerate([("vector-only RAG", 0.48), ("graph RAG", 0.92)]):
        y = ly + i * lh
        c.text(x0 + 12, y + lh / 2 + 7, str(i + 1), "D", 20, t["lane"], anchor="middle")
        c.text(x0 + 30, y + 16, lab, "M", 10.5, t["lane"])
        bx = x0 + 30 + span * v
        c.line(x0 + 30, y + 30, bx, y + 30, t["lane"], 4, extra='stroke-linecap="round"')
        c.circle(bx, y + 30, 6, fill=t["lane"])
        c.text(bx, y + 21, f"{v:.2f}", "D", 18, t["lane"], anchor="middle")
    for k in range(5):
        x = x0 + 30 + span * k / 4
        c.line(x, ly + lh * 2, x, ly + lh * 2 + 6, t["soft"])
        c.text(x, ly + lh * 2 + 20, f"{k/4:.2f}".rstrip("0").rstrip(".") if k else "0", "M",
               10, t["soft"], anchor="middle")
    c.text(x0, H - 72, "faithfulness", "M", 12, t["soft"])
    c.text(x1, H - 72, "1.00 · 1.00 (unchanged)", "MM", 12, t["ink"], anchor="end")


# ---- 06 Bloodlink: relay, and a disqualification
def fig_bloodlink(c, t, H):
    x0, x1 = FIG_X0, FIG_X1
    caption(c, x0, 58, "every commit runs the relay", t)
    stages = ["lint", "test", "scan", "trivy", "ghcr", "eks"]
    ly, lh = 104, 44
    c.rect(x0, ly, x1 - x0, lh * 2, fill=t["track"])
    for i in range(3):
        c.line(x0, ly + i * lh, x1, ly + i * lh, t["lane"], 1.2)
    sx = [x0 + 40 + i * ((x1 - x0 - 60) / 5) for i in range(6)]
    for s, x in zip(stages, sx):
        c.rect(x - 9, ly, 18, lh * 2, fill=t["lane"], extra='opacity="0.13"')
        c.line(x, ly - 4, x, ly + lh * 2 + 4, t["lane"], 1, extra='stroke-dasharray="2 3"')
        c.text(x, ly - 12, s, "DS", 13, t["muted"], anchor="middle", ls=1.2, upper=True)
    # lane 1: main goes all the way
    y1 = ly + lh / 2
    c.text(x0 + 12, y1 + 7, "1", "D", 20, t["lane"], anchor="middle")
    c.line(x0 + 26, y1, sx[-1], y1, t["lane"], 3, extra='stroke-linecap="round"')
    for x in sx:
        c.circle(x, y1, 4.5, fill=t["lane"])
    c.text(sx[-1] - 8, y1 - 8, "main · deployed", "M", 10, t["lane"], anchor="end")
    # lane 2: PR #1 is stopped at test
    y2 = ly + lh * 1.5
    c.text(x0 + 12, y2 + 7, "2", "D", 20, t["lane"], anchor="middle")
    c.line(x0 + 26, y2, sx[1], y2, t["lane"], 3, extra='stroke-linecap="round"')
    c.circle(sx[0], y2, 4.5, fill=t["lane"])
    c.line(sx[1] + 10, y2, sx[-1], y2, t["lane"], 1.2, extra='stroke-dasharray="2 5" opacity="0.5"')
    # DQ flag
    c.rect(sx[1] - 15, y2 - 13, 30, 26, fill=t["ink"], rx=3)
    c.text(sx[1], y2 + 6, "DQ", "D", 18, t["bg"], anchor="middle", ls=0.5)
    c.text(sx[1] + 24, y2 + 4, "PR #1 · no image built", "M", 10, t["lane"])

    yy = ly + lh * 2 + 36
    c.text(x0, yy, 'PR #1 "Use O+ stock for A- patients"', "MM", 12, t["ink"])
    c.text(x0, yy + 20, "failed test_compatibility_pairs[O+-A--False]", "M", 11.5, t["muted"])
    caption(c, x0, yy + 58, "allocation rule, a pure function", t)
    rules = ["compatible ABO/Rh only", "exact group first, O- last", "nearest expiry first (FEFO)",
             "emergencies before routine"]
    for i, r in enumerate(rules):
        y = yy + 80 + i * 19
        x = x0
        c.text(x, y, f"{i+1}", "MM", 11.5, t["track"])
        c.text(x + 14, y, r, "M", 11.5, t["muted"])


# ---- SpotHole: a report's run, and the laps I added
def fig_spothole(c, t, H):
    x0, x1 = FIG_X0, FIG_X1
    caption(c, x0, 58, "one report, start to finish", t)
    stages = ["snap", "clarity", "gps", "address", "post", "track"]
    ly, lh = 92, 40
    c.rect(x0, ly, x1 - x0, lh, fill=t["track"])
    c.line(x0, ly, x1, ly, t["lane"], 1.2)
    c.line(x0, ly + lh, x1, ly + lh, t["lane"], 1.2)
    sx = [x0 + 30 + i * ((x1 - x0 - 60) / 5) for i in range(6)]
    c.line(sx[0], ly + lh / 2, sx[-1], ly + lh / 2, t["lane"], 2.4, extra='stroke-linecap="round"')
    for s_, x in zip(stages, sx):
        c.circle(x, ly + lh / 2, 5, fill=t["lane"])
        c.text(x, ly + lh + 20, s_, "DS", 13, t["muted"], anchor="middle", ls=1.2, upper=True)
    c.add(f'<circle r="7" fill="{t["lane"]}" stroke="{t["ink"]}" stroke-width="2" cx="{sx[-1]:.1f}" cy="{ly+lh/2:.1f}">'
          f'<animate attributeName="cx" values="{sx[0]:.1f};{sx[-1]:.1f};{sx[-1]:.1f}" keyTimes="0;0.7;1" '
          f'dur="5s" repeatCount="indefinite"/></circle>')
    c.text(x0, ly + lh + 44, "blurry → retake  ·  no GPS → type the address", "M", 11,
           t["muted"])

    caption(c, x0, 208, "the api behind it", t)
    groups = [("/auth", ["signup", "signin", "guest-signin", "convert-guest"]),
              ("/pothole", ["upload", "dashboard", "recent-reports", "report/:id"])]
    for gi, (base, eps) in enumerate(groups):
        y = 226 + gi * 56
        c.text(x0, y + 15, base, "MM", 12.5, t["track"])
        xx = x0 + 78
        for k, ep in enumerate(eps):
            w_ = text_width("M", 11, ep) + 16
            if k == 2:
                xx, y = x0 + 78, y + 26
            c.rect(xx, y, w_, 22, fill=t["faint"], stroke=t["hair"], rx=4)
            c.text(xx + 8, y + 15, ep, "M", 11, t["ink"])
            xx += w_ + 8
    c.text(x0, H - 72, "report status", "M", 12, t["soft"])
    c.text(x1, H - 72, "pending → acknowledged → resolved", "MM", 12, t["ink"], anchor="end")


# ---- VoxField: every lane has a fallback lane
def fig_voxfield(c, t, H):
    x0, x1 = FIG_X0, FIG_X1
    caption(c, x0, 58, "when a layer drops, the next one runs", t)
    rows = [("speech", ["Cloud STT", "Web Speech"]),
            ("extraction", ["Vertex AI", "AI Studio", "rules"]),
            ("saving", ["API", "IndexedDB queue"]),
            ("lookup", ["asset code", "fuzzy match"])]
    ly, lh = 82, 52
    lab_w = 84
    c.rect(x0, ly, x1 - x0, lh * len(rows), fill=t["track"])
    for i in range(len(rows) + 1):
        c.line(x0, ly + i * lh, x1, ly + i * lh, t["lane"], 1.2)
    for i, (name, steps) in enumerate(rows):
        y = ly + i * lh
        c.text(x0 + 12, y + 20, name, "DS", 13, t["lane"], ls=1.4, upper=True)
        c.text(x0 + 12, y + 38, f"{len(steps)} layers", "M", 10, t["lane"], extra='opacity="0.75"')
        span = x1 - (x0 + lab_w) - 14
        seg = span / len(steps)
        for k, st in enumerate(steps):
            sx = x0 + lab_w + k * seg
            chip_w = seg - 14
            first = k == 0
            c.rect(sx, y + 12, chip_w, lh - 24, rx=4,
                   fill=t["lane"] if first else "none", stroke=t["lane"], sw=1.2)
            fs = 11.5
            if text_width("M", fs, st) > chip_w - 10:
                sys.exit(f"chip text too wide: {st!r}")
            c.text(sx + chip_w / 2, y + lh / 2 + 4, st, "M", fs,
                   "#1c1a16" if first else t["lane"], anchor="middle")
            if k < len(steps) - 1:
                ax = sx + chip_w + 2
                c.path(f"M{ax} {y+lh/2} l8 0 m-4 -4 l4 4 l-4 4", stroke=t["lane"], sw=1.4,
                       extra='stroke-linecap="round" stroke-linejoin="round"')
    yy = ly + lh * len(rows) + 30
    c.text(x0, yy, "6 fields extracted, each with its own confidence;", "M", 11.5, t["muted"])
    c.text(x0, yy + 19, "low confidence asks for a re-recording, never a guess", "M", 11.5, t["muted"])
    c.text(x0, H - 72, "languages · assets", "M", 12, t["soft"])
    c.text(x1, H - 72, "EN HI ES · 40 assets, 11 types", "MM", 12, t["ink"], anchor="end")


# ================================================================ OFF KEYS
def off_keyboard(t):
    H = 330
    c = Svg(W, H, t, "Off the keyboard: state-level cricketer, state-level footballer, "
                     "state-level track and field athlete. Paints. Watches films.")
    # a painted stroke behind the heading
    c.path("M30 52 C 120 34, 260 40, 368 44 C 382 45, 392 58, 380 68 C 300 76, 140 80, 44 76 "
           "C 26 74, 20 58, 30 52 Z", fill=t["track"], extra='opacity="0.92"')
    c.path("M60 74 C 160 70, 260 72, 350 66", stroke=t["track"], sw=3,
           extra='opacity="0.5" stroke-linecap="round"')
    c.text(44, 72, "OFF THE KEYBOARD", "D", 34, t["lane"], ls=1.5)
    c.text(W - 40, 70, "three sports at state level, and a paintbrush", "M", 12, t["soft"],
           anchor="end")

    cards = [("CRICKET", "state level"), ("FOOTBALL", "state level"),
             ("TRACK & FIELD", "state level")]
    cw, gap, cy0 = 252, 22, 104
    for i, (name, lvl) in enumerate(cards):
        x = 40 + i * (cw + gap)
        c.rect(x, cy0, cw, 132, fill=t["faint"], rx=10)
        ix, iy = x + 52, cy0 + 66
        ink, acc = t["ink"], t["track"]
        if name == "CRICKET":
            c.add(f'<g transform="rotate(-35 {ix} {iy})">'
                  f'<rect x="{ix-9}" y="{iy-30}" width="18" height="52" rx="5" fill="none" stroke="{ink}" stroke-width="1.8"/>'
                  f'<rect x="{ix-3}" y="{iy-50}" width="6" height="21" rx="2" fill="{ink}"/></g>')
            c.circle(ix + 26, iy + 26, 9, fill=acc)
            c.path(f"M{ix+19} {iy+21} Q {ix+26} {iy+26} {ix+33} {iy+31}", stroke=t["lane"], sw=1.2)
        elif name == "FOOTBALL":
            c.circle(ix, iy, 28, fill="none", stroke=ink, sw=1.8)
            pts = [(ix + 11 * math.cos(math.radians(-90 + k * 72)),
                    iy + 11 * math.sin(math.radians(-90 + k * 72))) for k in range(5)]
            c.path("M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts) + " Z", fill=acc)
            for px, py in pts:
                dx, dy = px - ix, py - iy
                c.line(px, py, ix + dx * 2.5, iy + dy * 2.5, ink, 1.4)
        else:
            # a hurdle on a lane line
            c.line(ix - 36, iy + 26, ix + 36, iy + 26, ink, 1.8)
            c.line(ix - 36, iy + 34, ix + 36, iy + 34, acc, 1.8)
            c.rect(ix - 26, iy - 18, 4, 44, fill=ink)
            c.rect(ix + 22, iy - 18, 4, 44, fill=ink)
            c.rect(ix - 32, iy - 22, 64, 11, fill=t["bg"], stroke=ink, sw=1.6)
            for k in range(4):
                c.rect(ix - 32 + k * 16, iy - 22, 8, 11, fill=acc)
            c.rect(ix - 30, iy + 22, 12, 4, fill=ink)
            c.rect(ix + 18, iy + 22, 12, 4, fill=ink)
        fs = 26
        while text_width("D", fs, name, 0.8) > cw - 116:
            fs -= 1
        c.text(x + 100, cy0 + 60, name, "D", fs, t["ink"], ls=0.8)
        c.text(x + 100, cy0 + 82, lvl.upper(), "DS", 13, t["track"], ls=2)

    # painting + films
    y2 = 264
    c.rect(40, y2, 387, 38, fill="none", stroke=t["hair"], rx=8)
    c.path(f"M58 {y2+27} L76 {y2+9}", stroke=t["ink"], sw=2.2, extra='stroke-linecap="round"')
    c.path(f"M76 {y2+9} q6 -6 9 -3 q3 3 -3 9 z", fill=t["track"])
    c.path(f"M54 {y2+30} q2 -4 5 -3", stroke=t["track"], sw=3, extra='stroke-linecap="round"')
    c.text(100, y2 + 25, "Painting", "BS", 16, t["ink"])
    c.text(100 + text_width("BS", 16, "Painting") + 10, y2 + 25, "canvas, not CSS", "B", 15,
           t["muted"])
    x2 = 453
    c.rect(x2, y2, 387, 38, fill="none", stroke=t["hair"], rx=8)
    c.rect(x2 + 16, y2 + 10, 28, 19, fill="none", stroke=t["ink"], sw=1.8, rx=2)
    for k in range(4):
        c.rect(x2 + 19 + k * 6.5, y2 + 12, 3, 3, fill=t["track"])
        c.rect(x2 + 19 + k * 6.5, y2 + 24, 3, 3, fill=t["track"])
    c.text(x2 + 60, y2 + 25, "Films", "BS", 16, t["ink"])
    c.text(x2 + 60 + text_width("BS", 16, "Films") + 10, y2 + 25, "a watchlist that only grows",
           "B", 15, t["muted"])
    save("off-keyboard", c)


# ================================================================== MAIN
def main():
    for t in (LIGHT, DARK):
        print(f"[{t['name']}]")
        hero(t)
        button("linkedin", "LinkedIn", t)
        button("email", "Email", t)
        button("repos", "All repositories", t)

        plate("heat-01-spothole", t, 1, "main project · mobile",
              "SpotHole",
              "Report a pothole with one photo, and keep it on record until it is fixed.",
              "React Native · Expo · Node.js · Express · MongoDB",
              "Snap a pothole: a blurry photo is sent back for a retake, the GPS location is "
              "tagged and turned into an address, and the report is posted to Twitter so it "
              "can't be quietly ignored. Every report is tracked on a dashboard until the road "
              "is fixed.",
              [("6", "stages, snap to track"), ("8", "API endpoints"),
               ("v1.1.0", "Android APK release")],
              "Report first, sign up later: guests can convert to a full account.",
              fig_spothole,
              "SpotHole, a pothole reporting app. A report runs snap, "
              "clarity check, GPS, address, post, track; status goes pending, acknowledged, resolved.")

        plate("heat-02-bloodlink", t, 2, "devsecops · full stack",
              "Bloodlink",
              "A blood bank system, and a pipeline that knows blood types.",
              "FastAPI · React 19 · Postgres 16 · Helm · Terraform · EKS",
              "Allocation is a pure function. Every commit runs lint, tests, secret and dependency "
              "scans and a Trivy gate before an image reaches GHCR, then deploys to EKS through "
              "GitHub OIDC, with no stored AWS keys, and a Helm rollout that waits for a smoke test.",
              [("97%", "coverage, 81 tests"), ("2–6", "pods, autoscaled under load"),
               ("66", "terraform resources")],
              "PR #1 looked helpful. A compatibility test disagreed, so nothing was deployed.",
              fig_bloodlink,
              "Bloodlink. CI relay: lint, test, scan, trivy, ghcr, eks. PR #1 'Use O+ stock for "
              "A- patients' disqualified at test; no image built.")

        plate("heat-03-synapse", t, 3, "retrieval",
              "Synapse",
              "Graph RAG for the questions vector search can't connect.",
              "FastAPI · Neo4j 5 · bge-small · Llama 3.3 70B · Next.js 14",
              "An LLM extracts typed entities and edges into Neo4j. At query time the question is "
              "linked to entities, an N-hop subgraph is walked, and its chunks are fused with "
              "vector top-k. The subgraph streams first, so the graph draws before the first token.",
              [("0.92", "multi-hop context recall"), ("0.48", "vector-only baseline"),
               ("1.00", "faithfulness, both")],
              "Same questions. Same LLM. Same chunks. Only the graph differs.",
              fig_synapse,
              "Synapse. OpenAI to Amodei to Anthropic, two hops. Multi-hop context recall 0.48 "
              "vector-only versus 0.92 graph RAG on a 4-question pilot.")

        plate("heat-04-voxfield", t, 4, "voice · agents",
              "VoxField",
              "Work orders by voice, for technicians who can't look at a screen.",
              "React PWA · FastAPI · Gemini 2.5 Flash · Cloud STT/TTS",
              "A technician talks; Gemini pulls six work-order fields out of the speech, scores "
              "each one, and asks again when it isn't sure. Every cloud capability has a "
              "fallback, so a dead signal degrades the app instead of breaking it, and the "
              "offline queue catches up on reconnect.",
              [("~1–2 s", "typical query, target < 3 s"), ("6", "fields, each scored"),
               ("51", "tests passing")],
              "Every cloud capability has a fallback, so the app never fully breaks.",
              fig_voxfield,
              "VoxField. Speech, extraction, saving and lookup each fall back a layer at a time: "
              "Cloud STT to Web Speech, Vertex AI to AI Studio to rules, API to an IndexedDB queue, "
              "exact asset code to fuzzy match.")

        plate("heat-05-typeahead", t, 5, "systems",
              "Typeahead Engine",
              "Search-as-you-type over 200,000 real Bing queries.",
              "Python · FastAPI · Redis × 3 · SQLite · Docker Compose",
              "A trie keeps the top ten at every node. A hand-written consistent-hash ring sends "
              "each prefix to one of three Redis nodes. A batch writer folds thousands of "
              "searches into a few SQLite transactions, and trending blends all-time counts with "
              "time-decayed recent activity.",
              [("~6.5 ms", "p95 suggestion latency"), ("~97%", "cache hit rate"),
               ("~99.6%", "fewer DB writes")],
              "Ring, trie and batch writer are hand-written, so every decision is explainable.",
              fig_typeahead,
              "Typeahead engine. A consistent-hash ring drawn as a running track with three Redis "
              "nodes; the trie sits in the infield. About 6.5 ms p95.")

        off_keyboard(t)


if __name__ == "__main__":
    main()
