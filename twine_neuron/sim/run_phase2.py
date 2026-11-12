#!/usr/bin/env python3
"""Phase 2 — simulations pré-layout (tt, 27 °C). S'exécute dans le conteneur :

    cd /foss/designs/twine_neuron && python3 sim/run_phase2.py <test> [...]
    tests : ron dc comp tdec settle func xor sar power   (ou « all »)

Chaque test écrit results/pre_<test>.csv (+ données brutes sim/out/) et une ligne de métriques
dans results/prelayout_tt_metrics.csv (fusionnées dans results/prelayout_tt.csv par summarize).
"""
import csv
import itertools
import json
import os
import sys
import time
import numpy as np
import tn

R = os.environ.get("TN_RESDIR", os.path.join(tn.ROOT, "results"))
os.makedirs(R, exist_ok=True)
CORNER = os.environ.get("TN_CORNER", "tt")
TEMP = float(os.environ.get("TN_TEMP", "27"))
VDDS = float(os.environ.get("TN_VDD", "1.8"))
NET = os.environ.get("TN_NETLIST", tn.NETLIST)
TAG = os.environ.get("TN_TAG", "pre")
MODEL = json.load(open(os.path.join(tn.ROOT, "calc", "out", "model_summary.json")))
RU = MODEL["RU_ohm"]
rng = np.random.default_rng(7)
# pas max des transitoires horlogés : décision StrongARM ≈ 0.5 ns ; 0.2 ns donne des décisions erratiques
# à quelques mV (vérifié : sim/out/dbg_comp_fine_0.80.spice), 20 ps donne seuil ±0.12 mV
TMAX = os.environ.get("TN_TMAX", "0.02n")
METRICS = []


def metric(name, value, unit, spec, ok, src):
    METRICS.append(dict(test=name, value=value, unit=unit, spec=spec, status="OK" if ok else "NON", source=src))
    print(f"  [{ 'OK ' if ok else 'NON'}] {name} = {value} {unit}   (spec {spec})")


def save_csv(path, rows):
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)


def hdr(title):
    return tn.header(title, CORNER, TEMP, VDDS, NET)


# ======================================================================== Ron des drivers
def t_ron():
    print("== Ron des drivers (slices isolées, sortie forcée à VDD/2)")
    sl = {"w1": 1, "w2": 2, "w4": 4, "w8": 8, "w16": 16, "half": 0.5}
    s = hdr("Ron drivers") + "VD d 0 DC 1.8\nVEN en 0 DC 1.8\n"
    for n in sl:
        s += f"XSL{n} d en o{n} vdd 0 slice_{n}\nVM{n} o{n} 0 DC {VDDS/2}\n"
    ctl = ".control\n"
    for dval, en in ((VDDS, VDDS), (0.0, VDDS), (VDDS, 0.0), (0.0, 0.0)):
        ctl += f"alter @vd[dc] = {dval}\nalter @ven[dc] = {en}\nop\n"
        for n in sl:
            ctl += (f"let i{n} = i(vm{n})\nlet vd{n} = v(xsl{n}.drv)\n"
                    f"echo \"RES d={dval} en={en} w={sl[n]} i=$&i{n} vdrv=$&vd{n}\"\n")
    s += ctl + ".endc\n.end\n"
    rows = tn.parse_res(tn.run(s, f"{TAG}_ron"))
    out, worst = [], 0
    for r in rows:
        w = r["w"]
        rslice = RU / w
        if r["en"] > 0:
            i = abs(r["i"])
            ron = (VDDS - r["vdrv"]) / i if r["d"] > 0 else r["vdrv"] / i
            out.append(dict(weight=w, drive="1 (PMOS)" if r["d"] > 0 else "0 (NMOS)", I_A=i, Ron_ohm=ron,
                            R_slice_ohm=rslice, Ron_over_R_pct=100 * ron / rslice))
            worst = max(worst, 100 * ron / rslice)
        else:
            out.append(dict(weight=w, drive=f"Hi-Z (D={r['d']:.1f})", I_A=abs(r["i"]), Ron_ohm=float("nan"),
                            R_slice_ohm=rslice, Ron_over_R_pct=float("nan")))
    save_csv(os.path.join(R, f"{TAG}_ron.csv"), out)
    leak = max(o["I_A"] for o in out if "Hi-Z" in o["drive"])
    metric("Ron/R_slice max", round(worst, 3), "%", "< 1 %", worst < 1, f"results/{TAG}_ron.csv")
    metric("fuite Hi-Z max", f"{leak:.3g}", "A", "<< I_LSB", leak < 1e-9, f"results/{TAG}_ron.csv")


