#!/usr/bin/env python3
"""
Generate a lightweight SVG benchmark chart from a pyperf JSON result.

Designed to be dependency-free (no matplotlib) so it can run in CI and local dev
environments without extra installs.

Example:
  python tools/plot_pyperf_svg.py bench/results/json.json -o bench/plots/json_speedup.svg
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def _load_pyperf(path: Path) -> Dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: Dict[str, float] = {}
    for bench in data.get("benchmarks", []):
        name = (bench.get("metadata") or {}).get("name")
        if not name:
            continue
        values: List[float] = []
        for run in bench.get("runs", []):
            values.extend(run.get("values", []))
        if not values:
            continue
        out[name] = sum(values) / len(values)
    return out


def _fmt_seconds(s: float) -> str:
    if s < 1e-6:
        return f"{s * 1e9:.3g} ns"
    if s < 1e-3:
        return f"{s * 1e6:.3g} µs"
    if s < 1:
        return f"{s * 1e3:.3g} ms"
    return f"{s:.3g} s"


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _svg_speedup_chart(
    rows: List[Tuple[str, float, float]],
    *,
    title: str,
    subtitle: str,
) -> str:
    # Layout constants.
    width = 920
    left = 220
    right = 30
    # Leave enough padding so the subtitle never overlaps axis labels.
    top = 92
    row_h = 54
    bar_h = 14
    gap = 8

    max_speedup = max((j / f for _, j, f in rows), default=1.0)
    max_speedup = max(1.0, max_speedup) * 1.1
    chart_w = width - left - right
    height = top + len(rows) * row_h + 40

    def x(speedup: float) -> float:
        return left + (speedup / max_speedup) * chart_w

    lines: List[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    lines.append("<style>")
    lines.append("  .title { font: 600 20px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; fill: #111827; }")
    lines.append("  .subtitle { font: 400 13px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; fill: #6b7280; }")
    lines.append("  .label { font: 600 13px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; fill: #111827; }")
    lines.append("  .meta { font: 400 12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; fill: #374151; }")
    lines.append("  .axis { stroke: #e5e7eb; stroke-width: 1; }")
    lines.append("  .bar { fill: #2563eb; }")
    lines.append("  .barbg { fill: #eef2ff; }")
    lines.append("  .value { font: 700 12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; fill: #111827; }")
    lines.append("</style>")

    # Background.
    lines.append('<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>')

    # Title block.
    lines.append(f'<text x="{left}" y="30" class="title">{_escape(title)}</text>')
    lines.append(f'<text x="{left}" y="52" class="subtitle">{_escape(subtitle)}</text>')

    # Axis ticks.
    for t in (1, 5, 10, 20, 30):
        if t > max_speedup:
            continue
        xx = x(t)
        lines.append(f'<line x1="{xx:.1f}" y1="{top - 10}" x2="{xx:.1f}" y2="{height - 20}" class="axis"/>')
        lines.append(f'<text x="{xx + 4:.1f}" y="{top - 14}" class="subtitle">{t}×</text>')

    # Rows.
    for i, (name, json_s, fast_s) in enumerate(rows):
        y0 = top + i * row_h
        speedup = json_s / fast_s if fast_s > 0 else 0.0
        bar_x0 = left
        bar_x1 = x(speedup)
        bar_w = max(0.0, bar_x1 - bar_x0)

        lines.append(f'<text x="30" y="{y0 + 18}" class="label">{_escape(name)}</text>')
        # Bar background at 0..max_speedup.
        lines.append(f'<rect x="{left}" y="{y0 + 6}" width="{chart_w}" height="{bar_h}" rx="7" class="barbg"/>')
        lines.append(f'<rect x="{left}" y="{y0 + 6}" width="{bar_w:.1f}" height="{bar_h}" rx="7" class="bar"/>')

        lines.append(
            f'<text x="{left}" y="{y0 + 40}" class="meta">'
            f'stdlib json={_escape(_fmt_seconds(json_s))}  zmij-fastjson={_escape(_fmt_seconds(fast_s))}'
            f"</text>"
        )
        lines.append(f'<text x="{min(left + bar_w + 8, width - right - 60):.1f}" y="{y0 + 17}" class="value">{speedup:.1f}×</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="pyperf JSON result file")
    ap.add_argument("-o", "--out", type=Path, required=True, help="output SVG path")
    ap.add_argument("--title", default="zmij-fastjson vs stdlib json", help="chart title")
    ap.add_argument(
        "--subtitle",
        default="Workload: numeric array serialization (compact separators)",
        help="chart subtitle",
    )
    ap.add_argument(
        "--datasets",
        default="1e4,1e5,mixed_1e5_nulls",
        help="comma-separated dataset suffixes (expects json.dumps/<name> and fastjson.dumps/<name>)",
    )
    args = ap.parse_args()

    results = _load_pyperf(args.input)
    datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]
    rows: List[Tuple[str, float, float]] = []
    for d in datasets:
        j = results.get(f"json.dumps/{d}")
        f = results.get(f"fastjson.dumps/{d}")
        if j is None or f is None:
            continue
        rows.append((d, j, f))

    if not rows:
        raise SystemExit("No datasets found in input (check --datasets and benchmark names).")

    svg = _svg_speedup_chart(rows, title=args.title, subtitle=args.subtitle)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
