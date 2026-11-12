# Données PDK sky130A utilisées (lues, pas supposées)

PDK : `open_pdks 1689ac3f2dc763876eaf967227c7dfe831b031ae` (`$PDK_ROOT/sky130A/SOURCES`), `PDK_ROOT=/foss/pdks`.
Abréviations : `NG=$PDK_ROOT/sky130A/libs.tech/ngspice`, `REF=$PDK_ROOT/sky130A/libs.ref/sky130_fd_pr/spice`.

> ⚠ Dans le conteneur, la variable d'environnement `PDK` vaut **`ihp-sg13g2`** par défaut.
> Tous nos fichiers référencent sky130A par **chemin absolu** (`.lib`, rcfile Magic, setup Netgen) et
> `~/.spiceinit` contient bien `set ngbehavior=hsa` (requis par sky130). Pour xschem, il faudra
> exporter `PDK=sky130A` (phase 2).

## Corners ngspice (`$NG/sky130.lib.spice`)

| Axe | Sections | Source |
|---|---|---|
| MOS | `tt sf ff ss fs` | lignes 18–82 |
| R/C | suffixes `_ll _hh _hl _lh` (ex. `ss_hl`) ; `ll`/`hh`/`hl`/`lh` seuls = MOS tt | lignes 83–330 |
| Mismatch | `*_mm` → `mc_mm_switch=1` | lignes 343–655 |
| Process MC | `mc` → `mc_pr_switch=1` (`parameters/critical.spice`, `montecarlo.spice`) | ligne 669 |

Convention R/C (`$NG/r+c/*`) : `ll` = res_low/cap_low, `hh` = res_high/cap_high, `hl` = res_high/cap_low, `lh` = res_low/cap_high.

## Résistance poly `sky130_fd_pr__res_xhigh_po` (choisie pour les synapses)

Source : `$REF/sky130_fd_pr__res_xhigh_po__base.model.spice`

| Paramètre | Valeur | Remarque |
|---|---|---|
| `rsheet` | 2000 Ω/□ | `rbody = (l·rsheet + rbody_var)·(1+res_match)/w` |
| `rcon` (par extrémité) | −46.62/w² + 331.73/w + 20.576 → **588 Ω** à w = 0.35 µm | |
| `body_pelgrom` | 0.0347 → σ(ΔR/R) = **3.47 %·µm / √(W·L)** (fraction, sur le corps) | `res_match` |
| `rend_mm` | 0.0472/√w (mismatch des extrémités) | |
| `tc1`, `tc2` | −1.47e−3 /°C, 2.7e−6 /°C² | |
| `vc1_body`, `vc2_body` | −1e−3 /V, −1e−4 | non-linéarité en tension |
| `r1_var` (corner) | 11.76/w Ω/µm, × `var_mult` | |
| `var_mult` | 0 (typ), **±5** (`_hl/_hh` : +5, `_ll/_lh` : −5) | `$NG/r+c/res_*__lin.spice` ligne 4 |
| Capa vers substrat | `c = ((l+2·2.08)·w·crpf_precision + 2·(l+2·2.08+w)·crpfsw_precision_1_1)/2` à chaque extrémité | |
| `crpf_precision` | 1.06e−4 F/m² (0.106 fF/µm²) typ | `$NG/r+c/res_typical__cap_typical.spice` |
| `crpfsw_precision_1_1` | 5.04e−11 F/m (0.0504 fF/µm) typ ; 4.51e−11 à 4.67e−11 en cap_low | idem, `res_*__cap_low.spice` |

Comparaison `res_high_po_0p35` (`$REF/sky130_fd_pr__res_high_po_0p35.model.spice`) : `rcon = 589.99`,
même `body_pelgrom = 0.0347`. Mesure ngspice (OTA, `rc_check.spice`) : R ≈ 670 Ω + 1070 Ω/µm·L,
soit ≈ 374 Ω/□ → **5.3× moins résistif que xhigh_po** pour la même surface, d'où le choix de xhigh_po.

## Capacité MIM `sky130_fd_pr__cap_mim_m3_1`

Source : `$NG/parameters/montecarlo.spice` : `camimc = 2.00e−15 F/µm²` (nominal, `mim=0`),
`cpmimc = 1.90e−16 F/µm` (périmètre). Vérifié par simulation (OTA) : 15×15 µm → 0.46 pF.

## MOSFET `nfet_01v8`

| Paramètre | Valeur | Source |
|---|---|---|
| `toxe` | 4.148 nm, `epsrox = 3.9` → **Cox = 8.32 fF/µm²** | `$REF/sky130_fd_pr__nfet_01v8__tt.pm3.spice` |
| Mismatch de paire A_ΔVgs | **5.5 / 5.4 / 6.4 mV·µm** pour W·L = 1 / 4 / 16 µm² | Monte Carlo `tt_mm`, 200 tirages, I = 10 µA/µm de W/L : `sim/pdk_char/avt_mc.spice` → `results/pdk_avt_mc.csv` |

Valeur de conception retenue : **A_ΔVgs = 6.4 mV·µm** (pire des trois).