# ======================================================================== DC : poids, biais, codes aléatoires
def dc_configs():
    cf = []
    for i in range(4):
        for w in range(-7, 8):
            for xv in (0, 1):
                ww = [0, 0, 0, 0]; ww[i] = w
                xx = [0, 0, 0, 0]; xx[i] = xv
                cf.append(("syn", i + 1, tuple(ww), 0, 0, tuple(xx)))
    for b in range(-31, 32):
        for h in (0, 1):
            cf.append(("bias", 0, (0, 0, 0, 0), b, h, (0, 0, 0, 0)))
    for _ in range(300):
        cf.append(("rand", 0, tuple(int(v) for v in rng.integers(-7, 8, 4)), int(rng.integers(-31, 32)),
                   int(rng.integers(0, 2)), tuple(int(v) for v in rng.integers(0, 2, 4))))
    return cf


def t_dc():
    print("== DC : V+, V−, ΔV pour tous les codes de poids/biais + 300 codes aléatoires")
    cf = dc_configs()
    s = hdr("DC poids") + tn.dut_line(NET) + tn.dc_sources(tn.levels((0, 0, 0, 0), 0, 0, (0, 0, 0, 0), VDDS))
    s += ".control\n"
    for k, (_, _, w, b, h, x) in enumerate(cf):
        s += tn.alters(tn.levels(w, b, h, x, VDDS))
        s += (f"op\nlet a=v(vp)\nlet c=v(vm)\nlet p=-i(vvdd)\n"
              f"echo \"RES k={k} vp=$&a vm=$&c idd=$&p\"\n")
    s += ".endc\n.end\n"
    t = time.time()
    res = tn.parse_res(tn.run(s, f"{TAG}_dc"))
    print(f"  {len(res)} points en {time.time()-t:.0f} s")
    rows = []
    for (st, i, w, b, h, x), r in zip(cf, res):
        m = tn.ideal(w, b, h, x, VDDS)
        dv = r["vp"] - r["vm"]
        rows.append(dict(set=st, i=i, w1=w[0], w2=w[1], w3=w[2], w4=w[3], b=b, h=h, x1=x[0], x2=x[1], x3=x[2],
                         x4=x[3], S=m["S"], D=m["D"], s_plus_b=m["s"], vp_sim=r["vp"], vm_sim=r["vm"], dv_sim=dv,
                         vp_mod=m["vp"], vm_mod=m["vn"], dv_mod=m["dv"], lsb_mod=m["lsb"],
                         err_LSB=(dv - m["dv"]) / m["lsb"], weff=dv / m["lsb"], P_W=r["idd"] * VDDS,
                         sign_ok=int(np.sign(dv) == np.sign(m["dv"]))))
    save_csv(os.path.join(R, f"{TAG}_dc.csv"), rows)
    err = np.array([r["err_LSB"] for r in rows])
    cm = np.array([min(r["vp_sim"], r["vm_sim"]) for r in rows])
    # INL / DNL du poids (synapse i, x_i = 1) : w_eff = ΔV/LSB(D)
    inl, dnl = [], []
    for i in range(1, 5):
        we = [r["weff"] for r in rows if r["set"] == "syn" and r["i"] == i and r[f"x{i}"] == 1]
        ws = [r[f"w{i}"] for r in rows if r["set"] == "syn" and r["i"] == i and r[f"x{i}"] == 1]
        we = np.array(we) + 0.0
        inl += list(we - np.array(ws))
        dnl += list(np.diff(we) - 1)
    bi = [(r["weff"] + 0.5 * r["h"]) - r["b"] for r in rows if r["set"] == "bias"]
    bd = np.diff([r["weff"] for r in rows if r["set"] == "bias" and r["h"] == 0]) - 1
    metric("erreur ΔV vs modèle (max |.|, tous codes)", round(float(np.abs(err).max()), 4), "LSB", "< 0.5 LSB",
           np.abs(err).max() < 0.5, f"results/{TAG}_dc.csv")
    metric("INL poids synapse (max |.|)", round(float(np.abs(inl).max()), 4), "LSB", "< 0.5 LSB",
           np.abs(inl).max() < 0.5, f"results/{TAG}_dc.csv")
    metric("DNL poids synapse (max |.|)", round(float(np.abs(dnl).max()), 4), "LSB", "< 0.5 LSB",
           np.abs(dnl).max() < 0.5, f"results/{TAG}_dc.csv")
    metric("INL biais (max |.|)", round(float(np.abs(bi).max()), 4), "LSB", "< 0.5 LSB", np.abs(bi).max() < 0.5,
           f"results/{TAG}_dc.csv")
    metric("DNL biais (max |.|)", round(float(np.abs(bd).max()), 4), "LSB", "< 0.5 LSB", np.abs(bd).max() < 0.5,
           f"results/{TAG}_dc.csv")
    metric("erreurs de signe (codes non nuls)", int(sum(1 - r["sign_ok"] for r in rows if r["dv_mod"] != 0)), "",
           "0", all(r["sign_ok"] for r in rows if r["dv_mod"] != 0), f"results/{TAG}_dc.csv")
    metric("mode commun min V± (codes testés)", round(float(cm.min()), 4), "V", ">= 0.75 V", cm.min() >= 0.75,
           f"results/{TAG}_dc.csv")
    pr = [r["P_W"] for r in rows if r["set"] == "rand"]
    metric("P statique moyenne (300 codes aléatoires)", round(float(np.mean(pr)) * 1e6, 2), "µW",
           "info (S12 v2)", True, f"results/{TAG}_dc.csv")


