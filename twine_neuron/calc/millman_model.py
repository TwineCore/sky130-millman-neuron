#!/usr/bin/env python3
"""TwineAnalog — modèle idéal + dimensionnement du neurone Millman à synapses tri-state (sky130A).

Exécution (depuis twine_neuron/) :  python3 calc/millman_model.py
Sorties : calc/out/model_summary.txt, calc/out/model_summary.json, results/model_*.csv, plots/model_*.png

Toutes les constantes PDK viennent de spec/PDK_DATA.md (source indiquée en commentaire).
Les HYPOTHÈSES (non PDK) sont regroupées dans HYP et marquées « à vérifier » : elles sont
re-mesurées en phase 2 (simulation transistor).
"""
import json
import math
import os
import sys
import itertools
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, RES, PLT = (os.path.join(ROOT, d) for d in ("calc/out", "results", "plots"))
for d in (OUT, RES, PLT, os.path.join(RES, "var")):
    os.makedirs(d, exist_ok=True)
rng = np.random.default_rng(20261111)
LOG = []


def log(s=""):
    print(s)
    LOG.append(s)


# ============================================================ PDK (spec/PDK_DATA.md)
W_R = 0.35                                     # µm, largeur xhigh_po (plus petite = moins de capa/Ω)
RSHEET = 2000.0                                # Ω/□  res_xhigh_po__base
RCON = -46.62 / W_R**2 + 331.73 / W_R + 20.576  # Ω par extrémité
PELGROM = 0.0347                               # σ(ΔR/R)·√(WL[µm²]) sur le corps
REND_MM = 0.0472 / math.sqrt(W_R)              # σ relatif des extrémités
R1VAR = 11.76 / W_R                            # Ω/µm, × var_mult (±5 aux corners R)
TC1, TC2 = -1.47e-3, 2.7e-6                    # /°C, /°C²
CRPF = 1.06e-4 * 1e-12                         # F/µm²  (crpf_precision typ)
CRPFSW = 5.04e-11 * 1e-6                       # F/µm   (crpfsw_precision_1_1 typ)
HEAD = 2.08                                    # µm, extension de tête dans la formule de capa du modèle
COX = 8.32e-15                                 # F/µm²  (toxe 4.148 nm, epsrox 3.9)
A_DVGS = 6.4e-3                                # V·µm, Monte Carlo tt_mm (results/pdk_avt_mc.csv)
CMIM = 2.0e-15                                 # F/µm²  camimc

# ============================================================ spécification / architecture
VDD, VDD_MIN, VDD_MAX = 1.8, 1.62, 1.98
N_IN = 4
W_BITS = (1, 2, 4)                  # poids 3 bits + signe : |w| ≤ 7
B_BITS = (1, 2, 4, 8, 16)           # biais 5 bits + signe : |b| ≤ 31 (ajustement : couvre Σw·x ∈ ±28 pour le SAR)
if os.environ.get("TN_BBITS"):     # variante d'étude : TN_BBITS=3 ou 4 (sorties suffixées)
    B_BITS = tuple(2**k for k in range(int(os.environ["TN_BBITS"])))
W_MAX, B_MAX = sum(W_BITS), sum(B_BITS)
HALF = 0.5                          # slice demi-LSB (lecture SAR sans égalité)
T_SETTLE_SPEC = 50e-9               # s, à 0.5 LSB
P_SPEC = 50e-6                      # W statique, neurone actif

HYP = {  # hypothèses de conception (pas des données PDK) — à vérifier en phase 2
    "VCM_LO": 0.75,     # V, bas de la fenêtre d'entrée d'un StrongARM à paire NMOS (≈ Vth + Vdsat queue)
    "K_DIST": 0.5,      # fraction de la capa répartie d'une branche vue par le pôle du nœud
    "C_ROUTE": 30e-15,  # F, routage par nœud (V+/V− blindés)
    "K_LATCH": 1.3,     # facteur offset total / offset de paire d'entrée (latch, horloge)
    "PITCH_R": 1.0,     # µm, pas des résistances xhigh_po en réseau (estimation surface)
    "T_MARGIN": 1.2,    # marge τ : corner R haut (+8.4 %) et −40 °C (+11 %), capa corner non incluse
}

# Réalisation à partir d'une résistance unitaire R_U = Ru/4 (conductance 4 Gu) :
#   (n_série, n_parallèle) ; poids = n_p / n_s × 4
REAL = {0.5: (8, 1), 1: (4, 1), 2: (2, 1), 4: (1, 1), 8: (1, 2), 16: (1, 4)}
for wgt, (ns, npar) in REAL.items():
    assert abs(4 * npar / ns - wgt) < 1e-12


