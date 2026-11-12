#!/usr/bin/env python3
"""Diagnostic post-layout : décisions du comparateur pour |ΔV| grand (b = −31, +31, −3, +3, −31).
Env : TN_NETLIST (PEX), TN_RSHUNT, TN_TAG. Sortie : sim/out/<TAG>_dbg.dat + affichage ΔV à 84 ns et Q à 92 ns."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_phase2 as rp
BH = [tuple(map(int, x.split(":"))) for x in os.environ.get("TN_DBG_BH", "-31:0,31:0,-3:0,3:0,-31:0").split(",")]
codes = [((0, 0, 0, 0), b, h, (0, 0, 0, 0)) for b, h in BH]
t, (vp, vm, clk, q, idd), qs = rp.run_slots(codes, f"{rp.TAG}_dbg")
import numpy as np
for k, c in enumerate(codes):
    j = np.searchsorted(t, k * 100e-9 + 84e-9)
    print(f"b={c[1]:+d} h={c[2]}  ΔV(84 ns) = {1e3*(vp[j]-vm[j]):+8.2f} mV  Vcm = {(vp[j]+vm[j])/2:.3f} V  Q = {int(qs[k])}")
