# Neurone de Millman à synapses tri-state — sky130A

*Rapport de conception (phases 1 à 7). Chaque chiffre provient d'un fichier du dépôt `twine_neuron/`, cité entre
parenthèses. Données brutes : `results/`, journal complet des commandes : `LOG.md`.*

## 1. Principe

Le neurone calcule `out = 1 ⇔ Σ wᵢ·xᵢ + b − 0.5·h > 0` avec 4 entrées binaires xᵢ, des poids wᵢ ∈ [−7, +7],
un biais b ∈ [−31, +31] et un demi-LSB h optionnel. La somme pondérée est réalisée **par le théorème de
Millman** : chaque bit de poids est une « slice » = un driver tri-state CMOS suivi d'une résistance de
conductance proportionnelle au poids (1, 2, 4… Gu). Toutes les slices actives d'un nœud (V+ ou V−) forment
un diviseur résistif ; la tension du nœud est la moyenne des tensions des drivers pondérée par les conductances :

V± = VDD · (G0 + Σ G_k·d_k) / (G0 + Σ G_k), où d_k ∈ {0, 1} est le niveau du driver k.

**Pourquoi deux nœuds équilibrés ?** Un poids positif tire V+ vers le haut, un poids négatif tire V− vers le
haut ; chaque synapse active **les deux** bancs (l'un mené à x, l'autre à 0). Les dénominateurs de V+ et V−
sont donc égaux pour tout code, et `ΔV = V+ − V− = VDD·(Σwx + b − 0.5h)/D` a **exactement le signe** de la
somme pondérée (`calc/millman_model.py` : 0 erreur de signe sur 102 M points × 3 VDD). Un comparateur
dynamique (StrongARM + latch SR) échantillonne ce signe à chaque coup d'horloge.

**Pourquoi G0 vers VDD ?** La paire NMOS du StrongARM exige un mode commun ≥ ≈ 0.75 V ; une conductance
fixe G0 = 52 Gu tirée vers VDD place V± dans [0.756 V, VDD] à 1.62 V
(`calc/out/model_summary.json`), au prix d'un LSB réduit (LSB_min = 14.53 mV à 1.62 V).

**Pourquoi un demi-LSB ?** Avec h = 1, ΔV ne vaut jamais 0 : |ΔV| ≥ 0.5 LSB. C'est ce qui rend la lecture
**SAR** (recherche dichotomique de b, 6 décisions) déterministe : elle restitue Σ w·x sans ADC.

## 2. Architecture et dimensionnement

| Bloc | Réalisation | Source |
|---|---|---|
| Unité résistive R_U | xhigh_po w = 0.35 µm, L = 52.61 µm, R_U = 301.8 kΩ ; Ru = 4·R_U = 1.207 MΩ (1 Gu) | `calc/out/model_summary.json` |
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
(netlist PEX). Pire pré : `results/corners_pre.csv` (57 points PVT/R). Pire post : `results/corners_post.csv`
(5 points extrêmes).

| Paramètre | Spec | Pré tt | Post tt | Pire corner pré | Pire corner post |
|---|---|---|---|---|---|
| Erreurs de signe de ΔV (codes critiques, S5) | 0 | 0 | 0 | 0.0 (tt, 1.62 V, -40 °C) | 0.0 (tt, 1.8 V, 27 °C) |
| Erreur ΔV vs modèle (LSB) | < 0.5 | 0.078 | 0.100 | 0.449 (fs, 1.62 V, 125 °C) | — |
| Mode commun min V± (V, S8) | ≥ 0.75 | 0.937 | 0.842 | 0.756 (ff, 1.62 V, -40 °C) | 0.757 (ss_hh, 1.62 V, -40 °C) |
| |ΔV| min à ±0.5 LSB (mV) | > 3σ_os | — | 8.04 | 5.59 (fs, 1.62 V, 125 °C) | — |
| t_settle 0.5 LSB, pire code (ns, S10) | ≤ 50 (budget 85) | 34.2 | 43.5 | 47.1 (ss_hh, 1.62 V, -40 °C) | 58.1 (ss_hh, 1.62 V, -40 °C) |
| t_décision comparateur à 0.5 LSB_min (ns) | < 5 | 0.543 | — | — | — |
| Ron / R_slice max (%, S14) | < 1 | 0.513 | — | — | — |
| ET / OU / NON-ET : erreurs (S16) | 0 / 12 | 0 | 0 | 0.0 (ff, 1.98 V, -40 °C) | 0 (5 coins) |
| XOR 2-2-1 : erreurs (S16) | 0 / 4 | 0 | — | — | — |
| Inversions de signe pendant la décision (kickback) | 0 | 0 | 0 | — | 0 (5 coins) |
| P statique pire code (µW, S12 info) | info | 131.7 | 131.6 | 367.4 (fs, 1.98 V, 125 °C) | 274.5 (ff_ll, 1.98 V, 125 °C) |
| P moyenne, 300 codes aléatoires (µW) | info | 72.9 | — | — | — |

