#!/usr/bin/env python3
"""Diagnostic comparateur : nœuds internes autour du front d'horloge (pré ou post-layout).
Env : TN_NETLIST, TN_RSHUNT, TN_TAG, TN_DBG_BH (comme dbg_post_comp.py), TN_DBG_POST=1 pour les noms PEX."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import run_phase2 as rp
BH = [tuple(map(int, x.split(":"))) for x in os.environ.get("TN_DBG_BH", "-1:0,1:0").split(",")]
codes = [((0, 0, 0, 0), b, h, (0, 0, 0, 0)) for b, h in BH]
if os.environ.get("TN_DBG_POST"):
    N = dict(TAIL="a_75728_0#", XN="a_75456_0#", XP="a_76000_0#", OUTN="a_77606_0#", OUTP="a_77565_455#",
             SN="a_79316_0.t3", RP="a_78746_0.t3")
    nodes = {k: f"v(xdut.{v})" for k, v in N.items()}
else:
    nodes = {k: f"v(xdut.xcmp.{k.lower()})" for k in ("TAIL", "XN", "XP", "OUTN", "OUTP", "SN", "RP")}
save = ("v(vp)", "v(vm)", "v(clk)", "v(q)", "i(vvdd)") + tuple(nodes.values()) + ("v(qb)",)
t, cols, qs = rp.run_slots(codes, f"{rp.TAG}_nodes", save=save)
names = ["VP", "VM", "CLK", "Q", "IDD"] + list(nodes) + ["QB"]
for k, c in enumerate(codes):
    print(f"--- slot {k} b={c[1]:+d} h={c[2]}  Q={qs[k]}")
    print("  t(ns) " + " ".join(f"{n:>7s}" for n in names if n != "IDD"))
    for tt in (84.0, 85.2, 85.5, 85.8, 86.1, 86.5, 87.0, 88.0, 92.0):
        j = np.searchsorted(t, k * tn_T + tt * 1e-9) if (tn_T := rp.tn.T_EVAL) else 0
        print(f"  {tt:5.1f} " + " ".join(f"{cols[i][j]:7.3f}" for i, n in enumerate(names) if n != "IDD"))
