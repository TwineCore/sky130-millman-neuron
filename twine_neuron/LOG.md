# LOG — TwineAnalog / twine_neuron

Format : commande → résultat → décision. Chemins relatifs à `twine_neuron/` (Mac) et
`~/analog_designs/twine_neuron/` (VM, `/foss/designs/twine_neuron` dans le conteneur).

## Demandes utilisateur en attente (fin de projet)
- Regrouper tout ce qui concerne le neurone analogique dans un dossier dédié, avec un **PDF** qui explique
  le pourquoi et le comment de la conception, une **datasheet** et un **guide utilisateur**
  (demande du 2026-11-11, à livrer après la phase 7).

## Phase 0 — Environnement (2026-11-11)

| Commande | Résultat | Décision |
|---|---|---|
| `ssh <user>@<vm-ip> hostname` | OK | — |
| `docker ps` | `eda-tools` (hpretl/iic-osic-tools:latest), up | conteneur recréé le jour même (`docker run … -v ~/analog_designs:/foss/designs`) |
| `echo $PDK_ROOT $PDK` | `/foss/pdks`, **`ihp-sg13g2`** | ⚠ PDK par défaut = IHP : chemins sky130A **absolus** partout ; `export PDK=sky130A` pour xschem |
| `cat ~/.spiceinit` | `set ngbehavior=hsa`, `ng_nomodcheck`, `enable_noisy_r` | compatible sky130 |
| versions | ngspice-47, xschem 3.4.8RC, magic 8.3.685, netgen 1.5.324, KLayout 0.30.12 ; open_pdks 1689ac3 | — |
| Projets existants relus | `../inverter_tb.spice`, `../ota_tb.spice`, `../ota.spice`, `../layout_ota.py`, `../pex.tcl`, `../sim_ota.sh`, `../flow.sh`, `../drc.sh`, `../extract.tcl` | flow réutilisé : `.lib …/sky130.lib.spice <corner>`, rcfile `sky130A.magicrc`, `sky130A_setup.tcl`, DRC KLayout avec `-rd feol=true -rd beol=true -rd offgrid=true` (sans eux : 0 règle vérifiée) |

## Phase 1 — Architecture et spécifications (2026-11-11)

### Lecture du PDK → `spec/PDK_DATA.md`
| Commande | Résultat |
|---|---|
| `grep -n "^.lib" $NG/sky130.lib.spice` | corners MOS tt/sf/ff/ss/fs ; R/C `_ll/_hh/_hl/_lh` ; `*_mm` ; `mc` |
| lecture `res_xhigh_po__base.model.spice` | rsheet 2000 Ω/□, rcon 588 Ω @w = 0.35, Pelgrom 0.0347/√(WL), tc1 −1.47e−3 |
| `grep var_mult r+c/*__lin.spice` | ±5 aux corners R (≈ ±8.4 % de R) |
| `grep crpf r+c/res_typical__cap_typical.spice` | crpf 1.06e−4 F/m², crpfsw 5.04e−11 F/m |
| `montecarlo.spice` | MIM : camimc 2.00 fF/µm², cpmimc 0.19 fF/µm |
| `grep toxe nfet_01v8__tt.pm3.spice` | toxe 4.148 nm → Cox 8.32 fF/µm² |
| `ngspice -b sim/pdk_char/avt_mc.spice` (tt_mm, 200 tirages, `reset` dans `dowhile`) | A_ΔVgs = 5.5 / 5.4 / 6.4 mV·µm (WL = 1 / 4 / 16) → `results/pdk_avt_mc.csv` ; retenu 6.4 |

### Modèle → `calc/millman_model.py`
| Commande | Résultat | Décision |
|---|---|---|
| `../.venv/bin/python calc/millman_model.py` (5.7 s) | `calc/out/model_summary.txt` ; 102 M points × 3 VDD : 0 erreur de signe ; V± ∈ [0.756, 1.62] @1.62 V | équilibrage par synapse validé |
| idem | Thévenin VDD/2 + StrongARM NMOS impossible ; G0 vers VDD → G0 = 52, LSB_min 14.53 mV | G0 = 52 Gu vers VDD |
| idem | Ru ≤ 1.72 MΩ (vitesse) vs Ru ≥ 3.18 MΩ (puissance) | **conflit** → Ru = 1.72 MΩ provisoire, décision demandée à l'utilisateur |
| idem | σ(R_U) 0.675 % ; \|INL\| max 0.12 LSB (poids), 0.27 LSB (biais) ; 0 erreur fonctionnelle (1000 dies × 3 VDD) | OK |
| `TN_BBITS=3 … --noplot` | SAR 681/3000 erreurs ; conflit P/vitesse toujours là | biais **5 bits** proposé |
| `TN_BBITS=4 … --noplot` | SAR 41/3000 erreurs (`results/var/` = variante 4 bits) | idem |
| `results/model_ru_tradeoff.csv` @3.18 MΩ | t_settle 145 ns | option 2 ⇒ ≈ 5 MHz |

