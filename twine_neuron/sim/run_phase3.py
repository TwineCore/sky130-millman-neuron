#!/usr/bin/env python3
"""Phase 3 — corners PVT + R (pré-layout). S'exécute DANS le conteneur :

    cd /foss/designs/twine_neuron && python3 sim/run_phase3.py [grid|rcorners|all] [-j 4]

Pour chaque point (lib, VDD, T) : run_phase2.py dccrit settle func power, avec
TN_SETTLE_SUBSET = 1,2,3 (S = 7.5 / 14.5 / 19.5, les plus lentes à tt) et des sorties
dans results/corners/<tag>_*.csv. Reprise : un point dont le fichier de métriques existe est sauté.
Agrégation : results/corners_pre.csv (une ligne par point) + results/corners_pre_worst.csv.
"""
import csv
import itertools
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
CDIR = os.path.join(RES, "corners")
os.makedirs(CDIR, exist_ok=True)
TESTS = ["dccrit", "settle", "power"]            # tous les points
FUNC_TESTS = ["func"]                            # points extrêmes seulement (transitoire horlogé, coûteux)
TAGP = os.environ.get("TN_CTAG", "c")             # préfixe (c = pré-layout, p = post-layout en phase 6)
NETLIST = os.environ.get("TN_NETLIST", "")

MOS = ["tt", "ff", "ss", "sf", "fs"]
VDDS = [1.62, 1.8, 1.98]
TEMPS = [-40, 27, 125]


def lib_name(mos, r):
    """Section de sky130.lib.spice : MOS + corner R/C (hh = R et C hauts, ll = bas)."""
    if r == "typ":
        return mos
    return r if mos == "tt" else f"{mos}_{r}"


def grid():
    return [(m, "typ", v, t) for m, v, t in itertools.product(MOS, VDDS, TEMPS)]


def rcorners():
    # R/C extrêmes : hh (τ max) à VDD bas, ll (P max, LSB/CM) à VDD haut, MOS tt/ss/ff, T extrêmes
    return ([(m, "hh", 1.62, t) for m in ("tt", "ss", "ff") for t in (-40, 125)] +
            [(m, "ll", 1.98, t) for m in ("tt", "ss", "ff") for t in (-40, 125)])


def funcpoints():
    # transitoire fonctionnel (décisions réelles à 10 MHz) aux coins extrêmes
    return [("ss", "typ", 1.62, -40), ("ss", "typ", 1.62, 125), ("ff", "typ", 1.98, -40), ("ff", "typ", 1.98, 125),
            ("sf", "typ", 1.62, -40), ("fs", "typ", 1.62, -40), ("ss", "hh", 1.62, -40), ("ff", "ll", 1.98, 125)]


def postpoints():
    # post-layout (PEX) : tt nominal + coins extrêmes en vitesse (ss/hh/1.62/−40), mode commun/LSB et P (ff/ll/1.98)
    return [("tt", "typ", 1.8, 27), ("ss", "hh", 1.62, -40), ("ss", "typ", 1.62, 125), ("ff", "typ", 1.98, -40),
            ("ff", "ll", 1.98, 125)]


def tag(p):
    m, r, v, t = p
    return f"{TAGP}_{m}_{r}_{v:.2f}_{t:+d}".replace("-", "m").replace("+", "p")


def run_point(p, tests=None):
    tests = tests or TESTS
    m, r, v, t = p
    tg = tag(p)
    mfile = os.path.join(CDIR, f"{tg}_metrics_{'_'.join(tests)}.csv")
    if os.path.exists(mfile):
        return tg, 0.0, "skip"
    env = dict(os.environ, TN_CORNER=lib_name(m, r), TN_VDD=str(v), TN_TEMP=str(t), TN_TAG=tg,
               TN_RESDIR=CDIR, TN_SETTLE_SUBSET="1,2,3")
    if NETLIST:
        env["TN_NETLIST"] = NETLIST
    t0 = time.time()
    r_ = subprocess.run([sys.executable, "-u", os.path.join(ROOT, "sim", "run_phase2.py")] + tests,
                        capture_output=True, text=True, env=env, cwd=ROOT)
    with open(os.path.join(CDIR, f"{tg}_{'_'.join(tests)}.txt"), "w") as f:
        f.write(r_.stdout + r_.stderr)
    return tg, time.time() - t0, "ok" if r_.returncode == 0 else f"ERREUR {r_.returncode}"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return x


