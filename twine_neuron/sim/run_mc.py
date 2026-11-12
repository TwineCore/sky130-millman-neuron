#!/usr/bin/env python3
"""Phase 3 — Monte Carlo désappariement (sections *_mm du PDK). S'exécute DANS le conteneur :

    cd /foss/designs/twine_neuron && python3 sim/run_mc.py [sys|comp|all] [N=200] [-j 4]

sys  : neurone complet, séquence de décisions critiques (|Σw·x+b−0.5h| = 0.5 LSB + portes), N dies.
       Par die et par période : ΔV juste avant le front d'horloge et Q échantillonné.
comp : comparateur seul, rampe ΔV de −15 à +15 mV (0.5 mV/période), seuil de bascule = offset, N dies.
Chaque worker est un ngspice distinct (graine `setseed` différente) ; tirage par `reset` dans `dowhile`
(méthode validée par sim/pdk_char/avt_mc.spice).
Env : TN_MC_CORNER (tt_mm), TN_VDD (1.8), TN_TEMP (27), TN_NETLIST.
Sorties : results/mc_sys.csv, results/mc_comp.csv, results/mc_summary.csv.
"""
import csv
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tn                                              # noqa: E402
import run_phase2 as p2                                # noqa: E402

CORNER = os.environ.get("TN_MC_CORNER", "tt_mm")
VDD = float(os.environ.get("TN_VDD", "1.8"))
TEMP = float(os.environ.get("TN_TEMP", "27"))
NET = os.environ.get("TN_NETLIST", tn.NETLIST)
SUF = os.environ.get("TN_MC_SUFFIX", "")             # ex. « _1v62 » pour une 2ᵉ campagne
RES = os.path.join(tn.ROOT, "results")
TMAX = "0.02n"


def seq_codes():
    cf = [c for c in p2.crit_codes() if c[0] in ("half", "gate")]
    return [(w, b, h, x) for (_, w, b, h, x) in cf]


def sys_netlist(ndie, seed, name):
    codes = seq_codes()
    tend = len(codes) * tn.T_EVAL
    s = tn.header(f"MC système {CORNER}", CORNER, TEMP, VDD, NET) + tn.dut_line(NET) + tn.slot_sources(codes, VDD)
    s += f".control\nsetseed {seed}\nlet die = 0\ndowhile die < {ndie}\n  reset\n  tran 0.1n {tend} 0 {TMAX}\n"
    for j in range(len(codes)):
        te = j * tn.T_EVAL + tn.T_CLK_R - 0.5e-9
        ts = j * tn.T_EVAL + tn.T_SAMPLE
        s += (f"  meas tran dv{j} FIND v(vp,vm) AT={te:.4e}\n  meas tran q{j} FIND v(q) AT={ts:.4e}\n"
              f"  echo \"RES die=$&die j={j} dv=$&dv{j} q=$&q{j}\"\n")
    s += "  destroy all\n  let die = die + 1\nend\n.endc\n.end\n"
    return s, codes


TRK_CYC, TRK_AVG = 20, 8          # boucle de suivi : 20 périodes, moyenne des 8 dernières
COMP_TMAX = "0.05n"               # validé : seuil identique à 20 ps (−2.905 mV pour −3 mV imposés, run_mc.py validate)


def comp_netlist(ndie, seed, vcm, tmax=None, sys_off=0.0):
    """Offset par boucle de suivi bang-bang : ΔV intégré, pente −/+ selon Q (latché) ;
    pas de 2 mV/période pendant 8 périodes (couvre ±16 mV), puis 0.25 mV/période ;
    offset = moyenne de ΔV sur les TRK_AVG dernières périodes (résolution ≈ ±0.125 mV)."""
    T = tn.T_EVAL
    tend = TRK_CYC * T
    s = tn.header(f"MC comparateur {CORNER} vcm={vcm}", CORNER, TEMP, VDD, NET)
    s += "XCMP inp inn clk q qb vdd 0 comparator\n"
    s += (f"VCLK clk 0 PULSE(0 {VDD} {tn.T_CLK_R} 0.2n 0.2n {tn.T_CLK_F-tn.T_CLK_R} {T})\n"
          f"Cdp dp 0 1p\n"
          f"Bdp 0 dp I=1e-12*(time<{8*T} ? 2e-3 : 0.25e-3)/{T}*tanh(({VDD/2}-v(q))*20)\n"
          f".ic v(dp)=0\n"
          f"BINP inp 0 V={vcm}+v(dp)/2+{sys_off/2}\nBINN inn 0 V={vcm}-v(dp)/2-{sys_off/2}\n")
    s += (f".control\nsetseed {seed}\nlet die = 0\ndowhile die < {ndie}\n  reset\n"
          f"  tran 0.2n {tend} 0 {tmax or COMP_TMAX} uic\n"
          f"  meas tran off AVG v(dp) FROM={(TRK_CYC-TRK_AVG)*T} TO={tend}\n"
          f"  echo \"RES die=$&die vcm={vcm} off=$&off\"\n  destroy all\n  let die = die + 1\nend\n.endc\n.end\n")
    return s, None


