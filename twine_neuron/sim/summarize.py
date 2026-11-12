#!/usr/bin/env python3
"""Fusionne results/<TAG>_metrics_*.csv -> results/prelayout_tt.csv (ou <out> donné).
    python3 sim/summarize.py [TAG] [fichier_sortie]"""
import csv
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = sys.argv[1] if len(sys.argv) > 1 else "pre"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results", "prelayout_tt.csv")
rows, seen = [], {}
for p in sorted(glob.glob(os.path.join(ROOT, "results", f"{TAG}_metrics_*.csv")), key=os.path.getmtime):
    for r in csv.DictReader(open(p)):
        seen[r["test"].split(" (")[0].split(" {")[0] if "pire code" not in r["test"] else "P pire code"] = r
rows = list(seen.values())
for r in rows:      # SPEC v2 (itération 2) : S12 puissance informative
    if "option 1" in r["spec"]:
        r["spec"], r["status"] = "info (S12 v2 ; v1 : " + r["spec"] + ")", "OK"
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["test", "value", "unit", "spec", "status", "source"])
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print(f"[{r['status']:3s}] {r['test']:60s} {r['value']:>14s} {r['unit']:5s} spec {r['spec']}")
print(f"-> {os.path.relpath(OUT, ROOT)} ({len(rows)} métriques)")
