# sky130-millman-neuron

Neurone à seuil **analogique** programmable en technologie **SkyWater sky130A** (1.8 V), conçu de la spécification
jusqu'au layout vérifié (DRC / LVS / PEX) avec des outils open source (xschem, ngspice, magic, netgen, KLayout).

```
out = 1  ⇔  Σ wᵢ·xᵢ + b − 0.5·h > 0        4 entrées binaires, wᵢ ∈ [−7, +7], b ∈ [−31, +31]
```

La somme pondérée est faite **par le théorème de Millman** : chaque bit de poids est une « slice » (driver
tri-state CMOS + résistance de conductance 1, 2, 4… Gu). Deux nœuds équilibrés V+ / V− donnent
`ΔV = VDD·(Σwx + b − 0.5h)/D`, dont un comparateur dynamique StrongARM + latch SR échantillonne le signe à 10 MHz.

## Résultats principaux

| Paramètre | Spec | Post-layout tt | Pire coin post-layout |
|---|---|---|---|
| Erreurs de signe de ΔV (codes critiques) | 0 | 0 | 0 |
| Fonctionnel ET / OU / NON-ET | 0 / 12 | 0 | 0 (5 coins) |
| Mode commun min V± | ≥ 0.75 V | 0.842 V | 0.757 V |
| Stabilisation à 0.5 LSB | ≤ 50 ns (budget 85) | 43.5 ns | 58.1 ns (ss_hh, 1.62 V, −40 °C) |
| Puissance statique, pire code | info | 131.6 µW | 274.5 µW |
| Surface | — | 0.041 mm² (447.5 × 91.9 µm) | — |

DRC 0 (magic et KLayout), LVS « Circuits match uniquely » (349 transistors / résistances, 224 nets),
0 violation d'antenne. Monte Carlo 200 dies : σ_offset comparateur 2.06 mV, rendement estimé ≈ 99.8 %.
Détails, limites et propositions V2 : [`neurone_analogique/Neurone_Millman_conception.pdf`](neurone_analogique/Neurone_Millman_conception.pdf).

## Contenu

| Dossier | Contenu |
|---|---|
| `neurone_analogique/` | **Livrable** : PDF de conception, datasheet, guide utilisateur, GDS, netlists (schéma et PEX), figures, résultats |
| `twine_neuron/spec/` | Spécification, architecture, données PDK |
| `twine_neuron/calc/` | Modèle de Millman (dimensionnement, vérification exhaustive du signe) |
| `twine_neuron/xschem/` | Schémas xschem (générés par `gen_xschem.py`) |
| `twine_neuron/netlist/` | Netlist SPICE extraite des schémas |
| `twine_neuron/sim/` | Bancs de test et campagnes ngspice (pré/post-layout, coins PVT/RC, Monte Carlo, diagnostics) |
| `twine_neuron/layout/` | Générateur de layout (KLayout Python) et GDS |
| `twine_neuron/pvs/`, `pex/` | DRC, LVS, antenne, extraction parasite |
| `twine_neuron/results/` | Métriques CSV de toutes les campagnes |
| `twine_neuron/report/` | Génération du rapport, de la datasheet et du guide |
| `twine_neuron/LOG.md` | Journal complet : commande → résultat → décision, phase par phase |

Les données brutes de simulation (`twine_neuron/sim/out/`, ≈ 450 Mo) ne sont pas versionnées ; elles se
régénèrent avec les scripts de `twine_neuron/sim/`.

## Reproduire

Environnement : conteneur IIC-OSIC-TOOLS (PDK `sky130A` dans `/foss/pdks`), projet monté dans
`/foss/designs/twine_neuron`.

```bash
cd /foss/designs/twine_neuron
python3 sim/run_phase2.py ron dc dccrit comp tdec settle func xor sar power   # pré-layout (tt)
python3 sim/run_phase3.py all                                                   # coins PVT/RC
python3 layout/layout_neuron.py && bash pvs/pvs.sh                              # layout + DRC/LVS
cd pex && magic -dnull -noconsole -rcfile /foss/pdks/sky130A/libs.tech/magic/sky130A.magicrc pex.tcl
cd .. && bash sim/post_v3_regr.sh && bash sim/post_v3_corners.sh               # post-layout (PEX)
python3 report/make_docs.py                                                     # rapport + livrable
```

Les commandes exactes et leurs résultats sont dans `twine_neuron/LOG.md`.
