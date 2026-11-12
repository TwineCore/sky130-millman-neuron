#!/usr/bin/env python3
"""Tracés de la phase 2 (Mac) : python3 plots/plot_phase2.py [TAG]   (TAG = pre par défaut)
Lit results/<TAG>_*.csv et sim/out/<TAG>_*.dat rapatriés depuis la VM ; écrit plots/<TAG>_*.png."""
import csv
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = sys.argv[1] if len(sys.argv) > 1 else "pre"
R, O, P = (os.path.join(ROOT, d) for d in ("results", "sim/out", "plots"))
BL, RD, GN, GR, OR = "#2a6fdb", "#d1495b", "#2e9e6a", "#888888", "#e08a1e"
T_EVAL, T_SAMPLE = 100e-9, 92e-9


def rd(name):
    p = os.path.join(R, f"{TAG}_{name}.csv")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in r.items():
            try:
                r[k] = float(v)
            except (ValueError, TypeError):
                pass
    return rows


def dat(name):
    p = os.path.join(O, f"{TAG}_{name}.dat")
    if not os.path.exists(p):
        return None
    d = np.loadtxt(p)
    return d[:, 0], [d[:, j] for j in range(1, d.shape[1], 2)]


made = []
# ---------------------------------------------------------------- DC
dc = rd("dc")
if dc:
    fig, ax = plt.subplots(2, 2, figsize=(12, 8), dpi=140)
    a = ax[0, 0]
    for st, c in (("syn", BL), ("bias", GN), ("rand", OR)):
        e = [r["err_LSB"] for r in dc if r["set"] == st]
        a.plot(range(len(e)), e, ".", ms=3, color=c, label={"syn": "synapses (w, x)", "bias": "biais (b, h)",
                                                              "rand": "300 codes aléatoires"}[st])
    a.set_ylabel("ΔV_sim − ΔV_modèle (LSB)")
    a.set_xlabel("index du code")
    a.set_title("(a) Écart au modèle de Millman idéal")
    a.legend(fontsize=8)
    a.grid(alpha=0.3)
    a = ax[0, 1]
    for i, c in zip(range(1, 5), (BL, RD, GN, OR)):
        rr = [r for r in dc if r["set"] == "syn" and r["i"] == i and r[f"x{i}"] == 1]
        w = np.array([r[f"w{i}"] for r in rr])
        a.plot(w, np.array([r["weff"] for r in rr]) - w, "o-", ms=3, color=c, label=f"synapse {i}")
    a.set_xlabel("poids programmé w")
    a.set_ylabel("INL = w_eff − w (LSB)")
    a.set_title("(b) INL des poids (x_i = 1, w_eff = ΔV / LSB(D))")
    a.legend(fontsize=8)
    a.grid(alpha=0.3)
    a = ax[1, 0]
    for h, c in ((0, GN), (1, BL)):
        rr = [r for r in dc if r["set"] == "bias" and r["h"] == h]
        b = np.array([r["b"] for r in rr])
        a.plot(b, np.array([r["weff"] for r in rr]) + 0.5 * h - b, "o-", ms=2.5, color=c, label=f"h = {h}")
    a.set_xlabel("code de biais b")
    a.set_ylabel("INL biais (LSB)")
    a.set_title("(c) INL du biais 5 bits + signe")
    a.legend(fontsize=8)
    a.grid(alpha=0.3)
    a = ax[1, 1]
    rr = [r for r in dc if r["set"] == "rand"]
    a.scatter([r["S"] for r in rr], [r["P_W"] * 1e6 for r in rr], s=8, color=BL, label="300 codes aléatoires")
    a.axhline(50, color=RD, ls="--", lw=0.8)
    a.text(1, 51, "50 µW (moyenne, option 1)", color=RD, fontsize=7)
    a.set_xlabel("S = Σ|w| + |b| + 0.5h")
    a.set_ylabel("P statique (µW)")
    a.set_title(f"(d) Puissance statique, moyenne = {np.mean([r['P_W'] for r in rr])*1e6:.1f} µW")
    a.grid(alpha=0.3)
    fig.suptitle(f"DC pré-layout ({TAG}) — tt, 27 °C, VDD = 1.8 V")
    fig.tight_layout()
    fig.savefig(os.path.join(P, f"{TAG}_dc.png"))
    made.append(f"{TAG}_dc.png")