# ======================================================================== DC codes critiques (corners, MC)
def crit_codes():
    """Codes à |Σw·x + b − 0.5h| = 0.5 (décision la plus serrée) + portes + code de mode commun minimal."""
    cf = []
    for w, x in SAR_VEC:
        s = int(np.dot(w, x))
        for b in (-s, -s + 1):                      # Σ+b−0.5h = −0.5 / +0.5 LSB (h = 1)
            if -31 <= b <= 31:
                cf.append(("half", w, b, 1, x))
    for g in GATES:
        for x1, x2 in itertools.product((0, 1), repeat=2):
            w, b, h, x = gate_code(g, x1, x2)
            cf.append(("gate", w, b, h, x))
    cf.append(("cm", (7, 7, 7, 7), -31, 1, (0, 0, 0, 0)))      # S max, V+ et V− au plus bas
    cf.append(("cm", (-7, -7, -7, -7), 31, 1, (0, 0, 0, 0)))
    return cf


def t_dccrit():
    print("== DC codes critiques (±0.5 LSB, portes, mode commun min)")
    cf = crit_codes()
    s = hdr("DC critiques") + tn.dut_line(NET) + tn.dc_sources(tn.levels((0, 0, 0, 0), 0, 0, (0, 0, 0, 0), VDDS))
    s += ".control\n"
    for k, (_, w, b, h, x) in enumerate(cf):
        s += tn.alters(tn.levels(w, b, h, x, VDDS))
        s += f"op\nlet a=v(vp)\nlet c=v(vm)\nlet p=-i(vvdd)\necho \"RES k={k} vp=$&a vm=$&c idd=$&p\"\n"
    s += ".endc\n.end\n"
    res = tn.parse_res(tn.run(s, f"{TAG}_dccrit"))
    rows = []
    for (st, w, b, h, x), r in zip(cf, res):
        m = tn.ideal(w, b, h, x, VDDS)
        dv = r["vp"] - r["vm"]
        rows.append(dict(set=st, w=" ".join(map(str, w)), b=b, h=h, x="".join(map(str, x)), S=m["S"],
                         dv_mod_mV=1e3 * m["dv"], dv_sim_mV=1e3 * dv, err_LSB=(dv - m["dv"]) / m["lsb"],
                         vmin=min(r["vp"], r["vm"]), P_W=r["idd"] * VDDS,
                         sign_ok=int(m["dv"] == 0 or np.sign(dv) == np.sign(m["dv"]))))
    save_csv(os.path.join(R, f"{TAG}_dccrit.csv"), rows)
    half = [r for r in rows if r["set"] == "half"]
    nerr = sum(1 - r["sign_ok"] for r in rows)
    metric("DC critiques : erreurs de signe", nerr, f"/{len(rows)}", "0", nerr == 0, f"results/{TAG}_dccrit.csv")
    metric("|ΔV| min à ±0.5 LSB", round(min(abs(r["dv_sim_mV"]) for r in half), 3), "mV", "> 3σ_os (MC)", True,
           f"results/{TAG}_dccrit.csv")
    metric("erreur ΔV max (codes critiques)", round(max(abs(r["err_LSB"]) for r in rows), 4), "LSB", "< 0.5 LSB",
           max(abs(r["err_LSB"]) for r in rows) < 0.5, f"results/{TAG}_dccrit.csv")
    vmin = min(r["vmin"] for r in rows)
    metric("mode commun min V±", round(vmin, 4), "V", ">= 0.75 V (fenêtre comparateur)", vmin >= 0.75,
           f"results/{TAG}_dccrit.csv")


