#!/usr/bin/env python3
"""results/post_vs_pre.csv : métriques pré (results/corners_pre.csv, prelayout_tt) vs post (corners_post.csv)."""
import csv, os
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
pre = {(r["lib"], r["vdd"], r["temp"]): r for r in csv.DictReader(open(os.path.join(R, "corners_pre.csv")))}
post = list(csv.DictReader(open(os.path.join(R, "corners_post.csv"))))
keys = ["dc_sign_err", "dv_half_min_mV", "dc_err_max_LSB", "vcm_min_V", "t_settle_ns", "P_worst_uW"]
rows = []
for p in post:
    k = (p["lib"], p["vdd"], p["temp"])
    q = pre.get(k, {})
    for m in keys:
        a, b = q.get(m, ""), p.get(m, "")
        try:
            d = f"{100 * (float(b) - float(a)) / abs(float(a)):+.1f} %" if float(a) != 0 else ""
        except ValueError:
            d = ""
        rows.append(dict(lib=p["lib"], vdd=p["vdd"], temp=p["temp"], metric=m, pre=a, post=b, delta=d))
with open(os.path.join(R, "post_vs_pre.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows:
    print(f"{r['lib']:6s} {r['vdd']:5s} {r['temp']:5s} {r['metric']:16s} pre {r['pre']:>10s}  post {r['post']:>10s}  {r['delta']}")