# ---------------------------------------------------------------- comparateur
co, td = rd("comp_offset"), rd("comp_tdec")
if co or td:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5), dpi=140)
    if co:
        a = ax[0]
        v = [r["vcm"] for r in co]
        a.plot(v, [r["offset_mV"] for r in co], "o-", color=BL, label="offset systématique")
        a.plot(v, [r["hyst_mV"] for r in co], "s-", color=RD, label="hystérésis")
        a.axvspan(0.75, 1.8, color=GN, alpha=0.08, label="plage de V± (modèle)")
        a.axhline(2.42, color=GR, ls="--", lw=0.8)
        a.axhline(-2.42, color=GR, ls="--", lw=0.8)
        a.text(0.52, 2.5, "± LSB_min/6", fontsize=7, color=GR)
        a.set_xlabel("mode commun d'entrée (V)")
        a.set_ylabel("mV")
        a.set_title("(a) Offset et hystérésis vs mode commun (rampe ±10 mV)")
        a.legend(fontsize=8)
        a.grid(alpha=0.3)
    if td:
        a = ax[1]
        for vcm, c in ((0.84, BL), (1.3, RD)):
            rr = [r for r in td if abs(r["vcm"] - vcm) < 1e-6]
            a.semilogx([r["dV_V"] * 1e3 for r in rr], [r["t_dec_s"] * 1e9 for r in rr], "o-", color=c,
                       label=f"Vcm = {vcm} V")
        a.axvline(7.26, color=GR, ls="--", lw=0.8)
        a.text(7.6, a.get_ylim()[1] * 0.9, "0.5 LSB_min", fontsize=7, color=GR)
        a.set_xlabel("ΔV d'entrée (mV)")
        a.set_ylabel("t_décision (ns), front clk → Q")
        a.set_title("(b) Temps de décision vs ΔV")
        a.legend(fontsize=8)
        a.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(P, f"{TAG}_comp.png"))
    made.append(f"{TAG}_comp.png")

# ---------------------------------------------------------------- stabilisation
st = rd("settle")
if st:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5), dpi=140)
    a = ax[0]
    k = int(np.argmax([max(r["t_settle_rise_ns"], r["t_settle_fall_ns"]) for r in st]))
    d = dat(f"settle_{k}")
    if d:
        t, (vp, vm) = d
        a.plot(t * 1e9, vp, color=BL, label="V+")
        a.plot(t * 1e9, vm, color=RD, label="V−")
        a.axvline(20, color=GR, lw=0.6)
        a.axvline(270, color=GR, lw=0.6)
        a.axvline(20 + st[k]["t_settle_rise_ns"], color=GN, ls="--", lw=1)
        a.axvline(270 + st[k]["t_settle_fall_ns"], color=GN, ls="--", lw=1)
        a.set_title(f"(a) Pire cas : {st[k]['config']} — t_settle = {st[k]['t_settle_rise_ns']:.1f} / "
                    f"{st[k]['t_settle_fall_ns']:.1f} ns")
        a.set_xlabel("t (ns)")
        a.set_ylabel("V")
        a.legend(fontsize=8)
        a.grid(alpha=0.3)
    a = ax[1]
    names = [r["config"] for r in st]
    x = np.arange(len(st))
    a.bar(x - 0.2, [r["t_settle_rise_ns"] for r in st], 0.4, color=BL, label="montée")
    a.bar(x + 0.2, [r["t_settle_fall_ns"] for r in st], 0.4, color=OR, label="descente")
    a.axhline(50, color=RD, ls="--", lw=0.8)
    a.set_xticks(x)
    a.set_xticklabels(names, rotation=30, ha="right", fontsize=7)
    a.set_ylabel("t_settle à 0.5 LSB (ns)")
    a.set_title("(b) Stabilisation vs charge S (spec 50 ns)")
    a.legend(fontsize=8)
    a.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(P, f"{TAG}_settle.png"))
    made.append(f"{TAG}_settle.png")