# ======================================================================== comparateur : offset, hystérésis, fenêtre CM
def comp_tb(title):
    return hdr(title) + "XCMP inp inn clk q qb vdd 0 comparator\n"


def t_comp():
    print("== Comparateur : offset et hystérésis (rampe lente) vs mode commun")
    ncyc, span = 40, 4e-3       # pas de rampe 0.2 mV/cycle
    T = tn.T_EVAL
    rows = []
    for vcm in np.round(np.arange(0.5, VDDS + 1e-9, 0.1), 3):
        tend = 2 * ncyc * T
        s = comp_tb(f"comp offset vcm={vcm}")
        s += (f"VCLK clk 0 PULSE(0 {VDDS} {tn.T_CLK_R} 0.2n 0.2n {tn.T_CLK_F-tn.T_CLK_R} {T})\n"
              f"VDP dp 0 PWL(0 {-span} {ncyc*T} {span} {2*ncyc*T} {-span})\n"
              f"BINP inp 0 V={vcm}+v(dp)/2\nBINN inn 0 V={vcm}-v(dp)/2\n"
              f".tran 0.2n {tend} 0 0.02n\n.control\nrun\nwrdata {tn.OUTD}/{TAG}_comp_{vcm:.2f}.dat v(dp) v(q)\n.endc\n.end\n")
        tn.run(s, f"{TAG}_comp_{vcm:.2f}")
        t, (dp, q) = tn.wrdata(f"{tn.OUTD}/{TAG}_comp_{vcm:.2f}.dat")
        ts = np.arange(ncyc * 2) * T + tn.T_SAMPLE
        qs = np.interp(ts, t, q) > VDDS / 2
        dps = np.interp(ts - (tn.T_SAMPLE - tn.T_CLK_R), t, dp)       # ΔV au front d'horloge
        up, dn = qs[:ncyc], qs[ncyc:]
        v_up = dps[:ncyc][np.argmax(up)] if up.any() and not up.all() else float("nan")
        v_dn = dps[ncyc:][np.argmax(~dn)] if (~dn).any() and dn[0] else float("nan")
        # fonctionnel = une seule transition par demi-rampe (pas de décisions erratiques)
        works = bool(up.any() and not up.all() and (~dn).any() and np.count_nonzero(np.diff(up.astype(int))) == 1
                     and np.count_nonzero(np.diff(dn.astype(int))) == 1)
        rows.append(dict(vcm=vcm, th_rising_mV=1e3 * v_up, th_falling_mV=1e3 * v_dn,
                         offset_mV=1e3 * (v_up + v_dn) / 2, hyst_mV=1e3 * (v_up - v_dn), works=int(works)))
        print(f"  Vcm={vcm:.2f} : seuil montant {1e3*v_up:+.3f} mV, descendant {1e3*v_dn:+.3f} mV, ok={works}")
    save_csv(os.path.join(R, f"{TAG}_comp_offset.csv"), rows)
    ok = [r for r in rows if r["works"]]
    win = (min(r["vcm"] for r in ok), max(r["vcm"] for r in ok)) if ok else (float("nan"),) * 2
    metric("fenêtre CM fonctionnelle (rampe ±4 mV, 1 transition)", f"{win[0]:.2f}–{win[1]:.2f}", "V", "⊇ [0.75, 1.80]",
           ok and win[0] <= 0.75 and win[1] >= 1.8 - 1e-9, f"results/{TAG}_comp_offset.csv")
    inwin = [r for r in ok if r["vcm"] >= 0.75]
    off = max(abs(r["offset_mV"]) for r in inwin)
    hy = max(abs(r["hyst_mV"]) for r in inwin)
    metric("offset systématique max (0.75–1.8 V)", round(off, 3), "mV", "< LSB/6 = 2.42 mV (aléatoire en phase 3)",
           off < 2.42, f"results/{TAG}_comp_offset.csv")
    metric("hystérésis max (0.75–1.8 V)", round(hy, 3), "mV", "< LSB/6 = 2.42 mV", hy < 2.42,
           f"results/{TAG}_comp_offset.csv")


