from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .analyzer import CSVAnalyzer

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #0d1117; color: #e6edf3; padding: 2rem; line-height: 1.6; }
h1 { font-size: 1.6rem; font-weight: 600; color: #f0f6fc; margin-bottom: .25rem; }
h2 { font-size: .85rem; font-weight: 600; color: #7d8590; margin: 2rem 0 .75rem;
     text-transform: uppercase; letter-spacing: .06em; }
.sub { color: #7d8590; font-size: .875rem; margin-bottom: 2rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 12px; margin-bottom: 2rem; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; }
.card .val { font-size: 1.4rem; font-weight: 600; color: #c084fc; }
.card .lbl { font-size: .75rem; color: #7d8590; margin-top: 4px; }
table { width: 100%; border-collapse: collapse; margin-bottom: 2rem;
        background: #161b22; border-radius: 8px; overflow: hidden; font-size: .875rem; }
th { text-align: left; padding: .5rem 1rem; color: #7d8590;
     font-size: .75rem; font-weight: 600; border-bottom: 1px solid #30363d; }
td { padding: .5rem 1rem; border-bottom: 1px solid #21262d; }
tr:last-child td { border-bottom: none; }
.pill { display: inline-block; padding: 2px 8px; border-radius: 12px;
        font-size: .75rem; font-weight: 500; }
.num  { background: #1f3a5f; color: #58a6ff; }
.cat  { background: #3b1f5e; color: #c084fc; }
.dt   { background: #12261e; color: #3fb950; }
.bool { background: #2d2008; color: #e3b341; }
.red  { background: #2d1118; color: #f85149; }
.ok   { color: #3fb950; }
.bar-wrap { display: flex; align-items: center; gap: 8px; }
.bar { height: 8px; border-radius: 4px; min-width: 2px; }
"""


def build_html(output: Path, analyzer: CSVAnalyzer) -> None:
    info = analyzer.file_info()
    profiles = analyzer.column_profiles()
    summary = analyzer.summary()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    missing_pct = round(info["missing_cells"] / max(info["total_cells"], 1) * 100, 1)

    # Overview cards
    card_data = [
        (str(info["rows"]), "Rows"),
        (str(info["columns"]), "Columns"),
        (info["file_size"], "File size"),
        (str(info["duplicate_rows"]), "Duplicate rows"),
        (f"{missing_pct}%", "Missing data"),
        (str(summary["numeric_cols"]), "Numeric cols"),
        (str(summary["categorical_cols"]), "Categorical cols"),
    ]
    cards_html = "".join(
        f'<div class="card"><div class="val">{v}</div><div class="lbl">{l}</div></div>'
        for v, l in card_data
    )

    # Column profiles table
    type_cls = {"numeric": "num", "categorical": "cat", "datetime": "dt", "boolean": "bool"}
    col_rows = ""
    for p in profiles:
        cls = type_cls.get(p["type"], "")
        missing_html = (
            f'<span class="pill red">{p["missing_pct"]}%</span>'
            if p["missing"] > 0 else '<span class="ok">✓</span>'
        )
        if p["type"] == "numeric":
            stats = f'mean {p.get("mean","—")} &nbsp; min {p.get("min","—")} &nbsp; max {p.get("max","—")}'
            if p.get("outliers", 0) > 0:
                stats += f' &nbsp; <span class="pill" style="background:#2d2008;color:#e3b341">⚠ {p["outliers"]} outliers</span>'
        elif p["type"] == "categorical":
            top = p.get("top_values", [])
            stats = " &nbsp; ".join(f'{_esc(v["value"])} ({v["count"]})' for v in top[:3])
        else:
            stats = "—"

        col_rows += f"""<tr>
          <td style="font-weight:600">{_esc(p['name'])}</td>
          <td><span class="pill {cls}">{p['type']}</span></td>
          <td>{missing_html}</td>
          <td>{p['unique']}</td>
          <td style="color:#7d8590;font-size:.8rem">{stats}</td>
        </tr>"""

    # Missing values section
    missing_profiles = sorted([p for p in profiles if p["missing"] > 0],
                               key=lambda x: x["missing_pct"], reverse=True)
    max_miss = max((p["missing_pct"] for p in missing_profiles), default=1)
    if missing_profiles:
        miss_rows = ""
        for p in missing_profiles:
            pct = p["missing_pct"]
            bar_w = int(pct / max_miss * 100)
            color = "#f85149" if pct > 20 else "#e3b341"
            miss_rows += f"""<tr>
              <td>{_esc(p['name'])}</td>
              <td>{p['missing']}</td>
              <td><div class="bar-wrap">
                <div class="bar" style="width:{max(bar_w,2)}%;background:{color}"></div>
                <span>{pct}%</span>
              </div></td>
            </tr>"""
        missing_section = f"""
        <h2>⚠ Missing values</h2>
        <table>
          <thead><tr><th>Column</th><th>Count</th><th>Percentage</th></tr></thead>
          <tbody>{miss_rows}</tbody>
        </table>"""
    else:
        missing_section = '<p style="color:#3fb950;margin-bottom:2rem">✓ No missing values found.</p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>csv-detective — {_esc(info['filename'])}</title>
<style>{_CSS}</style>
</head>
<body>
  <h1>🔍 {_esc(info['filename'])}</h1>
  <p class="sub">Generated by <strong>csv-detective</strong> · {now}</p>

  <h2>Overview</h2>
  <div class="grid">{cards_html}</div>

  <h2>Column profiles</h2>
  <table>
    <thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th><th>Stats</th></tr></thead>
    <tbody>{col_rows}</tbody>
  </table>

  {missing_section}

  <p style="margin-top:3rem;color:#7d8590;font-size:.75rem">
    Made with <a href="https://github.com/ekrmsnr/csv-detective" style="color:#c084fc">csv-detective</a>
  </p>
</body>
</html>"""

    output.write_text(html, encoding="utf-8")


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
