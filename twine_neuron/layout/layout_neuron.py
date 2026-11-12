"""Layout du neurone Millman (twine_neuron) — sky130A — généré avec klayout.db.

Exécution (conteneur) :  cd layout && python3 layout_neuron.py   ->  twine_neuron.gds (cellule top twine_neuron)
Entrée : res_unit.gds (unité R_U xhigh_po w = 0.35, L = 52.61, générée par magic : gen_res.tcl).

Plan (x croissant) :
  [G0 : 26 unités, G0P/G0M entrelacées]  [36 slices, P/M entrelacées par (synapse, bit)]  [comparateur]
Chaque slice : ligne de drivers en bas (inverseurs D→DB, EN→ENB + pile tri-state × m, style cellule
standard : rangée N, zone médiane de grilles en li, rangée P en nwell), chaîne de R_U au-dessus dans la
même tranche x. Bus V+ / V− (met3) au-dessus du réseau, séparés par un blindage VSS ; bus d'entrées
(met3) sous la rangée de drivers ; rails VDD/VSS met1 continus.
Hiérarchie électrique = netlist xschem (netlist/twine_neuron.spice) ; layout à plat sauf les R_U.
"""
import os
import re
import klayout.db as db

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, "..", "netlist", "twine_neuron.spice")

ly = db.Layout()
ly.dbu = 0.001
ly.read(os.path.join(HERE, "res_unit.gds"))
RCELL = [c for c in ly.each_cell() if c.name.startswith("sky130_fd_pr__res_xhigh_po_0p35")][0]
for c in list(ly.each_cell()):
    if c.name == "res_unit":
        ly.delete_cell(c.cell_index())
top = ly.create_cell("twine_neuron")

LAYERS = {
    "nwell": (64, 20), "diff": (65, 20), "tap": (65, 44), "poly": (66, 20),
    "licon": (66, 44), "li": (67, 20), "mcon": (67, 44),
    "m1": (68, 20), "via": (68, 44), "m2": (69, 20), "via2": (69, 44),
    "m3": (70, 20), "via3": (70, 44), "m4": (71, 20),
    "nsdm": (93, 44), "urpm": (79, 20), "psdm": (94, 20), "npc": (95, 20),
    "m1lbl": (68, 5), "m1pin": (68, 16), "m2lbl": (69, 5), "m2pin": (69, 16),
    "m3lbl": (70, 5), "m3pin": (70, 16), "m4lbl": (71, 5), "m4pin": (71, 16),
}
LI = {k: ly.layer(*v) for k, v in LAYERS.items()}


def nm(v):
    return int(round(v * 200)) * 5


def snap(v):
    return round(v * 200) / 200


def r(layer, x1, y1, x2, y2):
    top.shapes(LI[layer]).insert(db.Box(nm(min(x1, x2)), nm(min(y1, y2)), nm(max(x1, x2)), nm(max(y1, y2))))


def sq(layer, cx, cy, s):
    r(layer, cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)


def pin(name, metal, x1, y1, x2, y2):
    r(metal, x1, y1, x2, y2)
    r(metal + "pin", x1, y1, x2, y2)
    top.shapes(LI[metal + "lbl"]).insert(db.Text(name, db.Trans(nm((x1 + x2) / 2), nm((y1 + y2) / 2))))


# ---------------------------------------------------------------- contacts / vias (pastilles conformes)
def g2(v):
    """centre sur la grille 0.01 µm (évite les enclosures arrondies à 5 nm près)."""
    return round(v * 100) / 100


def mcon_m1(x, y):
    """li -> m1 : mcon + pastille m1 0.26 x 0.32 (le li dessous doit exister)."""
    x, y = g2(x), g2(y)
    sq("mcon", x, y, 0.17)
    r("m1", x - 0.13, y - 0.16, x + 0.13, y + 0.16)


def via1(x, y):
    x, y = g2(x), g2(y)
    sq("via", x, y, 0.15)
    r("m1", x - 0.13, y - 0.16, x + 0.13, y + 0.16)
    r("m2", x - 0.13, y - 0.16, x + 0.13, y + 0.16)