def t_tdec():
    print("== Comparateur : temps de décision vs ΔV (Vcm = 0.84 et 1.3 V)")
    T = tn.T_EVAL
    rows = []
    dvs = [1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 7.26e-3, 1e-2, 3e-2, 1e-1]
    for vcm in (0.84, 1.3):
        s = comp_tb(f"tdec vcm={vcm}")
        s += (f"VCLK clk 0 PULSE(0 {VDDS} {tn.T_CLK_R} 0.2n 0.2n {tn.T_CLK_F-tn.T_CLK_R} {T})\n"
              f"VDP dp 0 PWL(0 -0.05 {T} -0.05 {T+1e-9} 1e-3)\n"
              f"BINP inp 0 V={vcm}+v(dp)/2\nBINN inn 0 V={vcm}-v(dp)/2\n.tran 0.02n {2*T}\n.control\n")
        for dv in dvs:
            s += (f"alter @vdp[pwl] = [ 0 -0.05 {T} -0.05 {T+1e-9} {dv} ]\nrun\n"
                  f"let td = -1\n"
                  f"meas tran qlow FIND v(q) AT={T-5e-9}\n"
                  f"meas tran td TRIG v(clk) VAL={VDDS/2} RISE=2 TARG v(q) VAL={VDDS/2} TD={T+tn.T_CLK_R-2e-9} RISE=1\n"
                  f"echo \"RES vcm={vcm} dv={dv} td=$&td qlow=$&qlow\"\n")
        s += ".endc\n.end\n"
        for r in tn.parse_res(tn.run(s, f"{TAG}_tdec_{vcm}", allow=("out of interval",))):
            # nan : pas de décision, ou Q pas remis à 0 par la décision précédente à −50 mV
            td = r["td"] if (r["td"] > 0 and r["qlow"] < VDDS / 2) else float("nan")
            rows.append(dict(vcm=r["vcm"], dV_V=r["dv"], t_dec_s=td))
            print(f"  Vcm={r['vcm']} ΔV={r['dv']:.1e} V : t_dec = {td*1e9:.3f} ns")
    save_csv(os.path.join(R, f"{TAG}_comp_tdec.csv"), rows)
    big = [r["t_dec_s"] for r in rows if r["dV_V"] >= 7.26e-3 - 1e-12]
    worst = float("inf") if any(np.isnan(big)) else max(big)
    metric("t_dec à ΔV = 0.5 LSB_min (7.26 mV), pire Vcm", round(worst * 1e9, 3), "ns",
           f"< {(tn.T_CLK_F-tn.T_CLK_R-5e-9)*1e9:.0f} ns (fenêtre horloge haute − marge)",
           worst < tn.T_CLK_F - tn.T_CLK_R - 5e-9, f"results/{TAG}_comp_tdec.csv")


# ======================================================================== stabilisation du nœud
SETTLE_CFG = [  # (nom, w, b, h, x_avant, x_après)
    ("S=1.5", (1, 0, 0, 0), 0, 1, (0, 0, 0, 0), (1, 0, 0, 0)),
    ("S=7.5", (7, 0, 0, 0), 0, 1, (0, 0, 0, 0), (1, 0, 0, 0)),
    ("S=14.5", (7, 7, 0, 0), 0, 1, (0, 0, 0, 0), (1, 1, 0, 0)),
    ("S=19.5 (pire modèle)", (7, 7, 5, 0), 0, 1, (0, 0, 0, 0), (1, 1, 1, 0)),
    ("S=28.5", (7, 7, 7, 7), 0, 1, (0, 0, 0, 0), (1, 1, 1, 1)),
    ("S=40.5", (7, 7, 7, 7), 12, 1, (0, 0, 0, 0), (1, 1, 1, 1)),
    ("S=59.5", (7, 7, 7, 7), -31, 1, (0, 0, 0, 0), (1, 1, 1, 1)),
    ("S=28.5 opposé", (7, 7, -7, -7), 0, 1, (1, 1, 0, 0), (0, 0, 1, 1)),
]