def unit_length(Ru):
    """Longueur (µm) d'une unité R_U = Ru/4 en xhigh_po w = 0.35 (typ)."""
    return (Ru / 4 - 2 * RCON) * W_R / RSHEET


def unit_cap(L):
    """Capa totale vers substrat d'une unité (c1 + c2 du modèle PDK)."""
    return (L + 2 * HEAD) * W_R * CRPF + 2 * (L + 2 * HEAD + W_R) * CRPFSW


def branches_per_node():
    """Liste (poids, n_s, n_p) des branches physiquement reliées à UN nœud (V+ ou V−)."""
    b = [(w, *REAL[w]) for _ in range(N_IN) for w in W_BITS]      # banc synapse de chaque entrée
    b += [(w, *REAL[w]) for w in B_BITS]                           # banc de biais
    b += [(HALF, *REAL[HALF])]                                     # demi-LSB
    return b


# ============================================================ 1. G0 et mode commun
log("=" * 78)
log("TwineAnalog — modèle Millman (calc/millman_model.py)")
log("=" * 78)
S_MAX = N_IN * W_MAX + B_MAX + HALF
log(f"Bornes : N_in={N_IN}, |w|<=7, |b|<={B_MAX}, demi-LSB 0.5 -> S_max = Σ|w|+|b|+0.5 = {S_MAX}")


def g0_min(vt_ratio, vlo, vhi, vdd_lo, vdd_hi, s_max):
    """Plus petit G0 (unités Gu) qui garde V± dans [vlo, vhi] pour tout S ≤ s_max et VDD ∈ [vdd_lo, vdd_hi].
    Thévenin de G0 vers VT = vt_ratio·VDD."""
    best = None
    for g0 in np.arange(0.5, 400, 0.5):
        ok = True
        for vdd in (vdd_lo, vdd_hi):
            for s in (0.0, s_max):                 # extrêmes (monotone en S)
                d = s + g0
                vmin = vt_ratio * vdd * g0 / d
                vmax = (vdd * s + vt_ratio * vdd * g0) / d
                vh = vhi if vhi is not None else vdd
                if vmin < vlo - 1e-12 or vmax > vh + 1e-12:
                    ok = False
        if ok:
            best = g0
            break
    return best


opts = {
    "A: StrongARM NMOS, G0 tout vers VDD (VT=VDD)": (1.0, HYP["VCM_LO"], None),
    "B: comparateur rail-à-rail [0.3, VDD-0.3], VT=VDD/2": (0.5, 0.3, 1.32),
    "C: StrongARM NMOS, VT=VDD/2 (proposition initiale)": (0.5, HYP["VCM_LO"], None),
}
log("\nChoix du Thévenin G0 (fenêtre comparateur sur VDD ∈ [1.62, 1.98]) :")
g0_tab = {}
for k, (vt, vlo, vhi) in opts.items():
    g0 = g0_min(vt, vlo, vhi, VDD_MIN, VDD_MAX, S_MAX)
    if g0 is None:
        log(f"  {k:52s} -> impossible")
        continue
    lsb = VDD_MIN / (S_MAX + g0)
    g0_tab[k] = (g0, lsb)
    log(f"  {k:52s} -> G0 >= {g0:5.1f} Gu, LSB_min = {lsb*1e3:5.2f} mV")
G0 = 4 * math.ceil(g0_tab["A: StrongARM NMOS, G0 tout vers VDD (VT=VDD)"][0] / 4)   # multiple de 4 (unités R_U en //)
D_MAX = S_MAX + G0
LSB_MIN = VDD_MIN / D_MAX
log(f"Retenu : option A, G0 = {G0} Gu ({G0//4} unités R_U en parallèle vers VDD), D_max = {D_MAX}")
log(f"LSB = VDD/D : min {LSB_MIN*1e3:.2f} mV (VDD=1.62, D_max) ; nominal à D_max {VDD/D_MAX*1e3:.2f} mV")

# ============================================================ 2. Enumération exhaustive des codes
log("\nEnumération exhaustive : 15^4 poids × 63 biais × 2 (demi-LSB) × 16 entrées = "
    f"{15**4*63*2*16/1e6:.1f} M points (×3 VDD)")
