"""Small SVG charts drawn when the site is built. Colours come from site.css classes, so light and dark both work.
Each mark carries a <title>, which browsers show on hover."""

from __future__ import annotations

import math
from html import escape

from markupsafe import Markup

from izbori_hr.i18n import fmt_int, fmt_pct, t
from izbori_hr.stats import Digits


def _nice_step(top: float, ticks: int = 4) -> float:
    raw = top / ticks if top > 0 else 1
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def _col(x: float, y: float, w: float, h: float, r: float) -> str:
    """Path for a column with rounded top corners and a square base."""
    r = max(0.0, min(r, w / 2, h))
    return (f"M{x:.2f},{y + h:.2f}V{y + r:.2f}Q{x:.2f},{y:.2f} {x + r:.2f},{y:.2f}"
            f"H{x + w - r:.2f}Q{x + w:.2f},{y:.2f} {x + w:.2f},{y + r:.2f}V{y + h:.2f}Z")


def histogram(bins: list[int], loc: str) -> Markup:
    w, h = 640, 190
    left, right, top, bottom = 40, 20, 10, 24
    pw, ph = w - left - right, h - top - bottom
    n = len(bins)
    peak = max(bins) if bins else 0
    step = _nice_step(peak)
    ymax = max(step, math.ceil(peak / step) * step) if peak else 1
    slot = pw / n
    bar = max(1.0, slot - 2)
    unit = t("stations", loc).lower()
    parts = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(t("hist_heading", loc))}">']
    y = 0
    while y <= ymax + 1e-9:
        yy = top + ph - ph * y / ymax
        parts.append(f'<line class="grid" x1="{left}" x2="{w - right}" y1="{yy:.1f}" y2="{yy:.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 6}" y="{yy + 4:.1f}" text-anchor="end">{fmt_int(int(y), loc)}</text>')
        y += step
    for i, count in enumerate(bins):
        if not count:
            continue
        bh = ph * count / ymax
        x = left + i * slot + (slot - bar) / 2
        label = "100 %" if i == 100 else f"{i}–{i + 1} %"
        parts.append(f'<path class="bar" d="{_col(x, top + ph - bh, bar, bh, 1.5)}">'
                     f'<title>{escape(label)}: {fmt_int(count, loc)} ({unit})</title></path>')
    parts.append(f'<line class="axis" x1="{left}" x2="{w - right}" y1="{top + ph}" y2="{top + ph}"/>')
    for p in (0, 25, 50, 75, 100):
        x = left + p * slot + slot / 2
        parts.append(f'<text class="tick" x="{x:.1f}" y="{h - 6}" text-anchor="middle">{p} %</text>')
    parts.append("</svg>")
    return Markup("".join(parts))


def digits(d: Digits, loc: str) -> Markup:
    w, h = 300, 140
    left, right, top, bottom = 34, 6, 8, 22
    pw, ph = w - left - right, h - top - bottom
    shares = [c / d.n for c in d.counts]
    ymax = max(0.15, math.ceil(max(shares) * 20) / 20)
    slot = pw / 10
    bar = min(24.0, slot - 6)
    parts = [f'<svg class="chart small" viewBox="0 0 {w} {h}" role="img" '
             f'aria-label="{escape(t("digits_heading", loc))}">']
    for y in (0, 0.05, 0.10, 0.15, 0.20, 0.25):
        if y > ymax + 1e-9:
            break
        yy = top + ph - ph * y / ymax
        parts.append(f'<line class="grid" x1="{left}" x2="{w - right}" y1="{yy:.1f}" y2="{yy:.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 5}" y="{yy + 4:.1f}" text-anchor="end">{fmt_pct(y, loc, 0)}</text>')
    for i, share in enumerate(shares):
        bh = ph * share / ymax
        x = left + i * slot + (slot - bar) / 2
        parts.append(f'<path class="bar" d="{_col(x, top + ph - bh, bar, bh, 4)}">'
                     f'<title>{i}: {fmt_pct(share, loc)} ({fmt_int(d.counts[i], loc)})</title></path>')
        parts.append(f'<text class="tick" x="{x + bar / 2:.1f}" y="{h - 6}" text-anchor="middle">{i}</text>')
    ref = top + ph - ph * 0.10 / ymax
    parts.append(f'<line class="ref" x1="{left}" x2="{w - right}" y1="{ref:.1f}" y2="{ref:.1f}"/>')
    parts.append(f'<line class="axis" x1="{left}" x2="{w - right}" y1="{top + ph}" y2="{top + ph}"/>')
    parts.append("</svg>")
    return Markup("".join(parts))