Livrables : `spec/SPEC.md`, `spec/ARCHI.md`, `spec/PDK_DATA.md`, `calc/millman_model.py`, `calc/out/*`,
`results/model_*.csv`, `plots/model_overview.png`.

🛑 **Point d'arrêt phase 1** : en attente du « OK phase 2 » et des décisions sur S4 (biais 5 bits) et S12
(puissance).
| itération 2 — `ron power settle` | Ron/R 0.359 % ; P pire code 131.66 µW (modèle 131.5) ; **t_settle pire 34.22 ns** (S = 14.5) | S10 OK (≤ 50 ns visé, budget 85 ns) |
| itération 2 — `dc` | erreur ΔV max 0.078 LSB ; INL poids 0.014 / biais 0.055 LSB ; DNL 0.003 LSB ; 0 erreur de signe ; Vcm min 0.937 V ; P moy 72.9 µW | OK ; S12 informative |
| itération 2 — `func xor` (pas 20 ps) | ET/OU/NON-ET 0/12, XOR 0/4 ; kickback 29.9 mV abs. mais 31.8 % de ΔV max dans la fenêtre de décision, 0 inversion ; P moy séquence 26.9 µW | kickback absolu > LSB/4 (critère ARCHI) **mais proportionnel à ΔV** : sans effet sur le signe → repli double-tail non retenu, noté en limite |
| itération 2 — `tdec` | t_dec à 0.5 LSB_min : 0.543 ns (Vcm 0.84), 0.33 ns (1.3) | OK (budget 5 ns) |
| `sim/summarize.py pre` + `plots/plot_phase2.py` | `results/prelayout_tt.csv` (19 métriques) ; `plots/pre_{dc,comp,settle,func,xor}.png` | métriques v1 périmées archivées dans `results/iter1/` |

## Phase 3 — Corners et Monte Carlo (2026-11-12, lancée en tâche détachée `sim/phase3_all.sh`)
| Commande | Résultat | Décision |
|---|---|---|
| `sim/run_mc.py validate` (tt sans désappariement, offset imposé +3 mV, boucle de suivi bang-bang) | seuil mesuré −2.905 mV (pas max 20 ps : 44 s ; 50 ps : 25 s, même résultat) | MC comparateur à 50 ps |
| `sim/run_phase3.py all -j 3` | 45 points PVT (5 MOS × 3 VDD × 3 T, R typ) + 12 points R (hh à 1.62 V, ll à 1.98 V ; tt/ss/ff ; −40/125 °C) : dccrit + settle (S = 7.5/14.5/19.5) + power ; func sur 8 coins extrêmes | voir résultats ci-dessous |
| `sim/run_mc.py dcnet N=200` / `comp N=200` (tt_mm, 1.8 V, 27 °C) | réseau : ΔV aux codes critiques ; comparateur : seuil à Vcm 0.84 V (pire, mode commun le plus bas) | — |

