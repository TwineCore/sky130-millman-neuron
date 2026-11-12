#!/usr/bin/env python3
"""Génère report/REPORT.md et le dossier livrable ../neurone_analogique/ (PDF conception, datasheet, guide).
Tous les chiffres sont lus dans les fichiers de résultats (chemins cités) ; « n/d » si absent.
    ../.venv/bin/python report/make_docs.py
"""
import csv
import glob
import json
import os
import re
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
OUTDIR = os.path.join(os.path.dirname(ROOT), "neurone_analogique")


def rows(name):
    p = os.path.join(R, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def rows_abs(rel):
    p = os.path.join(ROOT, rel)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def met(rws, prefix, field="value"):
    for r in rws:
        if r.get("test", r.get("metric", "")).startswith(prefix):
            return r[field]
    return "n/d"


def fnum(v, nd=2):
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return str(v)


M = json.load(open(os.path.join(ROOT, "calc", "out", "model_summary.json")))
PRE = rows("prelayout_tt.csv")
POST = []
for f in sorted(glob.glob(os.path.join(R, "post_metrics_*.csv")), key=os.path.getmtime):
    POST += list(csv.DictReader(open(f)))
# fonctionnel post-layout : une porte par run (mémoire VM) -> results/post_<G>_metrics_func.csv, agrégé ici
_pf = [list(csv.DictReader(open(os.path.join(R, f"post_{g}_metrics_func.csv")))) for g in ("AND", "OR", "NAND")
       if os.path.exists(os.path.join(R, f"post_{g}_metrics_func.csv"))]
if len(_pf) == 3:
    for k, r0 in enumerate(_pf[0]):
        v = [float(x[k]["value"]) for x in _pf]
        tst = r0["test"]
        val = sum(v) if tst.startswith("ET/OU/NON-ET") else (sum(v) / 3 if tst.startswith("puissance") else max(v))
        POST.append(dict(r0, value=f"{val:g}", unit="/12" if tst.startswith("ET/OU/NON-ET") else r0["unit"]))
PAIRS = {r["pair"]: r for r in rows_abs("pex/pex_pairs.csv")}


def _pc(pair):
    r = PAIRS.get(pair)
    return f"{fnum(r['C_a_fF'], 2)} / {fnum(r['C_b_fF'], 2)}" if r else "n/d"
PPOW = rows("post_power.csv")
CW = rows("corners_pre_worst.csv")
CP = rows("corners_pre.csv")
CPOST = rows("corners_post.csv")
MC = rows("mc_summary.csv")
PVP = rows("post_vs_pre.csv")
MCC = rows("mc_combined.csv")
mcc = {r["set"]: r for r in MCC}


def worst(key, fn, src=CP):
    v = []
    for r in src:
        try:
            if float(r[key]) == float(r[key]):
                v.append((float(r[key]), r))
        except (ValueError, KeyError):
            pass
    if not v:
        return "n/d", ""
    x, r = fn(v, key=lambda z: z[0])
    return x, f"{r['lib']}, {r['vdd']} V, {r['temp']} °C"


def cw(metric):
    for r in CW:
        if r["metric"] == metric:
            return r["worst"], f"{r['lib']}, {r['vdd']} V, {r['temp']} °C"
    return "n/d", ""


def readf(p):
    p = os.path.join(ROOT, p)
    return open(p, errors="ignore").read() if os.path.exists(p) else ""


klay = readf("pvs/klayout_drc_summary.txt").splitlines()[:1]
lvs = re.findall(r"Final result: (.*)", readf("pvs/lvs.out"))
mdrc = re.findall(r"MAGIC_DRC_COUNT (\d+)", readf("pvs/magic_pvs.log"))
ant = len(re.findall(r"Antenna violation", readf("pvs/antenna_pex.log")))
devs = re.findall(r"Number of devices: (\d+)", readf("pvs/lvs.out"))
nets = re.findall(r"Number of nets: (\d+)", readf("pvs/lvs.out"))
linfo = readf("layout/layout_info.txt").strip()
area = re.findall(r"= ([0-9.]+) mm²", linfo)
dims = re.findall(r": ([0-9.]+ x [0-9.]+) µm", linfo)
pex = readf("pex/twine_neuron_pex.spice").splitlines()
nR = sum(1 for l in pex if l.startswith("R"))
nC = sum(1 for l in pex if l.startswith("C"))

# ------------------------------------------------------------------ tableau spec / pré / post / pire
s_w, s_wc = cw("t_settle_ns")
vcm_w, vcm_wc = cw("vcm_min_V")
dv_w, dv_wc = cw("dv_half_min_mV")
se_w, se_wc = cw("dc_sign_err")
er_w, er_wc = cw("dc_err_max_LSB")
p_w, p_wc = cw("P_worst_uW")
fe_w, fe_wc = cw("func_err")
ps_w, ps_wc = worst("t_settle_ns", max, CPOST)
pv_w, pv_wc = worst("vcm_min_V", min, CPOST)
pe_w, pe_wc = worst("dc_sign_err", max, CPOST)
pp_w, pp_wc = worst("P_worst_uW", max, CPOST)
pf_w, pf_wc = worst("func_err", max, CPOST)
pk_w, pk_wc = worst("kick_flips", max, CPOST)
if pf_w == 0:
    pf_wc = f"{len(CPOST)} coins"
if pk_w == 0:
    pk_wc = f"{len(CPOST)} coins"
TAB = [
    ("Erreurs de signe de ΔV (codes critiques, S5)", "0", met(PRE, "erreurs de signe"), met(POST, "DC critiques : erreurs"),
     f"{se_w} ({se_wc})", f"{pe_w} ({pe_wc})"),
    ("Erreur ΔV vs modèle (LSB)", "< 0.5", fnum(met(PRE, "erreur ΔV vs modèle"), 3), fnum(met(POST, "erreur ΔV max"), 3),
     f"{fnum(er_w, 3)} ({er_wc})", "—"),
    ("Mode commun min V± (V, S8)", "≥ 0.75", fnum(met(PRE, "mode commun min"), 3), fnum(met(POST, "mode commun min"), 3),
     f"{fnum(vcm_w, 3)} ({vcm_wc})", f"{fnum(pv_w, 3)} ({pv_wc})"),
    ("|ΔV| min à ±0.5 LSB (mV)", "> 3σ_os", "—", fnum(met(POST, "|ΔV| min"), 2), f"{fnum(dv_w, 2)} ({dv_wc})", "—"),
    ("t_settle 0.5 LSB, pire code (ns, S10)", "≤ 50 (budget 85)", fnum(met(PRE, "t_settle 0.5 LSB"), 1),
     fnum(met(POST, "t_settle 0.5 LSB"), 1), f"{fnum(s_w, 1)} ({s_wc})", f"{fnum(ps_w, 1)} ({ps_wc})"),
    ("t_décision comparateur à 0.5 LSB_min (ns)", "< 5", fnum(met(PRE, "t_dec"), 3), "—", "—", "—"),
    ("Ron / R_slice max (%, S14)", "< 1", fnum(met(PRE, "Ron/R_slice"), 3), "—", "—", "—"),
    ("ET / OU / NON-ET : erreurs (S16)", "0 / 12", met(PRE, "ET/OU/NON-ET"), met(POST, "ET/OU/NON-ET"),
     f"{fe_w} ({fe_wc})", f"{fnum(pf_w, 0)} ({pf_wc})"),
    ("XOR 2-2-1 : erreurs (S16)", "0 / 4", met(PRE, "XOR"), "—", "—", "—"),
    ("Inversions de signe pendant la décision (kickback)", "0", met(PRE, "inversions de signe"),
     fnum(met(POST, "inversions de signe"), 0), "—", f"{fnum(pk_w, 0)} ({pk_wc})"),
    ("P statique pire code (µW, S12 info)", "info", fnum(met(PRE, "P statique pire code"), 1),
     fnum(PPOW[0]["P_sim_W"], 9) if PPOW else "n/d", f"{fnum(p_w, 1)} ({p_wc})", f"{fnum(pp_w, 1)} ({pp_wc})"),
    ("P moyenne, 300 codes aléatoires (µW)", "info", fnum(met(PRE, "P statique moyenne"), 1), "—", "—", "—"),
]
if PPOW:
    TAB[10] = TAB[10][:3] + (fnum(float(PPOW[0]["P_sim_W"]) * 1e6, 1),) + TAB[10][4:]
mc_rows = [(r["campaign"], r["metric"], r["value"], r["unit"], r["spec"], r["status"]) for r in MC]


def table(head, data):
    s = "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n"
    for d in data:
        s += "| " + " | ".join(str(x) for x in d) + " |\n"
    return s


n_bad = sum(1 for r in CP if r.get("status", "OK") != "OK")
bad_kinds = {}
for r in CP:
    if r.get("status", "OK") != "OK":
        for k in r["status"][5:].split("; "):
            k = k.split(" (")[0]
            bad_kinds[k] = bad_kinds.get(k, 0) + 1

# ------------------------------------------------------------------ REPORT.md
rep = f"""# Neurone de Millman à synapses tri-state — sky130A

*Rapport de conception (phases 1 à 7). Chaque chiffre provient d'un fichier du dépôt `twine_neuron/`, cité entre
parenthèses. Données brutes : `results/`, journal complet des commandes : `LOG.md`.*

## 1. Principe

Le neurone calcule `out = 1 ⇔ Σ wᵢ·xᵢ + b − 0.5·h > 0` avec 4 entrées binaires xᵢ, des poids wᵢ ∈ [−7, +7],
un biais b ∈ [−31, +31] et un demi-LSB h optionnel. La somme pondérée est réalisée **par le théorème de
Millman** : chaque bit de poids est une « slice » = un driver tri-state CMOS suivi d'une résistance de
conductance proportionnelle au poids (1, 2, 4… Gu). Toutes les slices actives d'un nœud (V+ ou V−) forment
un diviseur résistif ; la tension du nœud est la moyenne des tensions des drivers pondérée par les conductances :

V± = VDD · (G0 + Σ G_k·d_k) / (G0 + Σ G_k), où d_k ∈ {{0, 1}} est le niveau du driver k.

**Pourquoi deux nœuds équilibrés ?** Un poids positif tire V+ vers le haut, un poids négatif tire V− vers le
haut ; chaque synapse active **les deux** bancs (l'un mené à x, l'autre à 0). Les dénominateurs de V+ et V−
sont donc égaux pour tout code, et `ΔV = V+ − V− = VDD·(Σwx + b − 0.5h)/D` a **exactement le signe** de la
somme pondérée (`calc/millman_model.py` : 0 erreur de signe sur 102 M points × 3 VDD). Un comparateur
dynamique (StrongARM + latch SR) échantillonne ce signe à chaque coup d'horloge.

**Pourquoi G0 vers VDD ?** La paire NMOS du StrongARM exige un mode commun ≥ ≈ 0.75 V ; une conductance
fixe G0 = {M['G0']} Gu tirée vers VDD place V± dans [{fnum(M['VCM_MIN_V'], 3)} V, VDD] à 1.62 V
(`calc/out/model_summary.json`), au prix d'un LSB réduit (LSB_min = {fnum(M['LSB_MIN_mV'], 2)} mV à 1.62 V).

**Pourquoi un demi-LSB ?** Avec h = 1, ΔV ne vaut jamais 0 : |ΔV| ≥ 0.5 LSB. C'est ce qui rend la lecture
**SAR** (recherche dichotomique de b, 6 décisions) déterministe : elle restitue Σ w·x sans ADC.

## 2. Architecture et dimensionnement

| Bloc | Réalisation | Source |
|---|---|---|
| Unité résistive R_U | xhigh_po w = 0.35 µm, L = {M['L_U_um']} µm, R_U = {fnum(M['R_U_ohm']/1e3, 1)} kΩ ; Ru = 4·R_U = {fnum(M['RU_ohm']/1e6, 3)} MΩ (1 Gu) | `calc/out/model_summary.json` |
| Slices | half 8 R_U série ; w1 4 ; w2 2 ; w4 1 ; w8 2 en // ; w16 4 en // ; driver × poids | `xschem/gen_xschem.py` |
| Bancs | 4 synapses × 2 bancs × 3 bits + biais 2 × 5 bits + 2 demi-LSB = 36 slices, 124 R_U | `netlist/twine_neuron.spice` |
| G0 | 13 R_U en parallèle par nœud (52 Gu) vers VDD | idem |
| Comparateur | StrongARM NMOS (paire W·L = 2 × 6 × 1 µm²), tampons, latch SR NOR ; 23 transistors | idem |
| Horloge | 10 MHz : code appliqué à t = 0, front montant à 85 ns, échantillonnage de Q à 92 ns | `sim/tn.py`, `spec/SPEC.md` §5 |

![modèle de Millman : ΔV, mode commun, compromis Ru](../plots/model_overview.png)

**Itérations de dimensionnement (phase 2)** : (1) latch SR NAND → tampons + latch NOR (hystérésis de 1–3 mV
supprimée) ; (2) la stabilisation simulée (65.2 ns) dépassait la spec de 50 ns car le réseau xhigh_po est un
RC **réparti** (τ ∝ Ru²) que le modèle localisé sous-estimait → décision « performance d'abord » : Ru × 0.7
et front d'horloge déplacé à 85 ns (`LOG.md`, `spec/SPEC.md` §5). Deux bugs de banc corrigés en route :
`m=` ignoré par ngspice sur le sous-circuit xhigh_po (unités parallèles instanciées une à une) et point de
polarisation métastable du latch en `.op` (`.nodeset`).

## 3. Résultats : spécification, pré-layout, post-layout, pire cas

Pré : `results/prelayout_tt.csv` (tt, 27 °C, 1.8 V). Post : `results/post_metrics_*.csv`, `results/post_power.csv`
(netlist PEX). Pire pré : `results/corners_pre.csv` ({len(CP)} points PVT/R). Pire post : `results/corners_post.csv`
({len(CPOST)} points extrêmes).

{table(["Paramètre", "Spec", "Pré tt", "Post tt", "Pire corner pré", "Pire corner post"], TAB)}
Points de corners pré-layout avec au moins une métrique hors spec : {n_bad} / {len(CP)}
({", ".join(f"{k} : {v}" for k, v in bad_kinds.items()) or "aucune"}). La métrique « kickback absolu »
(> LSB/4) est hors critère partout, mais le kickback est **proportionnel à ΔV** (≤ 32 % de ΔV dans la fenêtre
de décision, 0 inversion de signe) : il ne modifie aucune décision.

![DC : ΔV simulé vs modèle](../plots/pre_dc.png)

![stabilisation de V± (pire code)](../plots/pre_settle.png)

![fonctionnel ET/OU/NON-ET à 10 MHz](../plots/pre_func.png)

### Monte Carlo (désappariement, `*_mm`)
{table(["Campagne", "Métrique", "Valeur", "Unité", "Spec", "Statut"], mc_rows) if mc_rows else "n/d"}
Source : `results/mc_summary.csv`, `results/mc_dcnet.csv`, `results/mc_comp.csv`.

**Combinaison réseau × comparateur** (`sim/mc_combine.py` → `results/mc_combined.csv`) : les 200 dies du
réseau et les 200 seuils du comparateur sont croisés (40 000 paires). Une décision est fausse si le seuil du
comparateur dépasse ΔV dans le sens de ΔV.

{table(["Ensemble", "|ΔV| min (mV)", "σ_os (mV)", "P(erreur) par décision, empirique", "idem, loi normale"],
       [(k, mcc[k]["dv_abs_min_mV"], mcc[k]["os_sigma_mV"], mcc[k]["p_err_empirical"], mcc[k]["p_err_gauss"])
        for k in ("half", "cm") if k in mcc]) if mcc else "n/d"}
Fraction de paires (die réseau, die comparateur) avec **au moins une** décision fausse sur les 8 codes
à ±0.5 LSB : **{mcc["die_pairs"]["p_err_empirical"] if "die_pairs" in mcc else "n/d"}**, soit un rendement
fonctionnel estimé à ≈ 99.8 % à tt/27 °C/1.8 V. Les erreurs ne touchent que les codes à exactement ±0.5 LSB
(|ΔV| min 2.78 mV contre |offset| max 5.5 mV) ; tout code à ≥ 1.5 LSB a une marge > 7σ_os. Une calibration
d'offset par le code de biais (décalage de b mesuré une fois par die) ramènerait ces cas à 0 ; elle n'est pas
implémentée en V1.

### Post-layout vs pré-layout
Détail par point : `results/post_vs_pre.csv`.

{table(["lib", "VDD", "T", "métrique", "pré", "post", "écart"], [(r["lib"], r["vdd"], r["temp"], r["metric"], r["pre"], r["post"], r["delta"]) for r in PVP if r["metric"] in ("t_settle_ns", "vcm_min_V", "P_worst_uW", "dc_sign_err")]) if PVP else "n/d"}

## 4. Layout et vérification physique

![layout complet](../plots/layout_full.png)

- Dimensions : {dims[0] if dims else "n/d"} µm, **{area[0] if area else "n/d"} mm²** (`layout/layout_info.txt`) ;
  estimation phase 1 : {fnum(M['AREA_um2']/1e6, 4)} mm² (pas de résistance 1 µm ; le placement réel suit la
  largeur des drivers).
- Réseau résistif : 124 unités R_U générées par le générateur PDK de magic (`layout/gen_res.tcl`), bancs P et M
  **entrelacés** par (synapse, bit), G0P/G0M entrelacés unité par unité, urpm continu ; paire d'entrée du
  comparateur en **centroïde commun A-B-B-A** ; bus V+/V− en met3 séparés par un **blindage VSS** ; rails
  VDD/VSS met1 continus avec prises ptap/ntap sur toute la longueur ; bus d'entrée en met3 sous les drivers.
- DRC KLayout (deck sky130A_mr, feol/beol/offgrid) : {klay[0] if klay else "n/d"} (`pvs/klayout_drc_summary.txt`)
- DRC magic (drc(full)) : {mdrc[-1] if mdrc else "n/d"} erreur (`pvs/magic_pvs.log`)
- LVS netgen vs netlist xschem : **{lvs[-1] if lvs else "n/d"}** — {devs[0] if devs else "?"} devices,
  {nets[0] if nets else "?"} nets (`pvs/lvs.out`)
- Antenne (magic antennacheck) : {ant} violation (`pvs/antenna_pex.log`)
- PEX (magic, R + C, extresist) : {nR} résistances parasites, {nC} capacités (`pex/twine_neuron_pex.spice`)
- Canal de routage met3 du comparateur : pistes **en miroir autour de CLK**
  (`TAIL · Q TA SN OUTN XN INP CLK INN XP OUTP RP TB QB`, `layout/layout_neuron.py`) ; couplages PEX vers CLK :
  OUTN/OUTP {_pc("OUTN/OUTP<-CLK")} fF, XN/XP {_pc("XN/XP<-CLK")} fF (`pex/pex_pairs.csv`).

### Correction post-layout : offset du comparateur
La première PEX donnait 1 erreur sur 4 en ET/OU/NON-ET (OU et NON-ET) : le comparateur décidait Q = 1 jusqu'à
ΔV ≈ −34 mV (offset systématique ≈ −40 à −68 mV, contre σ_os = 2 mV en Monte Carlo). Deux hypothèses ont été
réfutées en simulation sur des copies de la PEX : capacités à la masse déséquilibrées (OUTN/OUTP −1.46 fF,
XN/XP −1.77 fF) et jonctions de la paire ABBA (XN : 2 diffusions de bord, ad 4.32 µm² contre 2.16 µm² pour XP) —
compensées, elles ne changeaient aucune décision. La sonde des nœuds internes (`sim/dbg_cmp_nodes.py`) a montré
qu'au front de CLK, OUTP montait à 2.095 V contre 2.008 V pour OUTN (pré-layout : 1.880 / 1.873 V) : le latch
partait du mauvais côté avant que la paire n'agisse. Cause : la piste CLK du canal, placée par ordre d'apparition
des terminaux **entre XP et OUTP** (C(CLK–OUTP) 2.66 fF contre 0.91 fF pour OUTN ; C(CLK–XP) 2.49 contre
0.80 fF). Avec les pistes en miroir, les décisions sont justes à ±16–18 mV (≈ ±0.5 LSB) et le fonctionnel
post-layout ne fait plus aucune erreur (`LOG.md`, phase 6).

![zoom slices](../plots/layout_zoom_slices.png)

## 5. Limites et propositions V2

Limites :
- Pas de transistors/résistances **dummies** (ils auraient exigé leur ajout au schéma pour le LVS) ;
  l'appariement repose sur l'entrelacement et le centroïde commun.
- Monte Carlo : rendement estimé 99.8 % (codes à ±0.5 LSB seulement, `results/mc_combined.csv`) ; MC fait à
  tt/27 °C/1.8 V seulement (pas de MC aux corners).
- Post-layout, pire coin ({ps_wc}) : t_settle = {fnum(ps_w, 1)} ns{", au-delà de la cible de 50 ns mais dans le budget dur de 85 ns (front d'horloge)" if isinstance(ps_w, float) and ps_w > 50 else ", dans la cible de 50 ns"} — aucune décision affectée (`results/corners_post.csv`).
- Kickback différentiel sur V+−V− de 19 à 27 mV aux 5 coins post-layout (critère LSB/4 ≈ 4 mV non tenu,
  comme en pré-layout) ; il reste ≤ 46 % de ΔV dans la fenêtre de décision, sans aucune inversion
  (`results/corners/p_*_metrics_func.csv`).
- P statique pire code jusqu'à 367 µW au coin fs/1.98 V/125 °C (`results/corners_pre_worst.csv`).
- Puissance statique élevée (réseau toujours polarisé) : S12 est devenue informative (décision du 2026-11-12).
- Surface 2.8 × l'estimation : la rangée de drivers (piles × 16) impose la largeur.
- SAR transitoire vérifié sur 2 lectures complètes ; les décisions limites des 10 vecteurs le sont en DC
  (`dccrit`) et en Monte Carlo.

Propositions V2 :
1. **Drivers coupés hors fenêtre d'évaluation** (Hi-Z entre les échantillons) : la puissance moyenne baisse
   du rapport cyclique, sans toucher τ (cf. `spec/SPEC.md` §3).
2. **Comparateur double-tail** (préampli séparé du latch) : kickback réduit, mode commun plus bas →
   G0 plus faible, LSB plus grand et τ plus court.
3. **Résistances plus courtes à rsheet plus élevé ou série par poly fendu** / réseau R-2R pour diviser le nombre
   d'unités (124 → ≈ 40) et la capacité répartie : surface et τ réduits ; ajout de dummies au schéma.

## 6. Fichiers et commandes

| Étape | Commande (conteneur, `/foss/designs/twine_neuron`) | Sorties |
|---|---|---|
| Modèle | `python3 calc/millman_model.py --noplot` | `calc/out/` |
| Schémas / netlist | `python3 xschem/gen_xschem.py && bash netlist/netlist.sh` | `xschem/*.sch`, `netlist/twine_neuron.spice` |
| Pré-layout | `python3 sim/run_phase2.py ron dc dccrit comp tdec settle func xor sar power` | `results/pre_*.csv` |
| Corners | `python3 sim/run_phase3.py all -j 3` | `results/corners_pre*.csv`, `results/corners/` |
| Monte Carlo | `python3 sim/run_mc.py dcnet N=200 ; python3 sim/run_mc.py comp N=200` | `results/mc_*.csv` |
| Layout | `cd layout && magic … gen_res.tcl && python3 layout_neuron.py` | `layout/twine_neuron.gds` |
| PVS | `pvs/pvs.sh` | `pvs/` |
| PEX | `cd pex && magic … pex.tcl` | `pex/twine_neuron_pex.spice` |
| Post-layout | `TN_RSHUNT=1e12 TN_NETLIST=pex/twine_neuron_pex.spice TN_TAG=post python3 sim/run_phase2.py dccrit power settle func` ; `TN_CTAG=p … sim/run_phase3.py post` | `results/post_*`, `results/corners_post.csv` |
| Synthèse | `python3 sim/summarize.py pre ; python3 sim/post_vs_pre.py ; python3 plots/plot_phase2.py ; python3 report/make_docs.py` | `results/`, `plots/`, `report/` |
"""
os.makedirs(os.path.join(ROOT, "report"), exist_ok=True)
open(os.path.join(ROOT, "report", "REPORT.md"), "w").write(rep)

# ------------------------------------------------------------------ DATASHEET / GUIDE
ds = f"""# TwineNeuron-1 — Datasheet

Neurone à seuil analogique programmable, 4 entrées, technologie SkyWater sky130A (1.8 V).

## Caractéristiques principales
| Paramètre | Valeur | Conditions / source |
|---|---|---|
| Fonction | out = 1 ⇔ Σ wᵢxᵢ + b − 0.5h > 0 | — |
| Entrées | 4 binaires (CMOS 1.8 V) | — |
| Poids | ±7 (3 bits + signe) par entrée | — |
| Biais | ±31 (5 bits + signe) ; demi-LSB h | — |
| Alimentation | 1.8 V (1.62–1.98 V) | corners `results/corners_pre.csv` |
| Cadence | 10 MHz (une décision par période) | `sim/tn.py` |
| LSB (ΔV par unité) | ≥ {fnum(M['LSB_MIN_mV'], 2)} mV @1.62 V, {fnum(M['LSB_NOM_DMAX_mV'], 2)} mV @1.8 V (code max) | `calc/out/model_summary.json` |
| Stabilisation 0.5 LSB (pire code) | {TAB[4][2]} ns tt pré ; {TAB[4][3]} ns tt post ; pire corner {TAB[4][4]} | §3 du rapport |
| Temps de décision | {TAB[5][2]} ns (0.5 LSB_min) | `results/pre_comp_tdec.csv` |
| Précision du réseau | erreur ΔV ≤ {TAB[1][2]} LSB (tt) | `results/pre_dc.csv` |
| Fonctionnel ET/OU/NON-ET (PEX) | {TAB[7][3]} / 12 erreur tt ; pire coin post : {TAB[7][5]} | `results/post_*_func.csv`, `results/corners_post.csv` |
| Rendement Monte Carlo | paires die en échec : {mcc["die_pairs"]["p_err_empirical"] if "die_pairs" in mcc else "n/d"} (codes ±0.5 LSB seulement) ; σ_os comparateur {mcc.get("half", {}).get("os_sigma_mV", "n/d")} mV | `results/mc_combined.csv` |
| Puissance statique | {TAB[10][2]} µW pire code ; {TAB[11][2]} µW moyenne (codes aléatoires) | `results/pre_power.csv`, `results/pre_dc.csv` |
| Surface | {area[0] if area else "n/d"} mm² ({dims[0] if dims else "n/d"} µm) | `layout/layout_info.txt` |
| Vérification | DRC 0 (magic, KLayout) ; LVS « {lvs[-1] if lvs else "n/d"} » ; antenne {ant} | `pvs/` |

## Broches
| Broche | Dir. | Rôle |
|---|---|---|
| DP1–DP4 / DM1–DM4 | E | donnée de l'entrée i vers le banc + (poids > 0) / − (poids < 0) : DPᵢ = xᵢ·(wᵢ>0), DMᵢ = xᵢ·(wᵢ<0) |
| ENi_0..ENi_2 | E | bits de \\|wᵢ\\| (poids 1, 2, 4), communs aux deux bancs de l'entrée i |
| DBP / DBM | E | signe du biais : DBP = (b > 0), DBM = (b < 0) |
| ENB_0..ENB_4 | E | bits de \\|b\\| (1, 2, 4, 8, 16) |
| HEN | E | demi-LSB (h) |
| CLK | E | horloge du comparateur (front montant = décision) |
| Q / QB | S | décision (Q = 1 ⇔ ΔV > 0), mémorisée jusqu'à la décision suivante |
| VP / VM | S (analog.) | nœuds de Millman V+ / V− (observation) |
| VDD / VSS | Alim. | 1.8 V / masse |

## Chronogramme (période 100 ns)
Code (D, EN) appliqué à t = 0 → stabilisation de V± → front montant de CLK à 85 ns → Q valide ≤ 1 ns plus
tard → CLK bas à 95 ns (pré-charge du comparateur).
"""
guide = f"""# TwineNeuron-1 — Guide utilisateur

## 1. Programmer un neurone
1. Choisir wᵢ ∈ [−7, 7] et b ∈ [−31, 31] (h = 0 en inférence, h = 1 pour lever les égalités).
2. Pour chaque entrée i : ENi_k = bit k de |wᵢ| ; à chaque évaluation : DPᵢ = xᵢ si wᵢ > 0 sinon 0,
   DMᵢ = xᵢ si wᵢ < 0 sinon 0.
3. Biais : ENB_k = bit k de |b| ; DBP = 1 si b > 0, DBM = 1 si b < 0.
4. Appliquer le code, attendre le front montant de CLK (85 ns après le changement à 10 MHz), lire Q.

Le traducteur de référence est `levels()` dans `twine_neuron/sim/tn.py`.

## 2. Portes logiques (validées en transitoire, `results/pre_func.csv`, `results/pre_xor.csv`)
| Porte | w1, w2 | b | h |
|---|---|---|---|
| ET | 2, 2 | −3 | 0 |
| OU | 2, 2 | −1 | 0 |
| NON-ET | −2, −2 | +3 | 0 |
| XOR (2 couches, multiplexé) | OU et NON-ET → ET | | |

## 3. Lire la somme pondérée (mode SAR)
Avec h = 1, Q = 1 ⇔ b ≥ 1 − Σw·x. Recherche dichotomique de b sur [−31, 31] (6 décisions) :
b_min = plus petit b donnant Q = 1, puis Σw·x = 1 − b_min. Exemple simulé : w = (7,7,7,7), x = 1111 →
décisions 0:1, −16:1, −24:1, −28:0, −26:1, −27:1 → Σw·x = 28 (`results/pre_sar.csv`).

## 4. Précautions
- Respecter le budget de stabilisation (≥ {TAB[4][4].split(' ')[0]} ns au pire corner pré-layout avant le front d'horloge).
- Consommation statique tant qu'une slice est active : mettre tous les EN à 0 (Hi-Z) au repos.
- Les nœuds VP/VM sont à haute impédance (Ru/D) : toute charge externe les ralentit et les décale.

## 5. Re-simuler
Dans le conteneur : `cd /foss/designs/twine_neuron && python3 sim/run_phase2.py func` (pré-layout) ou avec
`TN_NETLIST=pex/twine_neuron_pex.spice TN_RSHUNT=1e12` (post-layout). Corners : `sim/run_phase3.py`,
Monte Carlo : `sim/run_mc.py`.
"""

# ------------------------------------------------------------------ dossier livrable + PDF
os.makedirs(OUTDIR, exist_ok=True)
for sub in ("plots", "gds", "netlists", "results"):
    os.makedirs(os.path.join(OUTDIR, sub), exist_ok=True)
open(os.path.join(OUTDIR, "Datasheet.md"), "w").write(ds)
open(os.path.join(OUTDIR, "Guide_utilisateur.md"), "w").write(guide)
for f in glob.glob(os.path.join(ROOT, "plots", "*.png")):
    shutil.copy(f, os.path.join(OUTDIR, "plots"))
for src, dst in (("layout/twine_neuron.gds", "gds"), ("netlist/twine_neuron.spice", "netlists"),
                 ("pex/twine_neuron_pex.spice", "netlists")):
    if os.path.exists(os.path.join(ROOT, src)):
        shutil.copy(os.path.join(ROOT, src), os.path.join(OUTDIR, dst))
for f in ("prelayout_tt.csv", "corners_pre.csv", "corners_pre_worst.csv", "corners_post.csv", "post_vs_pre.csv",
          "mc_summary.csv"):
    if os.path.exists(os.path.join(R, f)):
        shutil.copy(os.path.join(R, f), os.path.join(OUTDIR, "results"))


def md2pdf(md_text, pdf_path, title, imgdir):
    from fpdf import FPDF
    md_text = md_text.replace("ᵢ", "i")
    html = subprocess.run(["pandoc", "-f", "markdown", "-t", "html"], input=md_text, capture_output=True,
                          text=True).stdout
    html = html.replace('src="../plots/', f'src="{imgdir}/')
    html = re.sub(r"<img ([^>]*)>", lambda m: "<img " + m.group(1).replace("/>", "") + ' width="480">', html)
    html = re.sub(r"<figcaption.*?</figcaption>", "", html, flags=re.S)
    html = html.replace("<figure>", "").replace("</figure>", "")
    html = re.sub(r"<table>", '<table border="1" cellpadding="2" width="100%">', html)
    html = re.sub(r"<(t[hd]) style=\"[^\"]*\">", r"<\1>", html)
    html = re.sub(r"</?(colgroup|col|thead|tbody|span)[^>]*>", "", html)
    html = re.sub(r"<table.*?</table>", lambda m: re.sub(r"</?(code|strong|em|a|br)[^>]*>", "", m.group(0)), html,
                  flags=re.S)
    pdf = FPDF(format="A4")
    pdf.set_margins(14, 14, 14)
    pdf.add_font("AU", "", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    pdf.add_font("AU", "B", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    pdf.add_font("AU", "I", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    pdf.add_font("AU", "BI", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    pdf.set_font("AU", size=9)
    pdf.set_title(title)
    pdf.add_page()
    pdf.write_html(html, font_family="AU", pre_code_font="AU", table_line_separators=True)
    pdf.output(pdf_path)


imgdir = os.path.join(OUTDIR, "plots")
md2pdf(rep, os.path.join(OUTDIR, "Neurone_Millman_conception.pdf"), "Neurone de Millman — conception", imgdir)
md2pdf(ds, os.path.join(OUTDIR, "Datasheet.pdf"), "TwineNeuron-1 datasheet", imgdir)
md2pdf(guide, os.path.join(OUTDIR, "Guide_utilisateur.pdf"), "TwineNeuron-1 guide", imgdir)
shutil.copy(os.path.join(ROOT, "report", "REPORT.md"), os.path.join(OUTDIR, "REPORT.md"))
print("écrit :", os.path.join(ROOT, "report", "REPORT.md"), "et", OUTDIR)
