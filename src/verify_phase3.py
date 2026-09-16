import os, json

checks = {
    "src/eda_analysis.py":       "EDA pipeline script",
    "src/generate_notebook.py":  "Notebook generator",
    "notebooks/01_eda.ipynb":    "Jupyter notebook",
    "outputs/eda_results.json":  "Results JSON",
    "docs/eda_report.md":        "EDA report",
}
chart_dir = "outputs/charts"
charts = sorted(os.listdir(chart_dir))

print("=== OUTPUT FILE VERIFICATION ===")
all_ok = True
for path, desc in checks.items():
    exists = os.path.exists(path)
    size   = os.path.getsize(path) // 1024 if exists else 0
    status = "OK" if exists else "MISSING"
    if not exists:
        all_ok = False
    print("  [%s] %-35s %s  (%dKB)" % (status, desc, path, size))

print("  Charts in outputs/charts/: %d" % len(charts))
for c in charts:
    print("    " + c)

with open("outputs/eda_results.json") as f:
    r = json.load(f)

print()
print("=== KEY METRICS VERIFICATION ===")
kpis = r["kpis"]
print("  Total orders:           %d" % kpis["total_orders"])
print("  Delivered orders:       %d" % kpis["delivered_orders"])
print("  Total revenue:          R$%.2f" % kpis["total_revenue_brl"])
print("  AOV:                    R$%.2f" % kpis["avg_order_value"])
print("  Avg review score:       %.4f" % kpis["avg_review_score"])
print("  Avg delivery days:      %.2f" % kpis["avg_delivery_days"])
print("  Late delivery rate:     %.2f%%" % kpis["late_delivery_rate"])
print("  Repeat buyer rate:      %.2f%%" % kpis["repeat_buyer_rate_pct"])
print("  On-time rate:           %.2f%%" % kpis["on_time_delivery_rate"])
print("  Insights generated:     %d" % len(r.get("insights", [])))

print()
sat = r.get("satisfaction", {})
print("=== SATISFACTION METRICS ===")
print("  Avg score on-time:      %.4f" % sat.get("avg_score_ontime", 0))
print("  Avg score late:         %.4f" % sat.get("avg_score_late", 0))
print("  Score delta (late):     %.4f" % sat.get("score_delta_late_vs_ontime", 0))

log = r.get("logistics", {})
print()
print("=== LOGISTICS METRICS ===")
print("  Avg delivery days:      %.2f" % log.get("avg_delivery_days", 0))
print("  Median delivery days:   %.2f" % log.get("median_delivery_days", 0))
print("  P90 delivery days:      %.2f" % log.get("p90_delivery_days", 0))
print("  Late rate:              %.2f%%" % log.get("late_rate_pct", 0))

print()
if all_ok:
    print("ALL CHECKS PASSED")
else:
    print("SOME CHECKS FAILED - INVESTIGATE")