def via2(x, y):
    x, y = g2(x), g2(y)
    sq("via2", x, y, 0.20)
    r("m2", x - 0.14, y - 0.19, x + 0.14, y + 0.19)      # via2 : m2 0.04 / 0.085
    r("m3", x - 0.25, y - 0.25, x + 0.25, y + 0.25)      # aire m3 >= 0.24


def via3(x, y):
    x, y = g2(x), g2(y)
    sq("via3", x, y, 0.20)
    r("m3", x - 0.25, y - 0.25, x + 0.25, y + 0.25)
    r("m4", x - 0.25, y - 0.25, x + 0.25, y + 0.25)


def poly_contact(x, y):
    """licon sur poly + tête de poly + li + npc."""
    x, y = g2(x), g2(y)
    sq("licon", x, y, 0.17)
    r("poly", x - 0.135, y - 0.165, x + 0.135, y + 0.165)
    r("li", x - 0.175, y - 0.085, x + 0.175, y + 0.085)      # li.5 : 0.08 sur 2 côtés opposés
    r("npc", x - 0.185, y - 0.185, x + 0.185, y + 0.185)


# ---------------------------------------------------------------- bande de diffusion (S/D)
def strip(x0, y0, w, ngates, l, sd, kind):
    """Diffusion avec ngates grilles verticales (dessinées par l'appelant) et ngates+1 colonnes S/D.
    Colonnes : licons + li + mcon + m1 (0.26 de large) limités à la diffusion. Renvoie (sdx, gx, xend)."""
    pitch = l + sd
    xt = x0 + ngates * l + (ngates + 1) * sd
    r("diff", x0, y0, xt, y0 + w)
    r("nsdm" if kind == "n" else "psdm", x0 - 0.125, y0 - 0.125, xt + 0.125, y0 + w + 0.125)
    sdx = [snap(x0 + sd / 2 + i * pitch) for i in range(ngates + 1)]
    gx = [snap(x0 + sd + i * pitch + l / 2) for i in range(ngates)]
    n = int((w - 0.12 - 0.17) / 0.34 + 1e-6) + 1
    span = 0.17 + (n - 1) * 0.34
    yb = snap(y0 + (w - span) / 2)
    m1y0, m1y1 = yb - 0.08, yb + span + 0.08
    m = int((m1y1 - m1y0 - 0.12 - 0.17) / 0.36 + 1e-6) + 1
    mspan = 0.17 + (m - 1) * 0.36
    mb = snap(m1y0 + (m1y1 - m1y0 - mspan) / 2)
    for cx in sdx:
        for k in range(n):
            sq("licon", cx, yb + 0.085 + k * 0.34, 0.17)
        r("li", cx - 0.085, m1y0, cx + 0.085, m1y1)
        for k in range(m):
            sq("mcon", cx, mb + 0.085 + k * 0.36, 0.17)
        r("m1", cx - 0.13, m1y0, cx + 0.13, m1y1)
    return sdx, gx, xt, (m1y0, m1y1)


def tap_row(x1, x2, yc, kind):
    """Rangée de prise substrat (kind p : ptap/VSS) ou de caisson (n : ntap/VDD) + rail m1 0.5."""
    r("tap", x1, yc - 0.205, x2, yc + 0.205)
    r("psdm" if kind == "p" else "nsdm", x1 - 0.125, yc - 0.33, x2 + 0.125, yc + 0.33)
    r("li", x1, yc - 0.17, x2, yc + 0.17)
    r("m1", x1 - 0.05, yc - 0.25, x2 + 0.05, yc + 0.25)
    n = int((x2 - x1 - 0.24 - 0.17) / 0.34) + 1
    s0 = x1 + (x2 - x1 - (0.17 + (n - 1) * 0.34)) / 2 + 0.085
    for k in range(n):
        sq("licon", snap(s0 + k * 0.34), yc, 0.17)
    n = int((x2 - x1 - 0.24 - 0.17) / 0.36) + 1
    s0 = x1 + (x2 - x1 - (0.17 + (n - 1) * 0.36)) / 2 + 0.085
    for k in range(n):
        sq("mcon", snap(s0 + k * 0.36), yc, 0.17)


