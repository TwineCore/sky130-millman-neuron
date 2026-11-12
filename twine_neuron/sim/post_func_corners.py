#!/usr/bin/env python3
"""Fonctionnel post-layout aux coins de postpoints(), une porte par run (mémoire VM), séquentiel.
Fusionne les 3 portes en results/corners/<tag>_metrics_func.csv (lu par run_phase3.aggregate) :
erreurs sommées, kickback/inversions au pire, puissance moyennée. Env : TN_NETLIST, TN_RSHUNT, TN_CTAG=p."""
import csv, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_phase3 as p3
GATES = ["AND", "OR", "NAND"]
t0 = time.time()
for p in p3.postpoints():
    m, r, v, t = p
    tg = p3.tag(p)
    out = os.path.join(p3.CDIR, f"{tg}_metrics_func.csv")
    if os.path.exists(out):
        print(f"  {tg} skip", flush=True)
        continue
    per = []
    for g in GATES:
        env = dict(os.environ, TN_CORNER=p3.lib_name(m, r), TN_VDD=str(v), TN_TEMP=str(t), TN_TAG=f"{tg}_{g}",
                   TN_RESDIR=p3.CDIR, TN_FUNC_GATES=g)
        r_ = subprocess.run([sys.executable, "-u", os.path.join(p3.ROOT, "sim", "run_phase2.py"), "func"],
                            capture_output=True, text=True, env=env, cwd=p3.ROOT)
        open(os.path.join(p3.CDIR, f"{tg}_{g}_func.txt"), "w").write(r_.stdout + r_.stderr)
        f = os.path.join(p3.CDIR, f"{tg}_{g}_metrics_func.csv")
        ok = r_.returncode == 0 and os.path.exists(f)
        print(f"  {tg} {g:4s} {'ok' if ok else 'ERREUR'}  (t = {time.time()-t0:.0f} s)", flush=True)
        if ok:
            per.append(list(csv.DictReader(open(f))))
    if len(per) != len(GATES):
        continue
    rows = []
    for k, row in enumerate(per[0]):
        vals = [float(x[k]["value"]) for x in per]
        name = row["test"]
        if name.startswith("ET/OU/NON-ET"):
            val = sum(vals)
        elif name.startswith("puissance moyenne"):
            val = sum(vals) / len(vals)
        else:
            val = max(vals)
        st = "OK" if all(x[k]["status"] == "OK" for x in per) else "NON"
        unit = f"/{4 * len(GATES)}" if name.startswith("ET/OU/NON-ET") else row["unit"]
        rows.append(dict(row, value=f"{val:.6g}", unit=unit, status=st))
    with open(out, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"  {tg} fusion -> {os.path.basename(out)}", flush=True)