Points de corners pré-layout avec au moins une métrique hors spec : 8 / 57
(kickback différentiel max sur V+−V− : 8). La métrique « kickback absolu »
(> LSB/4) est hors critère partout, mais le kickback est **proportionnel à ΔV** (≤ 32 % de ΔV dans la fenêtre
de décision, 0 inversion de signe) : il ne modifie aucune décision.

![DC : ΔV simulé vs modèle](../plots/pre_dc.png)

![stabilisation de V± (pire code)](../plots/pre_settle.png)

![fonctionnel ET/OU/NON-ET à 10 MHz](../plots/pre_func.png)

### Monte Carlo (désappariement, `*_mm`)
| Campagne | Métrique | Valeur | Unité | Spec | Statut |
|---|---|---|---|---|---|
| dcnet | dies | 200 |  | >= 200 | OK |
| dcnet | σ(ΔV_sim − ΔV_modèle) réseau | 0.0867 | LSB | info | OK |
| dcnet | |ΔV_sim − ΔV_modèle| max | 0.3793 | LSB | < 0.5 LSB | OK |
| dcnet | |ΔV| min aux codes ±0.5 LSB | 2.781 | mV | info : combiné au seuil MC du comparateur dans sim/mc_combine.py | info |
| dcnet | erreurs de signe de ΔV | 0 |  | 0 | OK |
| comp | σ_os comparateur (Vcm 0.84 V) | 2.058 | mV | < LSB_min/6 = 2.42 mV | OK |
| comp | |offset| max (Vcm 0.84 V) | 5.515 | mV | info (résolution ±0.125 mV) | OK |

Source : `results/mc_summary.csv`, `results/mc_dcnet.csv`, `results/mc_comp.csv`.

**Combinaison réseau × comparateur** (`sim/mc_combine.py` → `results/mc_combined.csv`) : les 200 dies du
réseau et les 200 seuils du comparateur sont croisés (40 000 paires). Une décision est fausse si le seuil du
comparateur dépasse ΔV dans le sens de ΔV.

| Ensemble | |ΔV| min (mV) | σ_os (mV) | P(erreur) par décision, empirique | idem, loi normale |
|---|---|---|---|---|
| half | 2.781 | 2.058 | 2.313e-04 | 3.623e-04 |
| cm | 486.964 | 2.058 | 0.000e+00 | 0.000e+00 |

Fraction de paires (die réseau, die comparateur) avec **au moins une** décision fausse sur les 8 codes
à ±0.5 LSB : **1.850e-03**, soit un rendement
fonctionnel estimé à ≈ 99.8 % à tt/27 °C/1.8 V. Les erreurs ne touchent que les codes à exactement ±0.5 LSB
(|ΔV| min 2.78 mV contre |offset| max 5.5 mV) ; tout code à ≥ 1.5 LSB a une marge > 7σ_os. Une calibration
d'offset par le code de biais (décalage de b mesuré une fois par die) ramènerait ces cas à 0 ; elle n'est pas
implémentée en V1.

### Post-layout vs pré-layout
Détail par point : `results/post_vs_pre.csv`.

