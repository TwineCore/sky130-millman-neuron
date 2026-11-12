# TwineNeuron-1 — Datasheet

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
| LSB (ΔV par unité) | ≥ 14.53 mV @1.62 V, 16.14 mV @1.8 V (code max) | `calc/out/model_summary.json` |
| Stabilisation 0.5 LSB (pire code) | 34.2 ns tt pré ; 43.5 ns tt post ; pire corner 47.1 (ss_hh, 1.62 V, -40 °C) | §3 du rapport |
| Temps de décision | 0.543 ns (0.5 LSB_min) | `results/pre_comp_tdec.csv` |
| Précision du réseau | erreur ΔV ≤ 0.078 LSB (tt) | `results/pre_dc.csv` |
| Fonctionnel ET/OU/NON-ET (PEX) | 0 / 12 erreur tt ; pire coin post : 0 (5 coins) | `results/post_*_func.csv`, `results/corners_post.csv` |
| Rendement Monte Carlo | paires die en échec : 1.850e-03 (codes ±0.5 LSB seulement) ; σ_os comparateur 2.058 mV | `results/mc_combined.csv` |
| Puissance statique | 131.7 µW pire code ; 72.9 µW moyenne (codes aléatoires) | `results/pre_power.csv`, `results/pre_dc.csv` |
| Surface | 0.0411 mm² (447.5 x 91.9 µm) | `layout/layout_info.txt` |
| Vérification | DRC 0 (magic, KLayout) ; LVS « Circuits match uniquely. » ; antenne 0 | `pvs/` |

## Broches
| Broche | Dir. | Rôle |
|---|---|---|
| DP1–DP4 / DM1–DM4 | E | donnée de l'entrée i vers le banc + (poids > 0) / − (poids < 0) : DPᵢ = xᵢ·(wᵢ>0), DMᵢ = xᵢ·(wᵢ<0) |
| ENi_0..ENi_2 | E | bits de \|wᵢ\| (poids 1, 2, 4), communs aux deux bancs de l'entrée i |
| DBP / DBM | E | signe du biais : DBP = (b > 0), DBM = (b < 0) |
| ENB_0..ENB_4 | E | bits de \|b\| (1, 2, 4, 8, 16) |
| HEN | E | demi-LSB (h) |
| CLK | E | horloge du comparateur (front montant = décision) |
| Q / QB | S | décision (Q = 1 ⇔ ΔV > 0), mémorisée jusqu'à la décision suivante |
| VP / VM | S (analog.) | nœuds de Millman V+ / V− (observation) |
| VDD / VSS | Alim. | 1.8 V / masse |

## Chronogramme (période 100 ns)
Code (D, EN) appliqué à t = 0 → stabilisation de V± → front montant de CLK à 85 ns → Q valide ≤ 1 ns plus
tard → CLK bas à 95 ns (pré-charge du comparateur).