def run_worker(kind, w, ndie, arg=None):
    seed = 1000 + 17 * w + (0 if kind == "sys" else 500)
    if kind == "sys":
        s, _ = sys_netlist(ndie, seed, f"mc_sys{SUF}_{w}")
        name = f"mc_sys{SUF}_{w}"
    else:
        s, _ = comp_netlist(ndie, seed, arg)
        name = f"mc_comp{SUF}_{arg:.2f}_{w}"
    out = tn.run(s, name, timeout=6 * 3600, allow=("out of interval", "no such vector"))
    rows = tn.parse_res(out)
    for r in rows:
        r["die"] = int(r["die"]) + 10000 * w
    return rows


def save(rows, path):
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)


def mc_sys(N, nj):
    codes = seq_codes()
    per = [N // nj + (1 if k < N % nj else 0) for k in range(nj)]
    t0 = time.time()
    with ThreadPoolExecutor(nj) as ex:
        parts = list(ex.map(lambda k: run_worker("sys", k, per[k]), range(nj)))
    rows = []
    for part in parts:
        for r in part:
            j = int(r["j"])
            w, b, h, x = codes[j]
            m = tn.ideal(w, b, h, x, VDD)
            exp = int(m["dv"] > 0)
            q = int(r["q"] > VDD / 2)
            rows.append(dict(die=r["die"], slot=j, w=" ".join(map(str, w)), b=b, h=h, x="".join(map(str, x)),
                             dv_model_mV=1e3 * m["dv"], dv_sim_mV=1e3 * r["dv"], expected=exp, q=q, ok=int(q == exp)))
    save(rows, os.path.join(RES, f"mc_sys{SUF}.csv"))
    ndies = len({r["die"] for r in rows})
    nerr = sum(1 - r["ok"] for r in rows)
    dies_bad = len({r["die"] for r in rows if not r["ok"]})
    # écart ΔV_sim − ΔV_modèle (désappariement du réseau), en LSB du code
    err_lsb = []
    for r in rows:
        w = tuple(int(v) for v in r["w"].split())
        x = tuple(int(c) for c in r["x"])
        lsb = tn.ideal(w, r["b"], r["h"], x, VDD)["lsb"]
        err_lsb.append((r["dv_sim_mV"] - r["dv_model_mV"]) * 1e-3 / lsb)
    err_lsb = np.array(err_lsb)
    print(f"  MC système : {ndies} dies × {len(codes)} décisions = {len(rows)} ; erreurs {nerr} ; dies fautifs {dies_bad} "
          f"({time.time()-t0:.0f} s)")
    return [dict(campaign=f"sys{SUF}", corner=CORNER, vdd=VDD, temp=TEMP, metric="décisions fausses",
                 value=nerr, unit=f"/{len(rows)}", spec="0", status="OK" if nerr == 0 else "NON",
                 source=f"results/mc_sys{SUF}.csv"),
            dict(campaign=f"sys{SUF}", corner=CORNER, vdd=VDD, temp=TEMP, metric="dies avec ≥ 1 erreur",
                 value=dies_bad, unit=f"/{ndies}", spec="0", status="OK" if dies_bad == 0 else "NON",
                 source=f"results/mc_sys{SUF}.csv"),
            dict(campaign=f"sys{SUF}", corner=CORNER, vdd=VDD, temp=TEMP, metric="σ(ΔV_sim − ΔV_modèle) réseau",
                 value=round(float(err_lsb.std()), 4), unit="LSB", spec="info", status="OK",
                 source=f"results/mc_sys{SUF}.csv"),
            dict(campaign=f"sys{SUF}", corner=CORNER, vdd=VDD, temp=TEMP, metric="|ΔV_sim − ΔV_modèle| max",
                 value=round(float(np.abs(err_lsb).max()), 4), unit="LSB", spec="< 0.5 LSB",
                 status="OK" if np.abs(err_lsb).max() < 0.5 else "NON", source=f"results/mc_sys{SUF}.csv")]


def mc_comp(N, nj, vcms=(0.84,)):
    rows, summ = [], []
    jobs = [(v, k) for v in vcms for k in range(nj)]
    per = [N // nj + (1 if k < N % nj else 0) for k in range(nj)]
    t0 = time.time()
    with ThreadPoolExecutor(nj) as ex:
        parts = list(ex.map(lambda vk: (vk[0], run_worker("comp", vk[1], per[vk[1]], vk[0])), jobs))
    for vcm, part in parts:
        for r in part:
            # ΔV d'entrée au seuil = −offset du comparateur ; on rapporte le seuil (convention ΔV = V+ − V−)
            rows.append(dict(die=r["die"], vcm=vcm, threshold_mV=1e3 * r["off"]))
    save(rows, os.path.join(RES, f"mc_comp{SUF}.csv"))
    for vcm in vcms:
        o = np.array([r["threshold_mV"] for r in rows if r["vcm"] == vcm])
        nan = int(np.isnan(o).sum())
        o = o[~np.isnan(o)]
        print(f"  MC comparateur Vcm={vcm} : {len(o)} dies, μ = {o.mean():+.3f} mV, σ = {o.std(ddof=1):.3f} mV, "
              f"max |.| = {np.abs(o).max():.2f} mV, non mesurés {nan}")
        summ.append(dict(campaign=f"comp{SUF}", corner=CORNER, vdd=VDD, temp=TEMP, metric=f"σ_os comparateur (Vcm {vcm} V)",
                         value=round(float(o.std(ddof=1)), 3), unit="mV", spec="< LSB_min/6 = 2.42 mV",
                         status="OK" if o.std(ddof=1) < 2.42 else "NON", source=f"results/mc_comp{SUF}.csv"))
        summ.append(dict(campaign=f"comp{SUF}", corner=CORNER, vdd=VDD, temp=TEMP, metric=f"|offset| max (Vcm {vcm} V)",
                         value=round(float(np.abs(o).max()), 3), unit="mV", spec="info (résolution ±0.125 mV)",
                         status="OK", source=f"results/mc_comp{SUF}.csv"))
    print(f"  ({time.time()-t0:.0f} s)")
    return summ


def dcnet_codes():
    # codes les plus serrés : ±0.5 LSB aux 4 premiers vecteurs SAR (S max = 56.5 et S moyens) + mode commun min
    cf = p2.crit_codes()
    half = [c for c in cf if c[0] == "half"][:8]
    return half + [c for c in cf if c[0] == "cm"]


def dcnet_worker(wk, n):
    cf = dcnet_codes()
    s = tn.header(f"MC réseau DC {CORNER}", CORNER, TEMP, VDD, NET) + tn.dut_line(NET)
    s += tn.dc_sources(tn.levels((0, 0, 0, 0), 0, 0, (0, 0, 0, 0), VDD))
    s += f".control\nsetseed {4242 + 31 * wk}\nlet die = 0\ndowhile die < {n}\n  reset\n"
    for k, (_, w, b, h, x) in enumerate(cf):
        s += "".join("  " + l + "\n" for l in tn.alters(tn.levels(w, b, h, x, VDD)).splitlines())
        s += f"  op\n  let d{k} = v(vp) - v(vm)\n  echo \"RES die=$&die k={k} dv=$&d{k}\"\n  destroy all\n"
    s += "  let die = die + 1\nend\n.endc\n.end\n"
    res = tn.parse_res(tn.run(s, f"mc_dcnet{SUF}_{wk}", timeout=6 * 3600))
    for r in res:
        r["die"] = int(r["die"]) + 10000 * wk
    return res


def mc_dcnet(N, nj=4):
    """Désappariement du réseau seul : ΔV en DC (op) aux codes critiques, N dies répartis sur nj ngspice."""
    cf = dcnet_codes()
    per = [N // nj + (1 if k < N % nj else 0) for k in range(nj)]
    t0 = time.time()
    with ThreadPoolExecutor(nj) as ex:
        parts = list(ex.map(lambda k: dcnet_worker(k, per[k]), range(nj)))
    res = [r for p in parts for r in p]
    rows = []
    for r in res:
        st, w, b, h, x = cf[int(r["k"])]
        m = tn.ideal(w, b, h, x, VDD)
        rows.append(dict(die=int(r["die"]), set=st, w=" ".join(map(str, w)), b=b, h=h, x="".join(map(str, x)),
                         dv_model_mV=1e3 * m["dv"], dv_sim_mV=1e3 * r["dv"], err_LSB=(r["dv"] - m["dv"]) / m["lsb"]))
    save(rows, os.path.join(RES, f"mc_dcnet{SUF}.csv"))
    e = np.array([r["err_LSB"] for r in rows])
    half = np.array([abs(r["dv_sim_mV"]) for r in rows if r["set"] == "half"])
    sgn = sum(1 for r in rows if r["dv_model_mV"] != 0 and np.sign(r["dv_sim_mV"]) != np.sign(r["dv_model_mV"]))
    nd = len({r["die"] for r in rows})
    print(f"  MC réseau : {nd} dies, σ(err) = {e.std():.4f} LSB, max |err| = {np.abs(e).max():.4f} LSB, "
          f"|ΔV| min à ±0.5 LSB = {half.min():.3f} mV, erreurs de signe {sgn} ({time.time()-t0:.0f} s)")
    base = dict(campaign=f"dcnet{SUF}", corner=CORNER, vdd=VDD, temp=TEMP, source=f"results/mc_dcnet{SUF}.csv")
    return [dict(base, metric="dies", value=nd, unit="", spec=">= 200", status="OK" if nd >= 200 else "NON"),
            dict(base, metric="σ(ΔV_sim − ΔV_modèle) réseau", value=round(float(e.std()), 4), unit="LSB", spec="info",
                 status="OK"),
            dict(base, metric="|ΔV_sim − ΔV_modèle| max", value=round(float(np.abs(e).max()), 4), unit="LSB",
                 spec="< 0.5 LSB", status="OK" if np.abs(e).max() < 0.5 else "NON"),
            dict(base, metric="|ΔV| min aux codes ±0.5 LSB", value=round(float(half.min()), 3), unit="mV",
                 spec="info : combiné au seuil MC du comparateur dans sim/mc_combine.py", status="info"),
            dict(base, metric="erreurs de signe de ΔV", value=sgn, unit="", spec="0", status="OK" if sgn == 0 else "NON")]


def validate():
    """Validation de la boucle de suivi (sans désappariement) : offset imposé +3 mV, pas max 20 et 50 ps."""
    global CORNER
    CORNER = CORNER.replace("_mm", "")
    for tm in ("0.02n", "0.05n"):
        s, _ = comp_netlist(1, 1, 0.84, tmax=tm, sys_off=3e-3)
        t0 = time.time()
        r = tn.parse_res(tn.run(s, f"mc_validate_{tm}"))
        print(f"  validation tmax={tm} : seuil = {1e3*r[0]['off']:+.3f} mV (attendu −3.000) ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("N=") and a != "-j" and not a.isdigit()]
    what = args[0] if args else "all"
    N = int(next((a[2:] for a in sys.argv if a.startswith("N=")), 200))
    nj = int(sys.argv[sys.argv.index("-j") + 1]) if "-j" in sys.argv else 4
    print(f"MC {CORNER} VDD={VDD} T={TEMP} N={N} workers={nj}")
    summ = []
    if what == "validate":
        validate()
        sys.exit(0)
    if what in ("dcnet", "all"):
        summ += mc_dcnet(N, nj)
    if what in ("comp", "all"):
        summ += mc_comp(N, nj)
    if what in ("sys", "all"):
        summ += mc_sys(N, nj)
    path = os.path.join(RES, "mc_summary.csv")
    old = list(csv.DictReader(open(path))) if os.path.exists(path) else []
    keys = {(s["campaign"], s["metric"]) for s in summ}
    allr = [o for o in old if (o["campaign"], o["metric"]) not in keys] + summ
    if allr:
        save(allr, path)
    for s in summ:
        print(f"  [{s['status']:3s}] {s['campaign']} {s['metric']} = {s['value']} {s['unit']}  (spec {s['spec']})")