# ---------------------------------------------------------------- fonctionnel + XOR
for name, csvname, title in (("func", "func", "ET / OU / NON-ET"), ("xor", "xor", "XOR 2-2-1 multiplexé")):
    d = dat(name)
    rows = rd(csvname)
    if not d or not rows:
        continue
    t, (vp, vm, clk, q, idd) = d
    fig, ax = plt.subplots(3, 1, figsize=(13, 7), dpi=140, sharex=True, gridspec_kw=dict(height_ratios=[2, 1, 1]))
    ax[0].plot(t * 1e9, vp, color=BL, lw=1, label="V+")
    ax[0].plot(t * 1e9, vm, color=RD, lw=1, label="V−")
    ax[0].set_ylabel("V")
    ax[0].legend(fontsize=8, loc="upper right")
    ax[1].plot(t * 1e9, (vp - vm) * 1e3, color=GN, lw=1)
    ax[1].axhline(0, color=GR, lw=0.6)
    ax[1].set_ylabel("ΔV (mV)")
    ax[2].plot(t * 1e9, clk, color=GR, lw=0.8, label="clk")
    ax[2].plot(t * 1e9, q, color="k", lw=1.4, label="Q")
    ax[2].set_ylabel("V")
    ax[2].set_xlabel("t (ns)")
    ax[2].legend(fontsize=8, loc="upper right")
    n = int(round(t[-1] / T_EVAL))
    if name == "func":
        labels = [r["eval"] for r in rows]
    else:
        labels = ([f"OR {int(r['x1'])}{int(r['x2'])}" for r in rows] + [f"NAND {int(r['x1'])}{int(r['x2'])}" for r in rows]
                  + [f"AND {int(r['h1'])}{int(r['h2'])}→y" for r in rows])
    for k in range(n):
        for a in ax:
            a.axvline(k * 100, color=GR, lw=0.3)
        ax[0].text(k * 100 + 3, ax[0].get_ylim()[1] * 0.98, labels[k] if k < len(labels) else "", fontsize=6.5,
                   va="top")
    for a in ax:
        a.grid(alpha=0.25)
    ok = sum(int(r["ok"]) for r in rows)
    fig.suptitle(f"{title} — {ok}/{len(rows)} corrects ({TAG}, tt 27 °C, 10 MHz)")
    fig.tight_layout()
    fig.savefig(os.path.join(P, f"{TAG}_{name}.png"))
    made.append(f"{TAG}_{name}.png")

# ---------------------------------------------------------------- SAR
sar = rd("sar")
if sar:
    fig, a = plt.subplots(figsize=(6, 5), dpi=140)
    a.plot([-30, 30], [-30, 30], color=GR, lw=0.8)
    a.scatter([r["s_true"] for r in sar], [r["s_read"] for r in sar], color=BL, zorder=3)
    for r in sar:
        a.annotate(f"{int(r['s_read'])}", (r["s_true"], r["s_read"]), xytext=(4, -10), textcoords="offset points",
                   fontsize=7)
    a.set_xlabel("Σ w·x attendu")
    a.set_ylabel("Σ w·x lu par SAR (6 décisions)")
    a.set_title(f"Lecture SAR : {sum(r['err'] == 0 for r in sar)}/{len(sar)} exactes ({TAG})")
    a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(P, f"{TAG}_sar.png"))
    made.append(f"{TAG}_sar.png")
print("tracés :", made)