wv = np.array(list(itertools.product(range(-W_MAX, W_MAX + 1), repeat=N_IN)), dtype=np.int8)
xv = np.array(list(itertools.product((0, 1), repeat=N_IN)), dtype=np.int8)
Ppos = np.clip(wv, 0, None).astype(np.int16) @ xv.T.astype(np.int16)      # unités à 1 sur V+ (hors biais)
Nneg = np.clip(-wv, 0, None).astype(np.int16) @ xv.T.astype(np.int16)     # unités à 1 sur V−
Sw = np.abs(wv).sum(1).astype(np.int16)[:, None]
stats = {v: dict(vmin=9, vmax=-9, dmin_lsb=9e9, ties=0, err=0, n=0, pmax_g=0.0, psum_g=0.0)
         for v in (VDD_MIN, VDD, VDD_MAX)}
for b in range(-B_MAX, B_MAX + 1):
    for h in (0, 1):
        S = Sw + abs(b) + HALF * h
        D = S + G0
        ghp = G0 + Ppos + max(b, 0)
        ghn = G0 + Nneg + max(-b, 0) + HALF * h
        num = (Ppos - Nneg + b) - HALF * h                       # Σw·x + b − 0.5h
        pg = (ghp * (D - ghp) + ghn * (D - ghn)) / D             # puissance / (VDD²·Gu)
        for vdd, st in stats.items():
            vp, vn = vdd * ghp / D, vdd * ghn / D
            st["vmin"] = min(st["vmin"], vp.min(), vn.min())
            st["vmax"] = max(st["vmax"], vp.max(), vn.max())
            dv = vp - vn
            nz = num != 0
            st["ties"] += int((~nz).sum())
            st["err"] += int((np.sign(dv[nz]) != np.sign(num[nz])).sum())
            st["dmin_lsb"] = min(st["dmin_lsb"], float(np.abs(num[nz]).min()))
            st["n"] += num.size
        stats[VDD]["pmax_g"] = max(stats[VDD]["pmax_g"], float(pg.max()))
        stats[VDD]["psum_g"] += float(pg.sum())
for vdd, st in stats.items():
    log(f"  VDD={vdd:.2f} : V± ∈ [{st['vmin']:.3f}, {st['vmax']:.3f}] V ; erreurs de signe (modèle idéal) = {st['err']} ; "
        f"égalités (h=0, Σ+b=0) = {st['ties']} ; |Σ+b-0.5h| min hors égalité = {st['dmin_lsb']} LSB")
P_MAX_G = stats[VDD]["pmax_g"]                      # max de (Gh·Gl/D) sommé sur 2 nœuds, unités Gu
P_AVG_G = stats[VDD]["psum_g"] / stats[VDD]["n"]
cm_ok = stats[VDD_MIN]["vmin"] >= HYP["VCM_LO"] - 1e-9
log(f"  Mode commun min (VDD=1.62) = {stats[VDD_MIN]['vmin']:.3f} V >= VCM_LO={HYP['VCM_LO']} V : {'OK' if cm_ok else 'NON'}")

# tableau par S (dénominateur)
rows_s = []
for S in np.arange(0, S_MAX + 0.5, 0.5):
    D = S + G0
    rows_s.append(dict(S=S, D=D, LSB_mV_1v8=1e3 * VDD / D, LSB_mV_1v62=1e3 * VDD_MIN / D,
                       Vmin_1v62=VDD_MIN * G0 / D, Vmax_1v8=VDD))
with open(os.path.join(RES, ("var/" if os.environ.get("TN_BBITS") else "") + "model_lsb_vs_S.csv"), "w") as f:
    f.write(",".join(rows_s[0]) + "\n")
    for r in rows_s:
        f.write(",".join(f"{v:.6g}" for v in r.values()) + "\n")

# ============================================================ 3. Ru : vitesse vs puissance
WC = 12.0  # µm², W·L paire d'entrée comparateur (dimensionné en §5, utilisé ici pour la capa)