def t_settle():
    print("== Stabilisation de V± (horloge à 0, pas d'entrée à t = 20 ns puis retour à t = 270 ns)")
    rows = []
    sub = os.environ.get("TN_SETTLE_SUBSET")          # ex. "1,2,3" (indices de SETTLE_CFG) pour les corners
    cfgs = [SETTLE_CFG[int(i)] for i in sub.split(",")] if sub else SETTLE_CFG
    for name, w, b, h, x0, x1 in cfgs:
        lv0, lv1 = tn.levels(w, b, h, x0, VDDS), tn.levels(w, b, h, x1, VDDS)
        s = hdr(f"settle {name}") + tn.dut_line(NET)
        for p in tn.CTRL:
            s += f"V{p} {p.lower()} 0 " + tn.pwl([(0, lv0[p]), (20e-9, lv1[p]), (270e-9, lv0[p])]) + "\n"
        s += f"VCLK clk 0 DC 0\n.tran 0.1n 520n\n.control\nrun\nwrdata {tn.OUTD}/{TAG}_settle_{len(rows)}.dat v(vp) v(vm)\n.endc\n.end\n"
        tn.run(s, f"{TAG}_settle_{len(rows)}")
        t, (vp, vm) = tn.wrdata(f"{tn.OUTD}/{TAG}_settle_{len(rows)}.dat")
        m1, m0 = tn.ideal(w, b, h, x1, VDDS), tn.ideal(w, b, h, x0, VDDS)
        lsb = m1["lsb"]
        res = {}
        for edge, ta, tb_ in (("montée", 20e-9, 270e-9), ("descente", 270e-9, 520e-9)):
            sel = (t >= ta) & (t <= tb_)
            tt = t[sel] - ta
            ok_all = []
            for v in (vp[sel], vm[sel]):
                fin = v[-1]
                bad = np.where(np.abs(v - fin) > 0.5 * lsb)[0]
                ok_all.append(tt[bad[-1] + 1] if len(bad) else 0.0)
            res[edge] = max(ok_all)
            res[edge + "_final_dv"] = (vp[sel][-1] - vm[sel][-1])
        rows.append(dict(config=name, S=m1["S"], D=m1["D"], lsb_mV=1e3 * lsb, t_settle_rise_ns=1e9 * res["montée"],
                         t_settle_fall_ns=1e9 * res["descente"], dv_final_mV=1e3 * res["montée_final_dv"],
                         dv_model_mV=1e3 * m1["dv"]))
        print(f"  {name:22s} t_settle(0.5 LSB) = {1e9*res['montée']:5.1f} / {1e9*res['descente']:5.1f} ns")
    save_csv(os.path.join(R, f"{TAG}_settle.csv"), rows)
    worst = max(max(r["t_settle_rise_ns"], r["t_settle_fall_ns"]) for r in rows)
    wc = max(rows, key=lambda r: max(r["t_settle_rise_ns"], r["t_settle_fall_ns"]))["config"]
    metric(f"t_settle 0.5 LSB, pire config ({wc})", round(worst, 2), "ns", "<= 50 ns (visé)", worst <= 50,
           f"results/{TAG}_settle.csv")
    budget = tn.T_CLK_R * 1e9                 # temps entre changement de code et front d horloge
    metric("t_settle vs budget dur (front d'horloge)", round(worst, 2), "ns", f"< {budget:.0f} ns", worst < budget,
           f"results/{TAG}_settle.csv")


# ======================================================================== fonctionnel ET / OU / NON-ET
GATES = {"AND": ((2, 2), -3), "OR": ((2, 2), -1), "NAND": ((-2, -2), 3)}


def gate_code(g, x1, x2):
    (w1, w2), b = GATES[g]
    return ((w1, w2, 0, 0), b, 0, (x1, x2, 0, 0))


def run_slots(codes, name, save=("v(vp)", "v(vm)", "v(clk)", "v(q)", "i(vvdd)")):
    tend = len(codes) * tn.T_EVAL
    s = hdr(name) + tn.dut_line(NET) + tn.slot_sources(codes, VDDS)
    s += ".save " + " ".join(save) + "\n"   # limite la mémoire (PEX : ~37k nœuds)
    s += (f".tran 0.1n {tend} 0 {TMAX}\n.control\nrun\nwrdata {tn.OUTD}/{name}.dat " + " ".join(save) + "\n.endc\n.end\n")
    tn.run(s, name)
    t, cols = tn.wrdata(f"{tn.OUTD}/{name}.dat")
    ts = np.arange(len(codes)) * tn.T_EVAL + tn.T_SAMPLE
    q = np.interp(ts, t, cols[3]) > VDDS / 2
    return t, cols, q.astype(int)


def kickback(t, vp, vm, clk, n):
    """ΔV(t) − ΔV(juste avant le front) pendant l'horloge haute, max sur les périodes."""
    kb, kbcm, rec = [], [], []
    for k in range(n):
        t0 = k * tn.T_EVAL + tn.T_CLK_R
        pre = np.interp(t0 - 1e-9, t, vp - vm)
        precm = np.interp(t0 - 1e-9, t, (vp + vm) / 2)
        sel = (t >= t0) & (t <= k * tn.T_EVAL + tn.T_EVAL)
        kb.append(np.abs((vp - vm)[sel] - pre).max())
        kbcm.append(np.abs(((vp + vm) / 2)[sel] - precm).max())
        # fenêtre de décision (1 ns après le front, Q bascule à ≈ 0.4 ns) : rapport kickback / ΔV et signe
        win = (t >= t0) & (t <= t0 + 1e-9)
        dvw = (vp - vm)[win]
        rec.append((np.abs(dvw - pre).max() / max(abs(pre), 1e-6), bool(np.all(np.sign(dvw) == np.sign(pre)))))
    return max(kb), max(kbcm), max(r[0] for r in rec), sum(not r[1] for r in rec)


