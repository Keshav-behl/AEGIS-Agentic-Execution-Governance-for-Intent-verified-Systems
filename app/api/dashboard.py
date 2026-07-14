def render_dashboard(stats: dict) -> str:
    total = stats["total_actions"]
    success = stats["auto_executed"] + stats["human_approved_executed"]
    success_rate = f"{(success / total * 100):.0f}%" if total else "—"
    avg_decision = (
        f"{stats['avg_decision_seconds'] / 60:.1f} min" if stats["avg_decision_seconds"] is not None else "—"
    )
    category_rows = "".join(
        f"<tr><td>{category}</td><td>{count}</td></tr>"
        for category, count in sorted(stats["category_breakdown"].items(), key=lambda kv: -kv[1])
    ) or "<tr><td colspan='2'>No human-reviewed requests yet</td></tr>"

    tiles = [
        (total, "Total Actions"),
        (stats["auto_executed"], "Auto-Executed"),
        (stats["human_approved_executed"], "Human-Approved"),
        (success_rate, "Success Rate"),
        (stats["human_reviewed_total"], "Sent to Human Review"),
        (stats["human_reviewed_still_pending"], "Still Pending"),
        (stats["human_reviewed_escalated"], "Escalated (SLA)"),
        (stats["denied"], "Denied"),
        (stats["rejected"], "Rejected (bad token)"),
        (stats["failed"], "Failed"),
        (avg_decision, "Avg Time to Decision"),
    ]
    tile_html = "".join(
        f'<div class="tile"><div class="value">{value}</div><div class="label">{label}</div></div>'
        for value, label in tiles
    )

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>AEGIS Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0d1117; color: #e6edf3; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  .subtitle {{ color: #8b949e; margin-bottom: 1.5rem; }}
  .tiles {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
  .tile {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem 1.5rem; min-width: 140px; }}
  .tile .value {{ font-size: 1.8rem; font-weight: 700; }}
  .tile .label {{ font-size: 0.8rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }}
  h2 {{ margin-top: 2rem; font-size: 1.1rem; }}
  table {{ border-collapse: collapse; margin-top: 0.75rem; }}
  td, th {{ padding: 0.4rem 1.25rem 0.4rem 0; border-bottom: 1px solid #30363d; text-align: left; }}
</style>
</head>
<body>
  <h1>AEGIS — Governance Dashboard</h1>
  <div class="subtitle">Every proposed action, how it was routed, and how it was resolved.</div>
  <div class="tiles">{tile_html}</div>
  <h2>Human-review triggers by category</h2>
  <table>
    <tr><th>Category</th><th>Count</th></tr>
    {category_rows}
  </table>
</body>
</html>"""