| lib | VDD | T | métrique | pré | post | écart |
|---|---|---|---|---|---|---|
| tt | 1.8 | 27 | dc_sign_err | 0.0 | 0.0 |  |
| tt | 1.8 | 27 | vcm_min_V | 0.8409 | 0.8415 | +0.1 % |
| tt | 1.8 | 27 | t_settle_ns | 34.22 | 43.54 | +27.2 % |
| tt | 1.8 | 27 | P_worst_uW | 131.66 | 131.56 | -0.1 % |
| ss_hh | 1.62 | -40 | dc_sign_err | 0.0 | 0.0 |  |
| ss_hh | 1.62 | -40 | vcm_min_V | 0.757 | 0.7574 | +0.1 % |
| ss_hh | 1.62 | -40 | t_settle_ns | 47.08 | 58.11 | +23.4 % |
| ss_hh | 1.62 | -40 | P_worst_uW | 88.72 | 88.67 | -0.1 % |
| ss | 1.62 | 125 | dc_sign_err | 0.0 | 0.0 |  |
| ss | 1.62 | 125 | vcm_min_V | 0.7588 | 0.7593 | +0.1 % |
| ss | 1.62 | 125 | t_settle_ns | 30.58 | 39.22 | +28.3 % |
| ss | 1.62 | 125 | P_worst_uW | 120.61 | 120.5 | -0.1 % |
| ff | 1.98 | -40 | dc_sign_err | 0.0 | 0.0 |  |
| ff | 1.98 | -40 | vcm_min_V | 0.9242 | 0.9247 | +0.1 % |
| ff | 1.98 | -40 | t_settle_ns | 37.43 | 47.08 | +25.8 % |
| ff | 1.98 | -40 | P_worst_uW | 277.22 | 270.82 | -2.3 % |
| ff_ll | 1.98 | 125 | dc_sign_err | 0.0 | 0.0 |  |
| ff_ll | 1.98 | 125 | vcm_min_V | 0.9255 | 0.9265 | +0.1 % |
| ff_ll | 1.98 | 125 | t_settle_ns | 24.93 | 32.36 | +29.8 % |
| ff_ll | 1.98 | 125 | P_worst_uW | 276.48 | 274.5 | -0.7 % |


## 4. Layout et vérification physique

![layout complet](../plots/layout_full.png)

- Dimensions : 447.5 x 91.9 µm, **0.0411 mm²** (`layout/layout_info.txt`) ;
  estimation phase 1 : 0.0112 mm² (pas de résistance 1 µm ; le placement réel suit la
  largeur des drivers).
- Réseau résistif : 124 unités R_U générées par le générateur PDK de magic (`layout/gen_res.tcl`), bancs P et M
  **entrelacés** par (synapse, bit), G0P/G0M entrelacés unité par unité, urpm continu ; paire d'entrée du
  comparateur en **centroïde commun A-B-B-A** ; bus V+/V− en met3 séparés par un **blindage VSS** ; rails
  VDD/VSS met1 continus avec prises ptap/ntap sur toute la longueur ; bus d'entrée en met3 sous les drivers.
- DRC KLayout (deck sky130A_mr, feol/beol/offgrid) : categories checked: 256  violations: 0 (`pvs/klayout_drc_summary.txt`)
- DRC magic (drc(full)) : 0 erreur (`pvs/magic_pvs.log`)
- LVS netgen vs netlist xschem : **Circuits match uniquely.** — 349 devices,
  224 nets (`pvs/lvs.out`)
- Antenne (magic antennacheck) : 0 violation (`pvs/antenna_pex.log`)
- PEX (magic, R + C, extresist) : 17697 résistances parasites, 3107 capacités (`pex/twine_neuron_pex.spice`)
- Canal de routage met3 du comparateur : pistes **en miroir autour de CLK**
  (`TAIL · Q TA SN OUTN XN INP CLK INN XP OUTP RP TB QB`, `layout/layout_neuron.py`) ; couplages PEX vers CLK :
  OUTN/OUTP 0.00 / 0.00 fF, XN/XP 1.94 / 1.66 fF (`pex/pex_pairs.csv`).

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
- Post-layout, pire coin (ss_hh, 1.62 V, -40 °C) : t_settle = 58.1 ns, au-delà de la cible de 50 ns mais dans le budget dur de 85 ns (front d'horloge) — aucune décision affectée (`results/corners_post.csv`).
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