def aggregate(points):
    rows = []
    for p in points:
        tg = tag(p)
        mfile = os.path.join(CDIR, f"{tg}_metrics_{'_'.join(TESTS)}.csv")
        if not os.path.exists(mfile):
            continue
        met = {r["test"]: r for r in csv.DictReader(open(mfile))}
        ffile = os.path.join(CDIR, f"{tg}_metrics_{'_'.join(FUNC_TESTS)}.csv")
        if os.path.exists(ffile):
            met.update({r["test"]: r for r in csv.DictReader(open(ffile))})

        def g(prefix):
            for k, r in met.items():
                if k.startswith(prefix):
                    return num(r["value"]), r["status"]
            return float("nan"), "?"
        m, rc, v, t = p
        row = dict(mos=m, rc=rc, lib=lib_name(m, rc), vdd=v, temp=t)
        for key, prefix in (("dc_sign_err", "DC critiques : erreurs"), ("dv_half_min_mV", "|ΔV| min"),
                            ("dc_err_max_LSB", "erreur ΔV max"), ("vcm_min_V", "mode commun min"),
                            ("t_settle_ns", "t_settle 0.5 LSB"), ("t_settle_budget", "t_settle vs budget"),
                            ("func_err", "ET/OU/NON-ET"),
                            ("kick_flips", "inversions de signe"), ("kick_rel_pct", "kickback / ΔV"),
                            ("P_func_uW", "puissance moyenne"), ("P_worst_uW", "P statique pire code")):
            row[key], st = g(prefix)
        bad = [k for k, r in met.items() if r["status"] != "OK"]
        row["status"] = "OK" if not bad else "NON: " + "; ".join(bad)
        rows.append(row)
    return rows


def write(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    nj = int(sys.argv[sys.argv.index("-j") + 1]) if "-j" in sys.argv else 4
    jobs = [(p, TESTS) for p in (grid() if what in ("grid", "all") else []) + (rcorners() if what in ("rcorners", "all") else [])]
    if what == "post":
        jobs = [(p, TESTS) for p in postpoints()]
    jobs += [(p, FUNC_TESTS) for p in (funcpoints() if what in ("func", "all") else [])]
    # les transitoires horlogés (longs) d'abord pour équilibrer la fin
    jobs.sort(key=lambda j: j[1] != FUNC_TESTS)
    print(f"{len(jobs)} jobs, {nj} en parallèle", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(nj) as ex:
        for tg, dt, st in ex.map(lambda j: run_point(*j), jobs):
            print(f"  {tg:28s} {st:8s} {dt:6.0f} s   (t = {time.time()-t0:.0f} s)", flush=True)
    allp = postpoints() if what == "post" else grid() + rcorners()
    rows = aggregate(allp)
    if rows:
        write(rows, os.path.join(RES, f"corners_{'pre' if TAGP == 'c' else 'post'}.csv"))
        worst = []
        for key, fn in (("dc_sign_err", max), ("dv_half_min_mV", min), ("dc_err_max_LSB", max), ("vcm_min_V", min),
                        ("t_settle_ns", max), ("func_err", max), ("kick_flips", max), ("P_func_uW", max),
                        ("P_worst_uW", max)):
            vals = [r for r in rows if isinstance(r[key], float) and r[key] == r[key]]
            if vals:
                r = fn(vals, key=lambda z: z[key])
                worst.append(dict(metric=key, worst=r[key], lib=r["lib"], vdd=r["vdd"], temp=r["temp"]))
        write(worst, os.path.join(RES, f"corners_{'pre' if TAGP == 'c' else 'post'}_worst.csv"))
        for w in worst:
            print(f"  pire {w['metric']:16s} = {w['worst']}  ({w['lib']}, {w['vdd']} V, {w['temp']} °C)")
        bad = [r for r in rows if r["status"] != "OK"]
        print(f"{len(rows)} points agrégés, {len(bad)} avec au moins une métrique NON")