## Phase 4/5 — Layout et vérification physique (2026-11-12)
| Commande | Résultat | Décision |
|---|---|---|
| `layout/gen_res.tcl` (magic, `sky130::sky130_fd_pr__res_xhigh_po_0p35` l = 52.61, guard 0) | `layout/res_unit.gds` | unité R_U issue du générateur PDK |
| `layout/layout_neuron.py` (klayout.db) | `layout/twine_neuron.gds` 447 × 92 µm = 0.041 mm² ; 36 slices, 124 R_U + 0 dummy, 28 bus d'entrée, comparateur 23 T | voir itérations PVS |
| PVS it. 1 (`pvs/pvs.sh`) | magic DRC 1035 (li.5 540, via.5a 376, met3.6 123, met2.2 200, rpm.1 10…) ; LVS 348/349 devices, VDD absent | enclosures li, pastilles via2/3, grille 0.01 µm, urpm continu, VDD comparateur en met4 |
| PVS it. 2 | magic DRC 15 → 10 (rpm.1) ; LVS 349/349 devices, 225/224 nets (caisson du comparateur isolé : via sur le rail ntap décalée) | correction de la pile de vias VDD |
| PVS it. 3 | magic DRC 0 ; **KLayout 0 violation / 256 catégories** (après implants continus par rangée, nsdm/psdm.1) ; **LVS « Circuits match uniquely »** 349 devices, 224 nets | — |
| `pex/pex.tcl` (antennacheck) | 3 violations d'antenne met3 (ratio 429–806 > 400) sur les bus d'entrée longs | bus limités à leurs terminaux → **0 violation** (`pvs/antenna_pex.log`) ; DRC/LVS repassés : 0 / 0 / match |
| `pex/pex.tcl` | `pex/twine_neuron_pex.spice` : 17 751 R, 3 165 C (cthresh 0.01 fF) | — |
| post-layout `dccrit` | `.op` non convergé (V+ = −1760 V : solution parasite du modèle xhigh_po à coefficients en tension négatifs, `sim/out/dbg_post_op.log`) | `TN_RSHUNT=1e12` + `.nodeset` V± = 0.75·VDD pour la PEX → 0 erreur de signe, erreur max 0.1 LSB |
| `calc/millman_model.py --noplot` (VM ; le JSON du conteneur était resté en Ru = 1.72 MΩ) + `run_phase2.py ron` | Ron/R_slice max **0.513 %** (avec Ru = 1.207 MΩ ; 0.359 % était rapporté à l'ancien Ru) | S14 OK |
| `tdec sar comp` (itération 2) | t_dec 0.543 ns ; SAR : 2 lectures complètes exactes (+28 → +28, −28 → −28, 6 décisions), job arrêté (≈ 25 min/lecture) | décisions limites des 10 vecteurs SAR couvertes par `dccrit` (codes à ±0.5 LSB) ; `comp` relancé seul |

### Phase 3 — résultats (2026-11-12, `sim/out/phase3_corners.log`)
| Source | Résultat | Décision |
|---|---|---|
| `results/corners_pre.csv` / `_worst.csv` (57 points) | 0 erreur de signe ; \|ΔV\| min 5.59 mV (fs 1.62 V 125 °C) ; erreur max 0.449 LSB (idem) ; Vcm min 0.756 V (ff 1.62 V −40 °C) ; **t_settle pire 47.08 ns** (ss_hh 1.62 V −40 °C) ; func 0 erreur sur les 8 coins ; P func max 65.0 µW ; P statique pire code max 367.4 µW (fs 1.98 V 125 °C) | 8 points « NON » = uniquement le kickback absolu (même constat qu'à tt, 0 inversion) |
| `results/mc_summary.csv` (200 dies, tt_mm) | réseau : σ(err) 0.087 LSB, max 0.379 LSB, 0 erreur de signe, \|ΔV\| min 2.78 mV à ±0.5 LSB ; comparateur : σ_os 2.058 mV, \|offset\| max 5.52 mV | statut « OK » codé en dur sur la ligne \|ΔV\| min → corrigé en « info » (`sim/run_mc.py`) |
| `sim/mc_combine.py` → `results/mc_combined.csv` | croisement 200 × 200 : P(erreur) par décision aux codes ±0.5 LSB 2.3e-4 (empirique), 3.6e-4 (gaussien) ; paires en échec 74/40000 = **1.85e-3** (rendement ≈ 99.8 %) | calibration d'offset via le biais proposée en V2, non implémentée |
| `run_phase3.py` (agrégation) | `max()` sur des NaN rendait « pire func_err = nan » | filtre NaN ajouté, ré-agrégé |

## Phase 6 — Post-layout (PEX)
| Commande | Résultat | Décision |
|---|---|---|
| `TN_TAG=post … run_phase2.py dccrit power settle` (tt) | 0 erreur de signe ; erreur max 0.1 LSB ; \|ΔV\| min 8.04 mV ; Vcm 0.8415 V ; P 131.54 µW ; **t_settle 43.54 ns** (pré 34.22) | S10 OK |
| `run_phase2.py func` (post) | 1er essai : ngspice > mémoire (3.3 Go, 37k nœuds), `.dat` absent ; 2e : chemin PEX relatif | `.save` limité aux vecteurs utiles + chemin absolu, relancé (`sim/out/post_func_run.log`) |
| `TN_CTAG=p run_phase3.py post` (5 coins) → `results/corners_post.csv` | 0 erreur de signe ; \|ΔV\| min 7.23 mV ; Vcm min 0.757 V ; P pire 274.5 µW ; **t_settle pire 58.11 ns** (ss_hh 1.62 V −40 °C) | > cible 50 ns mais < budget dur 85 ns : noté en limite |
| `sim/post_vs_pre.py` → `results/post_vs_pre.csv` | t_settle +26 à +30 % (capacités de routage) ; Vcm, P, signe inchangés | — |
| `run_phase2.py func` post, séquence entière | tué à 1.085 µs / 1.2 µs (mémoire VM) | `TN_FUNC_GATES` : une porte par run (400 ns) |
| func post OR / NAND (v1) | **1 erreur / 4 chacune** : Q = 1 sur tous les slots, y compris ΔV ≈ −30 mV | diagnostic comparateur |
| `sim/dbg_post_comp.py` (codes b, h isolés, PEX v1) | ±87 mV et plus : correct ; b = −1 (−34 mV) et b = 0 h = 1 (−18 mV) → Q = 1 ; b = −2 (−68 mV) → Q = 0 | offset systématique post-layout ≈ −40 à −68 mV (pré : σ_os 2 mV) |
| hypothèse 1 : C à la masse OUTN/OUTP (−1.46 fF), XN/XP (−1.77 fF) (`pex/pex_pairs.py`) | Cbal ajoutées dans une copie de la PEX → décisions **inchangées** ; pistes rallongées (relayout v2) : Δ inchangé | rejetée |
| hypothèse 2 : jonctions de la paire ABBA (XN = 2 diffusions de bord, ad 4.32 µm² ; XP = 1 centrale, 2.16 µm²) | ad/pd égalisés dans une copie de la PEX → décisions **inchangées** | rejetée (asymétrie réelle, mais pas la cause) |
| `sim/dbg_cmp_nodes.py` (nœuds internes, pré vs post) | au front de CLK, post : XP 1.964 vs XN 1.912 V, **OUTP 2.095 vs OUTN 2.008 V** (pré : 1.880 / 1.873) → le latch part du côté OUTN avant que la paire n'agisse | injection asymétrique de CLK |
| couplages PEX vers CLK | C(CLK–OUTP) 2.66 vs C(CLK–OUTN) 0.91 fF ; C(CLK–XP) 2.49 vs C(CLK–XN) 0.80 fF : piste met3 CLK placée entre XP et OUTP (ordre d'apparition des terminaux) | ordre des pistes en miroir autour de CLK : `TAIL - Q TA SN OUTN XN INP CLK INN XP OUTP RP TB QB` (`layout/layout_neuron.py`, `TN_CH_LEGACY=1` pour l'ancien) |
| relayout v3 (`sim/relayout.sh`) | DRC KLayout 0 / magic 0 ; LVS match (349 dev, 224 nets) ; antenne 0 ; C(CLK–OUTN/OUTP) 0 / 0, C(CLK–XN/XP) 1.94 / 1.66 fF ; Q/QB 8.07 / 4.19 fF (sorties du latch SR, hors décision) | `pex/pex_pairs.py` rapporte maintenant les couplages CLK/TAIL |
| `dbg_post_comp.py` PEX v3 | b = −1 (−33.9 mV) Q = 0 ; b = 0 h = 1 (−18.5 mV) Q = 0 ; b = +1 h = 1 (+16.2 mV) Q = 1 ; ±2 LSB corrects | **offset corrigé** ; régression func/dccrit/power/settle : `sim/post_v3_regr.sh` |
| `sim/post_v3_regr.sh` (PEX v3, tt) → `sim/out/post_v3_regr.log` | func AND / OR / NAND : **0 erreur / 4** chacune, 0 inversion de signe pendant la décision ; kickback différentiel 21–23 mV (NON vs LSB/4, même constat qu'en pré-layout et aux coins, kickback/ΔV ≤ 38 %) ; P func 30–35 µW ; dccrit 0/34 erreur, \|ΔV\| min 8.04 mV, erreur max 0.1 LSB, Vcm min 0.8415 V ; P pire code 131.56 µW ; **t_settle 43.54 ns** | post-layout tt validé ; reste : coins post-layout sur PEX v3 (`run_phase3.py post`) |
| `sim/post_v3_corners.sh` (PEX v3 : `run_phase3.py post` + `sim/post_func_corners.py`, fonctionnel par porte aux 5 coins) → `results/corners_post.csv` | **func 0 / 12 erreur aux 5 coins**, 0 inversion de signe ; \|ΔV\| min 7.23 mV ; Vcm min 0.757 V ; t_settle pire 58.11 ns (ss_hh 1.62 V −40 °C, < budget 85 ns) ; P func max 72.9 µW, P pire 274.5 µW ; NON = kickback différentiel 19–27 mV (tous coins, comme en pré) + t_settle > 50 ns à ss_hh | anciens résultats PEX v1 archivés dans `results/old_pex_v1/`, `results/corners/old_pex_v1/` |
| `report/make_docs.py` (+ section « Correction post-layout : offset du comparateur », func post dans tableau/datasheet, captures layout refaites par `layout/snap_layout.py`) | `../neurone_analogique/` régénéré : PDF conception, datasheet, guide, GDS v3, netlists, plots | **projet terminé** |
| `report/make_docs.py` → `report/docs_html.py` (HTML/CSS → PDF WeasyPrint ; Chromium headless bloqué sur macOS) | Datasheet 6 p. et guide 5 p. refaits : schéma bloc et chronogramme SVG, tableau min/typ/max, exemple de codage, SAR, dépannage | correction : t_set pire cas = 58.1 ns post-layout (ss_hh), et non 47.1 |