# ================================================================ SLICE (driver tri-state)
L, SD, P = 0.15, 0.36, 0.51
WN, WPI, WPS = 0.42, 0.84, 1.0          # N (inv + pile), P inverseur, P pile
YP = 2.0                                  # bas des diffusions P
Y_EN, Y_D, Y_ENB, Y_DB = 0.80, 1.15, 1.50, 3.35
Y_VSS, Y_VDD = -0.95, 3.95               # centres des rails (prises)
Y_NP, Y_NN = YP + 0.5, 0.21


def slice_cell(x0, m):
    """Dessine une slice (multiplicité m de la pile) ; renvoie les points de connexion."""
    xs1 = x0 + 2.0
    # inverseur 1 (D -> DB) et 2 (EN -> ENB)
    inv = []
    for k, xs in enumerate((xs1, xs1 + 1.41)):
        sn, gn, _, mn = strip(xs - 0.18, 0.0, WN, 1, L, SD, "n")
        sp, gp, _, mp = strip(xs - 0.18, YP, WPI, 1, L, SD, "p")
        g = gn[0]
        r("poly", g - L / 2, -0.13, g + L / 2, YP + WPI + 0.13)
        poly_contact(g, Y_D if k == 0 else Y_EN)
        # source N -> VSS, source P -> VDD, drains reliés en m1
        r("m1", sn[0] - 0.13, Y_VSS, sn[0] + 0.13, mn[1])
        r("m1", sp[0] - 0.13, mp[0], sp[0] + 0.13, Y_VDD)
        top_y = Y_DB + 0.16 if k == 0 else mp[1]
        r("m1", sn[1] - 0.13, mn[0], sn[1] + 0.13, top_y)
        inv.append((g, sn[1]))
    (g1, out1), (g2, out2) = inv
    # pile tri-state
    xst = xs1 + 1.41 + 1.41
    ng = 2 * m
    sn, gx, xend, mn = strip(xst - 0.18, 0.0, WN, ng, L, SD, "n")
    sp, _, _, mp = strip(xst - 0.18, YP, WPS, ng, L, SD, "p")
    kinds = []
    for i in range(ng):
        c = i // 2
        first = "DB" if c % 2 == 0 else "EN"
        kinds.append(first if i % 2 == 0 else ("EN" if first == "DB" else "DB"))
    for g, k in zip(gx, kinds):
        if k == "DB":
            r("poly", g - L / 2, -0.13, g + L / 2, Y_DB + 0.165)
            poly_contact(g, Y_DB)
        else:
            r("poly", g - L / 2, -0.13, g + L / 2, Y_EN + 0.165)          # N : EN
            poly_contact(g, Y_EN)
            r("poly", g - L / 2, Y_ENB - 0.165, g + L / 2, YP + WPS + 0.13)  # P : ENB
            poly_contact(g, Y_ENB)
    cols = []
    for j in range(ng + 1):
        cols.append("NP" if j % 2 else ("RAIL" if (j // 2) % 2 == 0 else "DRV"))
    drvx = []
    for j, (xn, xp) in enumerate(zip(sn, sp)):
        if cols[j] == "RAIL":
            r("m1", xn - 0.13, Y_VSS, xn + 0.13, mn[1])
            r("m1", xp - 0.13, mp[0], xp + 0.13, Y_VDD)
        elif cols[j] == "DRV":
            r("m1", xn - 0.13, mn[0], xn + 0.13, mp[1])
            via1(xn, Y_D)
            drvx.append(xn)
        else:
            via1(xp, Y_NP)
            via1(xn, Y_NN)
    npx = [sp[j] for j in range(ng + 1) if cols[j] == "NP"]
    if len(npx) > 1:
        r("m2", npx[0] - 0.13, Y_NP - 0.13, npx[-1] + 0.13, Y_NP + 0.13)
        r("m2", npx[0] - 0.13, Y_NN - 0.13, npx[-1] + 0.13, Y_NN + 0.13)
    r("m2", drvx[0] - 0.13, Y_D - 0.13, drvx[-1] + 0.13, Y_D + 0.13)
    # lignes li : EN (y 0.80), D (1.15), ENB (1.50), DB (3.35)
    xpe, xpd = x0 + 0.5, x0 + 1.3
    last = gx[-1] + 0.2
    r("li", xpe - 0.085, Y_EN - 0.085, last, Y_EN + 0.085)
    r("li", xpd - 0.085, Y_D - 0.085, g1 + 0.175, Y_D + 0.085)
    r("li", out2 - 0.085, Y_ENB - 0.085, last, Y_ENB + 0.085)
    r("li", out1 - 0.085, Y_DB - 0.085, last, Y_DB + 0.085)
    mcon_m1(out1, Y_DB)
    mcon_m1(out2, Y_ENB)
    # bandes npc (fusion des têtes de poly contactées)
    r("npc", x0 + 0.3, Y_EN - 0.185, last + 0.05, Y_ENB + 0.185)
    r("npc", out1 - 0.2, Y_DB - 0.185, last + 0.05, Y_DB + 0.185)
    # plots d'entrée EN et D : mcon + via1 -> m2
    for x, y in ((xpe, Y_EN), (xpd, Y_D)):
        mcon_m1(x, y)
        via1(x, y)
    width = xend + 0.18 + 0.6 - x0
    return dict(x0=x0, w=width, en=(xpe, Y_EN), d=(xpd, Y_D), drv=(drvx[0], Y_D))


# ================================================================ netlist de référence
txt = open(NETLIST).read().replace("\n+", " ")
subs = {m.group(1): m.group(2) for m in re.finditer(r"^\.subckt (\S+) .*?\n(.*?)^\.ends", txt, re.M | re.S)}
topinst = [l.split() for l in subs["twine_neuron"].splitlines() if l.startswith("X")]
SL = {"slice_half": (8, 1, 1), "slice_w1": (4, 1, 1), "slice_w2": (2, 1, 2), "slice_w4": (1, 1, 4),
      "slice_w8": (1, 2, 8), "slice_w16": (1, 4, 16)}       # (n_série, n_parallèle, m pile)
slices = [(t[0], t[1], t[2], t[3], t[6]) for t in topinst if t[-1].startswith("slice_")]   # nom, D, EN, OUT, type


def order_key(s):
    name = s[0]
    if name.startswith("XS"):              # XS<i><P|M><k>
        return (0, int(name[2]), int(name[4]), name[3] == "M")
    if name.startswith("XB"):
        return (1, 0, int(name[3]), name[2] == "M")
    return (2, 0, 0, name[2] == "M")


slices.sort(key=order_key)

# ================================================================ PLACEMENT
RPITCH = 1.2
RYC = 35.0                                 # centre des R_U
URPM = []                                  # unités placées (remplissage urpm continu, rpm.1)
RB = (RYC - 28.355, RYC - 26.25)           # borne basse (m1)
RT = (RYC + 26.25, RYC + 28.355)           # borne haute (m1)
Y_RB, Y_RT = (RB[0] + RB[1]) / 2, (RT[0] + RT[1]) / 2
Y_JOG = 5.3                                # canal met3 des descentes DRV
Y_VPB, Y_SH, Y_VMB = 65.6, 66.6, 67.6      # bus V+, blindage VSS, bus V− (met3)


def res_at(x):
    URPM.append(x)
    top.insert(db.CellInstArray(RCELL.cell_index(), db.Trans(nm(x), nm(RYC))))


def up_to_bus(x, ybus, y_from):
    """borne R (m1, y_from) -> m4 vertical -> via3 sur le bus met3."""
    via1(x, y_from)
    via2(x, y_from)
    via3(x, y_from)
    r("m4", x - 0.2, y_from, x + 0.2, ybus + 0.2)
    via3(x, ybus)


def jumper(xa, xb, side):
    yy = RT if side == "T" else RB
    r("m1", xa - 0.125, yy[0], xb + 0.125, yy[1])


X0 = 0.0
# ---- G0 : 26 unités entrelacées P/M, bas -> VDD, haut -> bus
x = X0 + 1.0
g0x = []
for k in range(26):
    res_at(x)
    g0x.append((x, "VP" if k % 2 == 0 else "VM"))
    x += RPITCH
jumper(g0x[0][0], g0x[-1][0], "B")                         # tous les bas reliés (VDD)
r("m1", g0x[0][0] - 0.13, Y_VDD, g0x[0][0] + 0.13, RB[1])   # descente vers le rail VDD
r("m1", g0x[-1][0] - 0.13, Y_VDD, g0x[-1][0] + 0.13, RB[1])
for xx, node in g0x:
    up_to_bus(xx, Y_VPB if node == "VP" else Y_VMB, Y_RT)
x += 1.0

# ---- slices
INPUT_NETS = []
info = []
for name, dnet, ennet, out, typ in slices:
    ns, npar, m = SL[typ]
    nunits = ns * npar
    s = slice_cell(x, m)
    wid = max(s["w"], nunits * RPITCH + 1.0)
    # chaîne de R au-dessus
    ux = [x + 0.8 + k * RPITCH for k in range(nunits)]
    if nunits == 1 and out == "VP":      # unité seule : P au bord droit, M (suivante) au bord gauche -> paire (rpm.1)
        ux = [x + wid - 0.4]
    for xx in ux:
        res_at(xx)
    # DRV -> bas de la première unité (met3 : montée, jog, montée)
    xd, yd = s["drv"]
    via2(xd, yd)
    r("m3", xd - 0.2, yd, xd + 0.2, Y_JOG + 0.2)
    r("m3", min(xd, ux[0]) - 0.2, Y_JOG - 0.2, max(xd, ux[0]) + 0.2, Y_JOG + 0.2)
    r("m3", ux[0] - 0.2, Y_JOG, ux[0] + 0.2, Y_RB)
    via2(ux[0], Y_RB)
    via1(ux[0], Y_RB)
    if npar > 1:                         # unités en parallèle : bas reliés, hauts reliés
        jumper(ux[0], ux[-1], "B")
        jumper(ux[0], ux[-1], "T")
        out_x, out_y = ux[-1], Y_RT
    else:                                # série en serpentin
        for k in range(ns - 1):
            jumper(ux[k], ux[k + 1], "T" if k % 2 == 0 else "B")
        out_x = ux[-1]
        out_y = Y_RB if ns % 2 == 0 else Y_RT
    ybus = Y_VPB if out == "VP" else Y_VMB
    if out_y == Y_RT:
        up_to_bus(out_x, ybus, Y_RT)
    else:                                # sortie en bas : montée met3 le long de l'unité puis m4
        via1(out_x, Y_RB)
        via2(out_x, Y_RB)
        r("m3", out_x - 0.2, Y_RB, out_x + 0.2, RT[1] + 1.0)
        via3(out_x, RT[1] + 1.0)
        r("m4", out_x - 0.2, RT[1] + 1.0, out_x + 0.2, ybus + 0.2)
        via3(out_x, ybus)
    info.append((name, dnet, ennet, s))
    x += wid
X_END_SL = x

# urpm continu sur le réseau (marqueur ; largeur rpm.1 >= 1.27 µm pour les unités isolées)
r("urpm", min(URPM) - 0.375, RYC - 28.585, max(URPM) + 0.375, RYC + 28.585)

# ================================================================ rails, caisson, prises
XR0, XR1 = X0, X_END_SL
tap_row(XR0 + 0.3, XR1 - 0.3, Y_VSS, "p")
tap_row(XR0 + 0.3, XR1 - 0.3, Y_VDD, "n")
r("nwell", XR0, 1.4, XR1, 4.45)
# implants continus par rangée (nsdm/psdm.1 : espacement 0.38 entre bandes voisines)
r("nsdm", XR0 + 0.3, -0.125, XR1 - 0.3, WN + 0.125)
r("psdm", XR0 + 0.3, YP - 0.125, XR1 - 0.3, YP + WPS + 0.125)

# ================================================================ bus d'entrée (met3, sous les drivers)
nets_in = []
for name, dnet, ennet, s in info:
    for n in (dnet, ennet):
        if n not in nets_in and n not in ("VDD", "VSS"):
            nets_in.append(n)
Y_BUS0 = -2.2
busy = {n: Y_BUS0 - 0.8 * k for k, n in enumerate(nets_in)}
span = {n: [1e9, -1e9] for n in nets_in}
for name, dnet, ennet, s in info:
    for net, (px, py) in ((ennet, s["en"]), (dnet, s["d"])):
        if net == "VSS":                       # D de XHP : via1 sur le rail VSS
            r("m2", px - 0.13, Y_VSS, px + 0.13, py)
            via1(px, Y_VSS)
            continue
        if net == "VDD":                       # D de XHM : montée m2 jusqu'au rail VDD
            r("m2", px - 0.13, py, px + 0.13, Y_VDD)
            via1(px, Y_VDD)
            continue
        yb = busy[net]
        r("m2", px - 0.13, yb, px + 0.13, py)
        via2(px, yb)
        span[net][0] = min(span[net][0], px)
        span[net][1] = max(span[net][1], px)
XB_PIN = X0 - 3.0
for n in nets_in:                          # bus limité à ses terminaux (antenne met3), broche à gauche
    yb = busy[n]
    r("m3", span[n][0] - 0.8, yb - 0.15, span[n][1] + 0.25, yb + 0.15)
    pin(n, "m3", span[n][0] - 0.8, yb - 0.15, span[n][0] - 0.3, yb + 0.15)

# ================================================================ COMPARATEUR (routeur générique 1 rangée)
cmp_dev = [l.split() for l in subs["comparator"].splitlines() if l.startswith("XM") or l.startswith("XS")
           or l.startswith("XP") or l.startswith("XN")]


def dprops(t):
    d = dict(kv.split("=", 1) for kv in t[6:] if "=" in kv)
    return float(d["W"]), float(d["L"]), int(float(d.get("mult", 1)))


devs = []
for t in cmp_dev:
    name, dn, gn, sn, bn, model = t[:6]
    W, Lg, mm = dprops(t)
    kind = "n" if "nfet" in model else "p"
    devs.append(dict(name=name, kind=kind, W=W, L=Lg, m=mm, d=dn, g=gn, s=sn))
pair = [d for d in devs if d["name"] in ("XM1", "XM2")]
others = [d for d in devs if d["name"] not in ("XM1", "XM2")]
XC0 = X_END_SL + 6.0
terms = []                                # (x, y, net, layer) points de départ des descentes m2
cx = XC0


def place_strip(cx, kind, W, Lg, gates, cols):
    sd = max(0.36, 0.90 - Lg)
    sdx, gx, xend, mrange = strip(cx, 0.0, W, len(gates), Lg, sd, kind)
    for g, net in zip(gx, gates):
        r("poly", g - Lg / 2, -0.13, g + Lg / 2, W + 0.6)
        poly_contact(g, W + 0.435)
        mcon_m1(g, W + 0.435)
        via1(g, W + 0.435)
        terms.append((g, W + 0.435, net))
    for xx, net in zip(sdx, cols):
        if net in ("VSS", "VDD"):
            r("m1", xx - 0.13, Y_VSS, xx + 0.13, mrange[1])
        else:
            via1(xx, W / 2)
            terms.append((xx, W / 2, net))
    return xend


# paire d'entrée en centroïde commun A B B A (A = XM1/INP, B = XM2/INN), 2 doigts chacun
pW, pL = pair[0]["W"], pair[0]["L"]
cx = place_strip(cx, "n", pW, pL, ["INP", "INN", "INN", "INP"], ["XN", "TAIL", "XP", "TAIL", "XN"]) + 1.2
for d in [d for d in others if d["kind"] == "n"]:
    gates = [d["g"]] * d["m"]
    cols = [d["d"] if i % 2 == 0 else d["s"] for i in range(d["m"] + 1)]
    if d["m"] == 1:
        cols = [d["s"], d["d"]]
    cx = place_strip(cx, "n", d["W"], d["L"], gates, cols) + 1.2
XN_END = cx
cx += 1.5
XP_START = cx
for d in [d for d in others if d["kind"] == "p"]:
    gates = [d["g"]] * d["m"]
    cols = [d["s"], d["d"]] if d["m"] == 1 else [d["d"] if i % 2 == 0 else d["s"] for i in range(d["m"] + 1)]
    cx = place_strip(cx, "p", d["W"], d["L"], gates, cols) + 1.2
XC1 = cx
_wn = max(d["W"] for d in devs if d["kind"] == "n")
_wp = max(d["W"] for d in devs if d["kind"] == "p")
r("nsdm", XC0 - 0.125, -0.125, XN_END - 1.2 + 0.125, _wn + 0.125)
r("psdm", XP_START - 0.125, -0.125, XC1 - 1.2 + 0.125, _wp + 0.125)
# prises et rails du comparateur (prolongent les rails globaux)
tap_row(XC0 - 0.5, XN_END - 0.6, Y_VSS, "p")
YNT = -2.2                                  # rangée ntap/VDD sous les PMOS (caisson étendu vers le bas)
tap_row(XP_START - 0.3, XC1 - 0.6, Y_VSS, "n")
maxw = max(d["W"] for d in devs)
r("nwell", XP_START - 0.9, Y_VSS - 0.6, XC1 + 0.2, maxw + 1.2)
# rails : VSS comparateur <- rail VSS global (même y) ; VDD comparateur (y = Y_VSS, côté P) <- m2/m3
r("m1", XR1 - 0.4, Y_VSS - 0.25, XC0 - 0.4, Y_VSS + 0.25)
# canal met3 au-dessus des transistors
cnets = []
for (xx, yy, net) in terms:
    if net not in cnets:
        cnets.append(net)
Y_CH0 = maxw + 1.6
# ordre des pistes (bas -> haut) en miroir autour de CLK : chaque nœud d'une paire différentielle a des voisins
# équivalents (phase 6 : l'ordre d'apparition plaçait CLK entre XP et OUTP -> C(CLK-OUTP) 2.66 fF vs
# C(CLK-OUTN) 0.91 fF, injection asymétrique au front d'horloge, offset post-layout ≈ −40 à −68 mV).
# TAIL (mode commun) en bas, séparé du bloc symétrique par une piste vide.
CH_ORDER = ["TAIL", None, "Q", "TA", "SN", "OUTN", "XN", "INP", "CLK", "INN", "XP", "OUTP", "RP", "TB", "QB"]
if os.environ.get("TN_CH_LEGACY"):
    CH_ORDER = list(cnets)
CH_ORDER += [n for n in cnets if n not in CH_ORDER]
assert set(n for n in CH_ORDER if n) >= set(cnets), (CH_ORDER, cnets)
cy = {n: Y_CH0 + 0.8 * k for k, n in enumerate(CH_ORDER) if n}
print("  pistes canal (bas -> haut) : " + " ".join(n or "-" for n in CH_ORDER))
cspan = {n: [1e9, -1e9] for n in cnets}
for (xx, yy, net) in terms:
    r("m2", xx - 0.13, yy, xx + 0.13, cy[net])
    via2(xx, cy[net])
    cspan[net][0] = min(cspan[net][0], xx)
    cspan[net][1] = max(cspan[net][1], xx)
# équilibrage des paires différentielles (phase 6 : offset post-layout de −40 à −68 mV dû à C(OUTP) − C(OUTN)
# = +1.46 fF sur des nœuds de ≈ 9 fF) : la piste la plus courte est prolongée à droite jusqu'à la longueur de
# l'autre, + EXT supplémentaire (µm, réglé d'après la PEX : env TN_CMP_EXT="NET:µm,...")
EXT = {k: float(v) for k, v in (x.split(":") for x in os.environ.get("TN_CMP_EXT", "").split(",") if x)}
CEXT = {n: 0.0 for n in cnets}
for a, b in (("OUTP", "OUTN"), ("XN", "XP"), ("RP", "SN"), ("TA", "TB"), ("Q", "QB")):
    if a in cspan and b in cspan:
        la, lb = cspan[a][1] - cspan[a][0], cspan[b][1] - cspan[b][0]
        CEXT[b if lb < la else a] = abs(la - lb)
        print(f"  piste {a} {la:.2f} µm / {b} {lb:.2f} µm")
for n in cnets:
    CEXT[n] += EXT.get(n, 0.0)
    r("m3", cspan[n][0] - 0.2, cy[n] - 0.15, cspan[n][1] + 0.2 + CEXT[n], cy[n] + 0.15)

# VDD du comparateur : rail ntap (y = Y_VSS, x côté P) -> m1 montant jusqu'au rail VDD global prolongé
XVDDC = XC1 - 0.9                   # sur le rail ntap du comparateur (qui s'arrête à XC1 − 0.55)
XVG = XR1 - 0.5                     # descente du rail VDD global (marge de la dernière slice)
for f in (via1, via2, via3):
    f(XVG, Y_VDD)
r("m4", XVG - 0.25, Y_VSS - 0.25, XVG + 0.25, Y_VDD + 0.25)
r("m4", XVG - 0.25, Y_VSS - 0.25, XVDDC + 0.25, Y_VSS + 0.25)       # m4 horizontal sous le comparateur
for f in (via3, via2, via1):
    f(XVDDC, Y_VSS)                 # sur le rail ntap du comparateur
# ---- entrées / sorties du comparateur
XLINK = XC1 + 2.0
for net, bus in (("INP", Y_VPB), ("INN", Y_VMB)):
    pass
# V+ / V− : prolongement des bus jusqu'au-dessus du comparateur, descente m4 jusqu'aux pistes INP / INN
xvp = cspan["INP"][0]
xvm = cspan["INN"][0] - 1.0
for net, ybus, xl in (("INP", Y_VPB, xvp - 1.5), ("INN", Y_VMB, xvp - 3.0)):
    via3(xl, cy[net])
    r("m3", xl - 0.2, cy[net] - 0.15, cspan[net][0], cy[net] + 0.15)
    r("m4", xl - 0.2, cy[net], xl + 0.2, ybus + 0.2)
    via3(xl, ybus)
X_BUS_END = xvp - 1.0
r("m3", X0, Y_VPB - 0.2, X_BUS_END, Y_VPB + 0.2)
r("m3", X0, Y_VMB - 0.2, X_BUS_END, Y_VMB + 0.2)
XSH = X0 - 1.0
r("m3", XSH - 0.25, Y_SH - 0.2, X_BUS_END, Y_SH + 0.2)       # blindage VSS
# blindage -> VSS : descente m4 à gauche du réseau, rail VSS prolongé
r("m1", XSH - 0.3, Y_VSS - 0.25, XR0 + 0.5, Y_VSS + 0.25)
via3(XSH, Y_SH)
r("m4", XSH - 0.25, Y_VSS, XSH + 0.25, Y_SH)
via3(XSH, Y_VSS)
via2(XSH, Y_VSS)
via1(XSH, Y_VSS)
pin("VP", "m3", X0, Y_VPB - 0.2, X0 + 0.6, Y_VPB + 0.2)
pin("VM", "m3", X0, Y_VMB - 0.2, X0 + 0.6, Y_VMB + 0.2)
for net in ("CLK", "Q", "QB"):
    pin(net, "m3", cspan[net][1] - 0.4, cy[net] - 0.15, cspan[net][1] + 0.2, cy[net] + 0.15)
pin("VSS", "m1", XR0 + 1.0, Y_VSS - 0.25, XR0 + 2.0, Y_VSS + 0.25)
pin("VDD", "m1", XR0 + 1.0, Y_VDD - 0.25, XR0 + 2.0, Y_VDD + 0.25)

top.flatten(True)                          # R_U à plat : l'urpm fusionne avec le remplissage continu
out = os.path.join(HERE, "twine_neuron.gds")
ly.write(out)
bb = top.bbox()
print(f"{out} : {bb.width()/1000:.1f} x {bb.height()/1000:.1f} µm = {bb.width()*bb.height()/1e12:.4f} mm² ; "
      f"{len(slices)} slices, {len(nets_in)} bus d'entrée, comparateur {len(devs)} transistors, canal {len(cnets)} nets")