def t_func():
    print("== Fonctionnel : ET, OU, NON-ET (12 évaluations à 10 MHz)")
    codes, exp, lab = [], [], []
    # TN_FUNC_GATES=AND,OR : sous-ensemble (PEX : une séquence de 1.2 µs dépasse la mémoire de la VM)
    for g in [g for g in GATES if g in os.environ.get("TN_FUNC_GATES", ",".join(GATES)).split(",")]:
        for x1, x2 in itertools.product((0, 1), repeat=2):
            codes.append(gate_code(g, x1, x2))
            (w1, w2), b = GATES[g]
            exp.append(int(w1 * x1 + w2 * x2 + b > 0))
            lab.append(f"{g}({x1},{x2})")
    t, (vp, vm, clk, q, idd), qs = run_slots(codes, f"{TAG}_func")
    rows = [dict(slot=k, eval=lab[k], expected=exp[k], q_sim=int(qs[k]), ok=int(exp[k] == qs[k])) for k in range(len(codes))]
    save_csv(os.path.join(R, f"{TAG}_func.csv"), rows)
    nerr = sum(1 - r["ok"] for r in rows)
    kb, kbcm, kbrel, nflip = kickback(t, vp, vm, clk, len(codes))
    pavg = float(np.trapezoid(-idd, t) / (t[-1] - t[0]) * VDDS)
    metric("ET/OU/NON-ET : erreurs", nerr, f"/{len(rows)}", "0", nerr == 0, f"results/{TAG}_func.csv")
    metric("kickback différentiel max sur V+−V−", round(kb * 1e3, 3), "mV", "< LSB/4 (≈ 4 mV)", kb < 4e-3,
           f"sim/out/{TAG}_func.dat")
    metric("kickback / ΔV dans la fenêtre de décision (1 ns), max", round(kbrel * 100, 1), "%", "info (< 100 % : pas d'inversion)",
           kbrel < 1, f"sim/out/{TAG}_func.dat")
    metric("inversions de signe de ΔV pendant la décision", nflip, "", "0", nflip == 0, f"sim/out/{TAG}_func.dat")
    metric("kickback mode commun max", round(kbcm * 1e3, 3), "mV", "info", True, f"sim/out/{TAG}_func.dat")
    metric("puissance moyenne (séquence ET/OU/NON-ET, 10 MHz)", round(pavg * 1e6, 2), "µW", "info (S12 v2)", True,
           f"sim/out/{TAG}_func.dat")


def t_xor():
    print("== XOR 2-2-1 multiplexé : 3 évaluations successives, sorties cachées réinjectées (Python)")
    xs = list(itertools.product((0, 1), repeat=2))
    codes = [gate_code("OR", *x) for x in xs]
    _, _, q = run_slots(codes, f"{TAG}_xor_s1")
    h1 = list(q[:4])
    codes += [gate_code("NAND", *x) for x in xs]
    _, _, q = run_slots(codes, f"{TAG}_xor_s2")
    h2 = list(q[4:8])
    codes += [gate_code("AND", h1[k], h2[k]) for k in range(4)]
    t, cols, q = run_slots(codes, f"{TAG}_xor")         # séquence complète (12 périodes)
    y = list(q[8:12])
    rows = [dict(x1=x[0], x2=x[1], h1=h1[k], h2=h2[k], y=y[k], expected=x[0] ^ x[1], ok=int(y[k] == (x[0] ^ x[1])))
            for k, x in enumerate(xs)]
    save_csv(os.path.join(R, f"{TAG}_xor.csv"), rows)
    nerr = sum(1 - r["ok"] for r in rows)
    for r in rows:
        print(f"  x={r['x1']}{r['x2']} h1={r['h1']} h2={r['h2']} -> y={r['y']} (attendu {r['expected']})")
    metric("XOR 2-2-1 : erreurs", nerr, "/4", "0", nerr == 0, f"results/{TAG}_xor.csv")