def trend(points: list[dict], label: str, ref_label: str, loc: str, zero: bool = False, hits: bool = True) -> Markup:
    """A small line chart across elections, oldest on the left (the Serbian archive's): this place in the accent
    colour, the area it is compared with as a dashed grey line, the newest values labelled at the right, and each
    election's column titled with both values. points: {"kind", "year", "title", "v", "r"}, oldest first; values
    are shares (0–1) or None. A year is written under its first election only, where it doesn't touch the one before;
    the parliament's dots are filled, the president's rounds hollow."""
    vals = [p[k] for p in points for k in ("v", "r") if p[k] is not None]
    if not vals:
        return Markup("")
    w, h, left, right, top, bottom = 600, 150, 38, 46, 10, 22
    pw, ph = w - left - right, h - top - bottom
    lo, hi = (0.0 if zero else min(vals)), max(vals)
    step = _nice_step((hi - lo) or hi or 0.01, 3)
    y0, y1 = math.floor(lo / step + 1e-9) * step, math.ceil(hi / step - 1e-9) * step
    if y1 <= y0:
        y1 = y0 + step
    digits_ = 0 if abs(step * 100 - round(step * 100)) < 1e-9 else 1
    slot = pw / len(points)

    def x(i: int) -> int:
        return round(left + (i + 0.5) * slot)

    def y(v: float) -> int:
        return round(top + ph - ph * (v - y0) / (y1 - y0))

    out = [f'<svg class="chart trend" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">']
    ticks = [y0 + k * step for k in range(int(round((y1 - y0) / step)) + 1)]
    out.append('<path class="grid" d="' + "".join(f"M{left} {y(v)}H{w - right}" for v in ticks) + '"/>')
    out.append('<g class="tick" text-anchor="end">' + "".join(
        f'<text x="{left - 6}" y="{y(v) + 4}">{fmt_pct(v, loc, digits_)}</text>' for v in ticks) + "</g>")
    for i, p in enumerate(points if hits else []):
        out.append(f'<rect class="hit" x="{round(left + i * slot)}" y="{top}" width="{max(1, round(slot))}" '
                   f'height="{ph}"><title>{escape(p["title"])}: {fmt_pct(p["v"], loc)} ({escape(ref_label)} '
                   f'{fmt_pct(p["r"], loc)})</title></rect>')
    ends = []
    for key, line, end in (("r", "trend-ref", "end-ref"), ("v", "trend-line", "end")):
        known = [(i, p[key]) for i, p in enumerate(points) if p[key] is not None]
        path, prev = "", None
        for i, v in known:
            path += f"{'L' if prev == i - 1 else 'M'}{x(i)} {y(v)}"
            prev = i
        out.append(f'<path class="{line}" d="{path}"/>')
        if key == "v":
            out.append('<g class="dot">' + "".join(
                f'<circle cx="{x(i)}" cy="{y(v)}" r="3"{"" if points[i]["kind"] == "parliament" else " class=\"pres\""}/>'
                for i, v in known) + "</g>")
        if known:
            i, v = known[-1]
            ends.append([end, x(i) + 8, y(v) + 4, fmt_pct(v, loc)])
    if len(ends) == 2 and abs(ends[0][2] - ends[1][2]) < 13:
        lower, upper = sorted(ends, key=lambda e: e[2], reverse=True)
        mid = (lower[2] + upper[2]) / 2
        lower[2], upper[2] = round(mid + 6.5), round(mid - 6.5)
    out.extend(f'<text class="{c}" x="{ex}" y="{min(max(ey, 12), top + ph + 4)}">{text}</text>'
               for c, ex, ey, text in ends)
    years, last = [], None
    for i, p in enumerate(points):  # every year since 2000 has an election or two: a label where there's room
        if p["year"] and (last is None or x(i) - x(last) >= 34):
            years.append(f'<text x="{x(i)}" y="{h - 6}">{p["year"]}</text>')
            last = i
    out.append('<g class="tick" text-anchor="middle">' + "".join(years) + "</g>")
    out.append("</svg>")
    return Markup("".join(out))
