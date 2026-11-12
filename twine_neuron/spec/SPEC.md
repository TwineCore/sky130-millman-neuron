# SPEC — Neurone Millman à synapses tri-state (sky130A) — v1 (phase 1)

Sources des chiffres : `calc/out/model_summary.txt` / `.json` (modèle `calc/millman_model.py`),
données PDK dans `spec/PDK_DATA.md`. Colonne « Modèle » = résultat du modèle idéal + estimations,
**pas encore une simulation transistor** (phase 2).

## 1. Fonction

`out = 1  ⇔  Σᵢ wᵢ·xᵢ + b − 0.5·h > 0`, avec xᵢ ∈ {0,1} (4 entrées), wᵢ ∈ [−7, +7], b ∈ [−31, +31],
h ∈ {0,1} (slice demi-LSB, utilisée pour la lecture SAR).

## 2. Tableau des spécifications

| # | Paramètre | Cible | Justification | Vérification | Modèle (phase 1) |
|---|---|---|---|---|---|
| S1 | VDD | 1.8 V (1.62–1.98) | `nfet/pfet_01v8` | corners phase 3 | — |
| S2 | Entrées | 4 binaires | demande | fonctionnel | — |
| S3 | Poids | 3 bits + signe (±7) | demande | DC + INL/DNL | — |
| S4 | **Biais** | **5 bits + signe (±31)** ⚠ *ajusté (était 3 bits)* | le SAR lit Σw·x en balayant b : il faut \|b\| ≥ max\|Σw·x\| = 28. Avec 3 bits : **681/3000** lectures SAR fausses (`calc/out/model_summary_b3.txt`) ; 4 bits : 41/3000 (`_b4.txt`) ; 5 bits : 0/3000 | SAR phase 2 | 0/3000 erreurs |
| S5 | Équilibrage | dénominateurs V+/V− égaux pour tout code | sign(ΔV) = sign(Σw·x+b) exige D₊ = D₋ | DC tous codes | 0 erreur de signe sur 102 M points × 3 VDD |
| S6 | Demi-LSB | 1 slice 0.5 Gu, activable | supprime l'égalité ΔV = 0 en lecture SAR | SAR | marge SAR = 0.5 LSB |
| S7 | LSB (ΔV par unité de Σw·x+b) | ≥ 14 mV au pire (VDD = 1.62, D_max) | LSB = VDD/D, D = Σ\|w\|+\|b\|+0.5h+G0 | DC | **14.53 mV** (16.14 mV @1.8 V) ; jusqu’à 34.6 mV @1.8 V à S = 0 (`results/model_lsb_vs_S.csv`) |
| S8 | Mode commun V± | ⊂ fenêtre du comparateur [0.75 V, VDD] sur tous codes | StrongARM à paire NMOS (hyp. VCM_LO = 0.75 V à vérifier) | DC tous codes + corners | **[0.756, VDD]** @1.62 V ; [0.839, 1.80] @1.8 V |
| S9 | G0 | 52 Gu, tout vers VDD (13 R_U en //) | Thévenin optimal pour un comparateur NMOS ; Thévenin VDD/2 **impossible** avec StrongARM NMOS (option C) | DC | — |
| S10 | Stabilisation à 0.5 LSB | ≤ 50 ns (pire code) | évaluation à 10 MHz (≥ 50 ns de décision et de marge) | transitoire | **41.6 ns** typ ; 49.9 ns avec marge corner ×1.2 (estimé) |
| S11 | Cadence d'évaluation | 10 MHz | demande | transitoire fonctionnel | — |
| S12 | **Puissance statique** | ⚠ **conflit** : ≤ 50 µW au pire code **incompatible** avec S10 | τ ∝ Ru² (capa du poly ∝ longueur ∝ Ru), P ∝ 1/Ru. S10 ⇒ Ru ≤ 1.72 MΩ ; S12 ⇒ Ru ≥ 3.18 MΩ | DC + transitoire | Ru = 1.72 MΩ : **P_max = 92 µW** (111 µW @1.98 V), **P_moy = 51 µW** (codes uniformes) → **décision demandée** (§3) |
| S13 | Offset comparateur | σ < LSB/3 = 4.84 mV (spec) ; **cible σ < LSB/6 = 2.42 mV** | marge SAR 0.5 LSB à 3σ | rampe/dichotomie + MC | σ_os ≈ **2.40 mV** (W·L = 12 µm², A_ΔVgs = 6.4 mV·µm mesuré, ×1.3 hyp.) |
| S14 | Ron des drivers | < 1 % de la plus petite slice | plus petite slice = biais 16 = Ru/16 = 108 kΩ | DC (Ron à Vds faible) | Ron < **1.08 kΩ** |
| S15 | Erreur de poids (mismatch R) | \|INL\| < 0.5 LSB (pire die) | ne pas déplacer un seuil entier | MC 200+ | max \|INL\| = **0.12 LSB** (poids), **0.27 LSB** (biais) sur 2000 dies ; σ(R_U) = 0.675 % |
| S16 | Fonctionnel | ET, OU, NON-ET, XOR 2-2-1 : 0 erreur | démonstration du concept | transitoire + MC | 0 / 12 000 par fonction (1000 dies × 3 VDD) |
| S17 | Capa de nœud explicite | 0 (pas de MIM) | la capa répartie des résistances (≈ 470 fF estimés) absorbe le kickback ; une MIM ralentirait τ | kickback phase 2 | — |
| S18 | Surface | ≈ 0.015 mm² (estimation) | 124 unités R_U × 75.24 µm de xhigh_po (9.3 mm), 36 drivers, comparateur | layout phase 4 | 14 865 µm² (pas de résistance de 1 µm **estimé**) |

## 3. Point à trancher : puissance vs vitesse (S10 ↔ S12)

| Option | Ru | t_settle (pire, ×1.2) | P_max @1.8 V | P_moy | Conséquence |
|---|---|---|---|---|---|
| **1 (recommandée)** : spec puissance redéfinie « ≤ 50 µW en moyenne, ≤ 100 µW au pire code » | 1.72 MΩ | 49.9 ns | 92 µW | 51 µW | 10 MHz tenu ; S12 reformulée |
| 2 : puissance prioritaire | 3.18 MΩ | 145 ns (`results/model_ru_tradeoff.csv`) | 50 µW | 28 µW | évaluation ramenée à ≈ 5 MHz (145 ns + décision) |

Réduire le biais à 3 ou 4 bits **ne résout pas** le conflit : Ru_vitesse ≤ 1.51 / 1.59 MΩ contre
Ru_puissance ≥ 2.19 / 2.57 MΩ (`calc/out/model_summary_b3.txt`, `_b4.txt`), et casse le SAR.
Une 3ᵉ voie (V2) : couper les drivers (tous en Hi-Z) hors de la fenêtre d'évaluation réduit la
puissance moyenne d'un facteur égal au rapport cyclique, sans changer τ.

## 4. Hypothèses à vérifier en phase 2 (non PDK)

| Hypothèse | Valeur | Vérification |
|---|---|---|
| Bas de fenêtre du StrongARM NMOS | 0.75 V | balayage du mode commun d'entrée |
| Fraction de capa répartie vue par le nœud | 0.5 | transitoire avec modèles PDK (c1/c2 intégrés) |
| Routage par nœud | 30 fF | PEX phase 6 |
| Offset total / offset de paire | 1.3 | Monte Carlo transistor |
| Pas des résistances (surface) | 1.0 µm | layout phase 4 |
| Marge τ des corners | 1.2 | corners phase 3 |