# ======================================================================== SAR
SAR_VEC = [((7, 7, 7, 7), (1, 1, 1, 1)), ((-7, -7, -7, -7), (1, 1, 1, 1)), ((0, 0, 0, 0), (0, 0, 0, 0)),
           ((3, -5, 2, 6), (1, 1, 0, 1)), ((-1, 4, -6, 7), (0, 1, 1, 1)), ((5, 5, -3, 0), (1, 0, 1, 1)),
           ((2, -2, 1, -1), (1, 0, 1, 0)), ((-7, 6, 0, 1), (1, 1, 0, 1)), ((4, 4, 4, -7), (0, 1, 1, 1)),
           ((1, 1, 1, 1), (1, 0, 0, 0))]


def t_sar():
    print("== SAR : lecture de Σw·x par dichotomie sur le biais (demi-LSB actif), 6 décisions par lecture")
    rows = []
    for vi, (w, x) in enumerate(SAR_VEC):
        lo, hi, codes, trace = -31, 31, [], []
        while lo < hi:
            mid = (lo + hi) // 2
            codes.append((w, mid, 1, x))
            _, _, q = run_slots(codes, f"{TAG}_sar_{vi}")
            d = int(q[-1])
            trace.append(f"{mid}:{d}")
            if d:
                hi = mid
            else:
                lo = mid + 1
        s_read, s_true = 1 - lo, int(np.dot(w, x))
        rows.append(dict(vec=vi, w=" ".join(map(str, w)), x="".join(map(str, x)), s_true=s_true, s_read=s_read,
                         err=s_read - s_true, decisions=len(trace), trace=" ".join(trace)))
        print(f"  w={w} x={x} : Σw·x = {s_true:+d}, lu = {s_read:+d}  [{' '.join(trace)}]")
    save_csv(os.path.join(R, f"{TAG}_sar.csv"), rows)
    nerr = sum(r["err"] != 0 for r in rows)
    metric("SAR : lectures fausses", nerr, f"/{len(rows)}", "0", nerr == 0, f"results/{TAG}_sar.csv")


# ======================================================================== puissance statique pire code
def worst_power_code():
    """Recherche exhaustive du code (w, b, h, x) qui maximise P statique (modèle idéal)."""
    best = (0, None)
    wv = np.array(list(itertools.product(range(-7, 8), repeat=4)))
    xv = np.array(list(itertools.product((0, 1), repeat=4)))
    Pp = np.clip(wv, 0, None) @ xv.T
    Nn = np.clip(-wv, 0, None) @ xv.T
    Sw = np.abs(wv).sum(1)[:, None]
    for b in range(-31, 32):
        for h in (0, 1):
            D = Sw + abs(b) + 0.5 * h + tn.G0
            gp = tn.G0 + Pp + max(b, 0)
            gn = tn.G0 + Nn + max(-b, 0) + 0.5 * h
            pg = (gp * (D - gp) + gn * (D - gn)) / D
            k = np.unravel_index(np.argmax(pg), pg.shape)
            if pg[k] > best[0]:
                best = (float(pg[k]), (tuple(int(v) for v in wv[k[0]]), b, h, tuple(int(v) for v in xv[k[1]])))
    return best


def t_power():
    print("== Puissance statique au pire code (recherche exhaustive sur le modèle, puis simulation)")
    pg, code = worst_power_code()
    s = hdr("P pire code") + tn.dut_line(NET) + tn.dc_sources(tn.levels(*code, vdd=VDDS))
    s += ".control\nop\nlet p=-i(vvdd)\necho \"RES idd=$&p\"\n.endc\n.end\n"
    r = tn.parse_res(tn.run(s, f"{TAG}_pmax"))[0]
    p = r["idd"] * VDDS
    save_csv(os.path.join(R, f"{TAG}_power.csv"), [dict(code=str(code), P_model_W=VDDS**2 * pg / RU, P_sim_W=p)])
    metric(f"P statique pire code {code}", round(p * 1e6, 2), "µW", "info (S12 v2)", True,
           f"results/{TAG}_power.csv")


TESTS = dict(ron=t_ron, dc=t_dc, dccrit=t_dccrit, comp=t_comp, tdec=t_tdec, settle=t_settle, func=t_func, xor=t_xor, sar=t_sar,
             power=t_power)

if __name__ == "__main__":
    todo = list(TESTS) if sys.argv[1:] == ["all"] else sys.argv[1:]
    print(f"corner={CORNER} T={TEMP} VDD={VDDS} netlist={os.path.relpath(NET, tn.ROOT)}")
    for name in todo:
        t0 = time.time()
        TESTS[name]()
        print(f"   ({time.time()-t0:.0f} s)")
    mpath = os.path.join(R, f"{TAG}_metrics_{'_'.join(todo)}.csv")
    if METRICS:
        save_csv(mpath, METRICS)
