#!/usr/bin/env python3
"""Combinaison MC réseau × comparateur (dies indépendants, tt_mm, 1.8 V, 27 °C).
Erreur de décision si le seuil du comparateur (offset) dépasse ΔV dans le sens de ΔV :
  sign(ΔV) > 0 et os >= ΔV, ou sign(ΔV) < 0 et os <= ΔV.
Sources : results/mc_dcnet.csv (ΔV simulé par die et par code), results/mc_comp.csv (seuil par die).
Sortie : results/mc_combined.csv. P_err est estimé par produit croisé empirique (200 × 200 paires)
et par une loi normale N(μ_os, σ_os) ajustée sur mc_comp.csv."""
import csv, math, os
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
dc = list(csv.DictReader(open(f"{R}/mc_dcnet.csv")))
os_ = [float(r["threshold_mV"]) for r in csv.DictReader(open(f"{R}/mc_comp.csv"))]
mu = sum(os_) / len(os_); sd = (sum((x - mu) ** 2 for x in os_) / (len(os_) - 1)) ** 0.5
Phi = lambda z: 0.5 * (1 + math.erf(z / 2 ** 0.5))
rows = []
for st in sorted({r["set"] for r in dc}):
    dv = [float(r["dv_sim_mV"]) for r in dc if r["set"] == st]
    emp = sum((v > 0 and o >= v) or (v < 0 and o <= v) for v in dv for o in os_) / (len(dv) * len(os_))
    gau = sum((1 - Phi((v - mu) / sd)) if v > 0 else Phi((v - mu) / sd) for v in dv) / len(dv)
    rows.append(dict(set=st, n_dv=len(dv), dv_abs_min_mV=round(min(abs(v) for v in dv), 3),
                     os_mu_mV=round(mu, 3), os_sigma_mV=round(sd, 3),
                     p_err_empirical=f"{emp:.3e}", p_err_gauss=f"{gau:.3e}"))
with open(f"{R}/mc_combined.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)

# rendement par die : paire (die réseau i, die comparateur j) en échec si au moins un code ±0.5 LSB est mal décidé
from collections import defaultdict
bydie = defaultdict(list)
for r in dc:
    if r["set"] == "half":
        bydie[r["die"]].append(float(r["dv_sim_mV"]))
fail = sum(any((v > 0 and o >= v) or (v < 0 and o <= v) for v in d) for d in bydie.values() for o in os_)
npair = len(bydie) * len(os_)
print(f"paires en échec : {fail}/{npair} = {fail/npair:.3e} (rendement {1-fail/npair:.4%})")
with open(f"{R}/mc_combined.csv", "a") as f:
    f.write(f"die_pairs,{npair},,,,{fail/npair:.3e},\n")