def node_cap(Ru):
    L = unit_length(Ru)
    cu = unit_cap(L)
    cb = sum(ns * npar * cu for (_, ns, npar) in branches_per_node()) + (G0 // 4) * cu
    return HYP["K_DIST"] * cb + COX * WC + HYP["C_ROUTE"], L, cu


def t_settle_worst(Ru, margin=1.0):
    """max sur S de τ(S)·ln(2S) ; τ = C_node·Ru/D (le nœud porte toutes les branches, actives ou non)."""
    c, _, _ = node_cap(Ru)
    best = (0, None)
    for S in np.arange(0.5, S_MAX + 0.5, 0.5):
        D = S + G0
        t = margin * c * Ru / D * math.log(max(2 * S, 2))
        if t > best[0]:
            best = (t, S)
    return best


def p_max(Ru, vdd=VDD):
    return vdd**2 * P_MAX_G / Ru


ru_grid = np.logspace(5, 7.3, 200)
ts = np.array([t_settle_worst(r, HYP["T_MARGIN"])[0] for r in ru_grid])
pm = np.array([p_max(r) for r in ru_grid])
RU_SPEED = ru_grid[ts <= T_SETTLE_SPEC].max()
RU_POWER = ru_grid[pm <= P_SPEC].min()
log(f"\nCompromis Ru (Ru = résistance d'une conductance unitaire Gu ; unité de layout R_U = Ru/4) :")
log(f"  P_max = VDD²·{P_MAX_G:.2f}·Gu ; P_moy (codes uniformes) = VDD²·{P_AVG_G:.2f}·Gu")
log(f"  vitesse : t_settle(pire code, marge {HYP['T_MARGIN']}) <= 50 ns  =>  Ru <= {RU_SPEED/1e6:.3f} MΩ")
log(f"  puissance : P_max(VDD=1.8) <= 50 µW               =>  Ru >= {RU_POWER/1e6:.3f} MΩ")
if RU_POWER <= RU_SPEED:
    RU = RU_POWER
    log(f"  -> compatibles ; Ru choisi = {RU/1e6:.3f} MΩ (puissance minimale qui tient la vitesse)")
    CONFLICT = False
else:
    RU = RU_SPEED
    CONFLICT = True
    log(f"  -> INCOMPATIBLES (τ ∝ Ru² car la capa parasite poly ∝ longueur ∝ Ru, P ∝ 1/Ru)")
    log(f"     Ru retenu = {RU/1e6:.3f} MΩ (vitesse prioritaire) => P_max = {p_max(RU)*1e6:.1f} µW, "
        f"P_moy = {VDD**2*P_AVG_G/RU*1e6:.1f} µW")
# Itération 2 (phase 2, décision utilisateur 2026-11-12 « priorité = performance ») : le modèle localisé de τ
# sous-estime la stabilisation (simulé 65.2 ns à Ru = 1.72 MΩ, τ ∝ Ru² mesuré : results/pre_settle.csv,
# sim/out/explore_ru0p8.txt) -> Ru = RU_SCALE × Ru(vitesse, modèle). S12 devient informative.
RU_SCALE = float(os.environ.get("TN_RU_SCALE", "0.7"))
RU = RU * RU_SCALE
log(f"  itération 2 : Ru × {RU_SCALE} => Ru = {RU/1e6:.3f} MΩ (P_max {p_max(RU)*1e6:.1f} µW, "
    f"P_moy {VDD**2*P_AVG_G/RU*1e6:.1f} µW)")
# arrondi : longueur d'unité sur grille 0.01 µm
L_U = round(unit_length(RU), 2)
R_U = L_U * RSHEET / W_R + 2 * RCON
RU = 4 * R_U
C_NODE, _, C_U = node_cap(RU)
t_w, s_w = t_settle_worst(RU)
t_wm, _ = t_settle_worst(RU, HYP["T_MARGIN"])
log(f"  Unité R_U : xhigh_po w={W_R} L={L_U} µm -> R_U = {R_U/1e3:.1f} kΩ (Ru = {RU/1e6:.3f} MΩ), C_U = {C_U*1e15:.2f} fF")
log(f"  C_nœud (estim.) = {C_NODE*1e15:.0f} fF ; R_nœud = Ru/D ∈ [{RU/D_MAX/1e3:.1f}, {RU/G0/1e3:.1f}] kΩ")
log(f"  t_settle 0.5 LSB : typ {t_w*1e9:.1f} ns (pire S = {s_w}) ; avec marge {t_wm*1e9:.1f} ns")
log(f"  P_max = {p_max(RU)*1e6:.1f} µW @1.8 V, {p_max(RU, VDD_MAX)*1e6:.1f} µW @1.98 V ; "
    f"P_moy = {VDD**2*P_AVG_G/RU*1e6:.1f} µW")
with open(os.path.join(RES, ("var/" if os.environ.get("TN_BBITS") else "") + "model_ru_tradeoff.csv"), "w") as f:
    f.write("Ru_ohm,t_settle_worst_margin_s,P_max_W\n")
    for r, t, p in zip(ru_grid, ts, pm):
        f.write(f"{r:.6g},{t:.6g},{p:.6g}\n")

# ============================================================ 4. Drivers, explicit node cap
R_SLICE_MIN = RU / 16                       # bit 16 du biais = 4 R_U en parallèle
RON_MAX = 0.01 * R_SLICE_MIN
log(f"\nDrivers : plus petite slice = biais 16 -> R = Ru/16 = {R_SLICE_MIN/1e3:.1f} kΩ ; Ron < 1 % -> Ron < {RON_MAX:.0f} Ω")
log("Capa de nœud explicite : 0 (la capa répartie des résistances, "
    f"{C_NODE*1e15:.0f} fF, domine déjà et absorbe le kickback ; une MIM ralentirait τ)")

# ============================================================ 5. Comparateur : offset
SIG_TGT = LSB_MIN / 6     # marge SAR = 0.5 LSB à 3σ  (spec utilisateur : LSB/3)
wl_req = (HYP["K_LATCH"] * A_DVGS / SIG_TGT) ** 2
log(f"\nComparateur : LSB_min = {LSB_MIN*1e3:.2f} mV -> spec σ < LSB/3 = {LSB_MIN/3*1e3:.2f} mV ;"
    f" cible σ < LSB/6 = {SIG_TGT*1e3:.2f} mV (marge SAR 0.5 LSB à 3σ)")
log(f"  σ_os ≈ {HYP['K_LATCH']}·A_ΔVgs/√(WL) -> W·L >= {wl_req:.1f} µm² ; retenu W·L = {WC} µm² "
    f"(ex. W=12 L=1 ou 2×(6/1) en centroïde commun)")
SIG_OS = HYP["K_LATCH"] * A_DVGS / math.sqrt(WC)
log(f"  σ_os estimé = {SIG_OS*1e3:.2f} mV = LSB_min/{LSB_MIN/SIG_OS:.1f} ; C_gate ≈ {COX*WC*1e15:.0f} fF par entrée")

# ============================================================ 6. Monte Carlo mismatch (résistances + offset)
N_MC = 2000
SIG_U = PELGROM / math.sqrt(W_R * L_U) * (L_U * RSHEET / W_R) / R_U       # σ relatif de R_U (corps seul)
SIG_END = REND_MM * (2 * RCON) / R_U / math.sqrt(2)
SIG_UT = math.hypot(SIG_U, SIG_END)
log(f"\nMonte Carlo ({N_MC} tirages) : σ(R_U)/R_U = {SIG_UT*100:.3f} % (Pelgrom PDK, L={L_U} µm)")


def draw_bank(bits, n):
    """Conductances réelles (unités Gu) des slices d'un banc, n tirages -> (n, len(bits))."""
    g = np.zeros((n, len(bits)))
    for j, w in enumerate(bits):
        ns, npar = REAL[w]
        r = 1 + SIG_UT * rng.standard_normal((n, ns, npar))         # résistances unitaires relatives
        g[:, j] = (1.0 / (r.sum(1) / 4)).sum(1)  # série puis //, conductance en Gu (R_U = Ru/4)
    return g


def codes_err(g, bits):
    codes = np.array(list(itertools.product((0, 1), repeat=len(bits))))
    ideal = codes @ np.array(bits)
    real = g @ codes.T
    return ideal, real - ideal


gw = draw_bank(W_BITS, N_MC)
gb = draw_bank(B_BITS, N_MC)
iw, ew = codes_err(gw, W_BITS)
ib, eb = codes_err(gb, B_BITS)
inl_w = np.abs(ew).max(1)
inl_b = np.abs(eb).max(1)
log(f"  Erreur de poids (synapse 3b) : σ max-INL = {np.std(ew, 0).max():.4f} LSB ; |INL| max sur {N_MC} = {inl_w.max():.4f} LSB")
log(f"  Erreur de biais (5b)         : σ max-INL = {np.std(eb, 0).max():.4f} LSB ; |INL| max sur {N_MC} = {inl_b.max():.4f} LSB")
with open(os.path.join(RES, ("var/" if os.environ.get("TN_BBITS") else "") + "model_mc_weight_error.csv"), "w") as f:
    f.write("bank,code,sigma_err_LSB,max_abs_err_LSB\n")
    for name, idl, e in (("weight", iw, ew), ("bias", ib, eb)):
        for c in range(len(idl)):
            f.write(f"{name},{idl[c]},{e[:, c].std():.5g},{np.abs(e[:, c]).max():.5g}\n")


def eval_dv(vdd, w, b, h, x, die):
    """ΔV réel (V) pour un die : w (4,), b, h, x (4,) ; die = dict de bancs tirés."""
    gp = gn = G0 + 0.0
    hi_p = hi_n = G0 + 0.0
    for i in range(N_IN):
        code = abs(w[i])
        g = sum(die["w"][i][j] for j, bit in enumerate(W_BITS) if code & bit)
        g0side = sum(die["w0"][i][j] for j, bit in enumerate(W_BITS) if code & bit)   # banc opposé, piloté à 0
        if w[i] > 0:
            gp += g; gn += g0side; hi_p += g * x[i]
        elif w[i] < 0:
            gn += g; gp += g0side; hi_n += g * x[i]
    code = abs(b)
    g = sum(die["b"][j] for j, bit in enumerate(B_BITS) if code & bit)
    g0side = sum(die["b0"][j] for j, bit in enumerate(B_BITS) if code & bit)
    if b > 0:
        gp += g; gn += g0side; hi_p += g
    elif b < 0:
        gn += g; gp += g0side; hi_n += g
    if h:
        gn += die["h"][0]; gp += die["h"][1]; hi_n += die["h"][0]
    return vdd * (hi_p / gp - hi_n / gn)


def make_die():
    return {"w": draw_bank(W_BITS, N_IN), "w0": draw_bank(W_BITS, N_IN),
            "b": draw_bank(B_BITS, 1)[0], "b0": draw_bank(B_BITS, 1)[0],
            "h": draw_bank((HALF, HALF), 1)[0], "os": SIG_OS * rng.standard_normal()}


# ============================================================ 7. Tables de vérité (idéal) + taux d'erreur MC
GATES = {  # (w1, w2, b) : sign(2·x1+2·x2+b) — marge ≥ 1 LSB (biais impair)
    "AND": ((2, 2), -3), "OR": ((2, 2), -1), "NAND": ((-2, -2), 3),
}
ideal_die = {"w": np.ones((N_IN, 3)) * np.array(W_BITS), "w0": np.ones((N_IN, 3)) * np.array(W_BITS),
             "b": np.array(B_BITS, float), "b0": np.array(B_BITS, float), "h": np.array([HALF, HALF]), "os": 0.0}
tt_rows = []
log("\nTables de vérité attendues (modèle idéal, VDD = 1.8 V) :")
for gname, ((w1, w2), b) in GATES.items():
    w = (w1, w2, 0, 0)
    for x1, x2 in itertools.product((0, 1), repeat=2):
        x = (x1, x2, 0, 0)
        dv = eval_dv(VDD, w, b, 0, x, ideal_die)
        s = w1 * x1 + w2 * x2 + b
        tt_rows.append((gname, x1, x2, "", "", s, round(dv * 1e3, 3), int(dv > 0)))
    log(f"  {gname:5s} w=({w1:+d},{w2:+d}) b={b:+d} : " +
        " ".join(f"{x1}{x2}->{int(eval_dv(VDD, (w1, w2, 0, 0), b, 0, (x1, x2, 0, 0), ideal_die) > 0)}"
                 for x1, x2 in itertools.product((0, 1), repeat=2)))


def xor_221(x1, x2, die, vdd=VDD):
    """XOR 2-2-1 en multiplexage temporel : h1 = OR, h2 = NAND, y = AND(h1, h2)."""
    h1 = eval_dv(vdd, (2, 2, 0, 0), -1, 0, (x1, x2, 0, 0), die) - die["os"] > 0
    h2 = eval_dv(vdd, (-2, -2, 0, 0), 3, 0, (x1, x2, 0, 0), die) - die["os"] > 0
    y = eval_dv(vdd, (2, 2, 0, 0), -3, 0, (int(h1), int(h2), 0, 0), die) - die["os"] > 0
    return int(h1), int(h2), int(y)


for x1, x2 in itertools.product((0, 1), repeat=2):
    h1, h2, y = xor_221(x1, x2, ideal_die)
    tt_rows.append(("XOR_221", x1, x2, h1, h2, "", "", y))
log("  XOR 2-2-1 (3 évaluations : h1=OR, h2=NAND, y=AND(h1,h2)) : " +
    " ".join(f"{x1}{x2}->{xor_221(x1, x2, ideal_die)[2]}" for x1, x2 in itertools.product((0, 1), repeat=2)))
with open(os.path.join(RES, ("var/" if os.environ.get("TN_BBITS") else "") + "model_truth_tables.csv"), "w") as f:
    f.write("function,x1,x2,h1,h2,sum_wx_plus_b,dV_mV_ideal,out_expected\n")
    for r in tt_rows:
        f.write(",".join(str(v) for v in r) + "\n")

# MC fonctionnel + SAR, aux 3 VDD
N_FMC = 1000
fail = {k: 0 for k in ("AND", "OR", "NAND", "XOR_221", "SAR")}
n_eval = {k: 0 for k in fail}
sar_err = []


def sar_read(w, x, die, vdd):
    """Recherche dichotomique du plus petit b tel que sortie=1, avec demi-LSB : s = 1 − b_min."""
    lo, hi = -B_MAX, B_MAX                 # out(hi)=1 garanti si s ≥ 1−31
    while lo < hi:
        mid = (lo + hi) // 2
        if eval_dv(vdd, w, mid, 1, x, die) - die["os"] > 0:
            hi = mid
        else:
            lo = mid + 1
    return 1 - lo


for _ in range(N_FMC):
    die = make_die()
    for vdd in (VDD_MIN, VDD, VDD_MAX):
        for gname, ((w1, w2), b) in GATES.items():
            for x1, x2 in itertools.product((0, 1), repeat=2):
                out = eval_dv(vdd, (w1, w2, 0, 0), b, 0, (x1, x2, 0, 0), die) - die["os"] > 0
                fail[gname] += out != (w1 * x1 + w2 * x2 + b > 0)
                n_eval[gname] += 1
        for x1, x2 in itertools.product((0, 1), repeat=2):
            fail["XOR_221"] += xor_221(x1, x2, die, vdd)[2] != (x1 ^ x2)
            n_eval["XOR_221"] += 1
        w = tuple(rng.integers(-W_MAX, W_MAX + 1, N_IN))
        x = tuple(rng.integers(0, 2, N_IN))
        s = int(np.dot(w, x))
        r = sar_read(w, x, die, vdd)
        sar_err.append(r - s)
        fail["SAR"] += r != s
        n_eval["SAR"] += 1
log(f"\nMonte Carlo fonctionnel ({N_FMC} dies × VDD {{1.62, 1.8, 1.98}}, offset σ = {SIG_OS*1e3:.2f} mV) :")
for k in fail:
    log(f"  {k:8s} : {fail[k]} erreurs / {n_eval[k]} évaluations")
sar_err = np.array(sar_err)
log(f"  SAR (poids et entrées aléatoires) : erreur ∈ [{sar_err.min()}, {sar_err.max()}] LSB")

# sensibilité : offset nécessaire pour casser une porte (marge 1 LSB) et le SAR (0.5 LSB)
log(f"  Marges : portes 1 LSB = {VDD_MIN/(G0+4+3)*1e3:.1f} mV (D = G0+7) ; SAR 0.5 LSB_min = {LSB_MIN/2*1e3:.2f} mV "
    f"= {LSB_MIN/2/SIG_OS:.1f} σ_os")

# ============================================================ 8. Surface (estimation)
n_units = (sum(ns * npar for (_, ns, npar) in branches_per_node()) * 2 + 2 * (G0 // 4))
a_res = n_units * (L_U + 2 * 2.16) * HYP["PITCH_R"]
n_drv = 2 * (N_IN * len(W_BITS) + len(B_BITS) + 1)
log(f"\nSurface (estimation) : {n_units} unités R_U de {L_U} µm -> {n_units*L_U/1e3:.2f} mm de poly, "
    f"≈ {a_res:.0f} µm² ; {n_drv} drivers tri-state ; comparateur ≈ 600 µm² (estim.)")
A_TOT = a_res * 1.3 + n_drv * 40 + 600
log(f"  Total estimé (×1.3 routage) ≈ {A_TOT:.0f} µm² ≈ {A_TOT/1e6:.4f} mm²")

# ============================================================ résumé
summary = dict(S_MAX=S_MAX, G0=G0, D_MAX=D_MAX, LSB_MIN_mV=LSB_MIN * 1e3, LSB_NOM_DMAX_mV=VDD / D_MAX * 1e3,
               VCM_MIN_V=stats[VDD_MIN]["vmin"], RU_ohm=RU, R_U_ohm=R_U, L_U_um=L_U, C_NODE_fF=C_NODE * 1e15,
               T_SETTLE_ns=t_w * 1e9, T_SETTLE_MARGIN_ns=t_wm * 1e9, P_MAX_uW=p_max(RU) * 1e6,
               P_MAX_198_uW=p_max(RU, VDD_MAX) * 1e6, P_AVG_uW=VDD**2 * P_AVG_G / RU * 1e6,
               RU_SPEED_ohm=RU_SPEED, RU_POWER_ohm=RU_POWER, CONFLICT=CONFLICT, RON_MAX_ohm=RON_MAX,
               SIG_OS_mV=SIG_OS * 1e3, WL_COMP_um2=WC, SIG_RU_pct=SIG_UT * 100,
               INL_W_MAX_LSB=float(inl_w.max()), INL_B_MAX_LSB=float(inl_b.max()),
               FAILS={k: [int(fail[k]), int(n_eval[k])] for k in fail}, AREA_um2=A_TOT, N_UNITS=int(n_units),
               HYP=HYP)
SUF = f"_b{len(B_BITS)}" if os.environ.get("TN_BBITS") else ""
with open(os.path.join(OUT, f"model_summary{SUF}.json"), "w") as f:
    json.dump(summary, f, indent=1)
with open(os.path.join(OUT, f"model_summary{SUF}.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")

# ============================================================ tracés
if "--noplot" not in sys.argv:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    blue, red, grey, green = "#2a6fdb", "#d1495b", "#888888", "#2e9e6a"
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.5), dpi=140)
    # (a) transfert V+, V−, ΔV pour la config D_max (Σ|w| = 28, |b| = 31, h = 1)
    a = ax[0, 0]
    sv = np.arange(-28, 29)
    D = S_MAX + G0
    b = 0  # balayage de s = Σw·x avec biais nul pour montrer la linéarité
    vp = VDD * (G0 + np.clip(sv, 0, None)) / D
    vn = VDD * (G0 + np.clip(-sv, 0, None) + 0.5) / D
    a.plot(sv, vp, color=blue, label="V+")
    a.plot(sv, vn, color=red, label="V−")
    a.plot(sv, (vp - vn) * 1e3 / 1e3, color=green, label="ΔV = V+ − V−")
    a.axhline(HYP["VCM_LO"], color=grey, ls="--", lw=0.8)
    a.text(-28, HYP["VCM_LO"] + 0.02, "bas de fenêtre comparateur (hyp.)", fontsize=7, color=grey)
    a.set_xlabel("Σ w·x (unités) — config D_max, demi-LSB actif")
    a.set_ylabel("V")
    a.set_title(f"(a) Millman : linéarité, LSB = {VDD/D*1e3:.2f} mV @1.8 V")
    a.legend(fontsize=8)
    a.grid(alpha=0.3)
    # (b) LSB et fenêtre de mode commun vs S
    a = ax[0, 1]
    Ss = np.array([r["S"] for r in rows_s])
    for vdd, c in ((VDD_MIN, red), (VDD, blue), (VDD_MAX, green)):
        a.fill_between(Ss, vdd * G0 / (Ss + G0), vdd, color=c, alpha=0.12)
        a.plot(Ss, vdd * G0 / (Ss + G0), color=c, lw=1.2, label=f"V± min @{vdd} V")
    a.axhline(HYP["VCM_LO"], color=grey, ls="--", lw=0.8)
    a2 = a.twinx()
    a2.plot(Ss, VDD_MIN / (Ss + G0) * 1e3, color="k", lw=1.5, ls=":", label="LSB @1.62 V")
    a2.set_ylabel("LSB (mV)")
    a.set_xlabel("S = Σ|w| + |b| + 0.5h")
    a.set_ylabel("plage de V± (V)")
    a.set_title(f"(b) Mode commun et LSB vs charge (G0 = {G0} Gu)")
    a.legend(fontsize=7, loc="lower left")
    a2.legend(fontsize=7, loc="upper right")
    a.grid(alpha=0.3)
    # (c) compromis Ru
    a = ax[1, 0]
    a.loglog(ru_grid / 1e6, ts * 1e9, color=blue, label="t_settle pire code (×marge)")
    a.axhline(50, color=blue, ls="--", lw=0.8)
    a2 = a.twinx()
    a2.loglog(ru_grid / 1e6, pm * 1e6, color=red, label="P_max statique")
    a2.axhline(50, color=red, ls="--", lw=0.8)
    a.axvline(RU / 1e6, color="k", lw=1)
    a.text(RU / 1e6 * 1.05, 3, f"Ru = {RU/1e6:.2f} MΩ", fontsize=8)
    a.axvspan(RU_POWER / 1e6, ru_grid.max() / 1e6, color=red, alpha=0.06)
    a.axvspan(ru_grid.min() / 1e6, RU_SPEED / 1e6, color=blue, alpha=0.06)
    a.set_xlabel("Ru (MΩ) — conductance unitaire Gu = 1/Ru")
    a.set_ylabel("t_settle (ns)", color=blue)
    a2.set_ylabel("P_max (µW)", color=red)
    a.set_title("(c) Vitesse ∝ Ru² vs puissance ∝ 1/Ru")
    a.grid(alpha=0.3, which="both")
    # (d) MC
    a = ax[1, 1]
    a.hist(ew.ravel(), bins=60, color=blue, alpha=0.7, label="erreur de poids (LSB)")
    a.hist(eb.ravel(), bins=60, color=green, alpha=0.5, label="erreur de biais (LSB)")
    a.set_xlabel("erreur (LSB)")
    a.set_title(f"(d) Monte Carlo mismatch R ({N_MC} dies) ; σ_os = {SIG_OS*1e3:.2f} mV = LSB/{LSB_MIN/SIG_OS:.1f}")
    a.legend(fontsize=8)
    a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLT, "model_overview.png"))
    log(f"\nTracé : plots/model_overview.png")
